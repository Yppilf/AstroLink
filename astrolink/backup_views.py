from permissions.utils import external_user_permissions_required, has_permission
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
import json, tempfile, django
from io import StringIO
from django.core.management import call_command
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from django.views.decorators.http import require_POST
from .encryption_utils import encrypt_data, decrypt_data
from django.db import connection

@external_user_permissions_required('create_supervisor', 'create_student', 'create_association')
def export_encrypted_fixture_backup(request):
    buffer = StringIO()

    call_command(
        "dumpdata",
        "--natural-foreign",
        "--natural-primary",
        stdout=buffer,
    )

    payload = {
        "project": "astrolink",
        "created_at": timezone.now().isoformat(),
        "django_version": django.get_version(),
        "data": json.loads(buffer.getvalue()),
    }

    encrypted = encrypt_data(
        json.dumps(payload).encode("utf-8"),
        settings.BACKUP_ENCRYPTION_KEY,
    )

    response = HttpResponse(
        encrypted,
        content_type="application/octet-stream",
    )
    response["Content-Disposition"] = (
        'attachment; filename="astrolink_fixture_backup.enc"'
    )
    return response

@external_user_permissions_required('create_supervisor', 'create_student', 'create_association')
@require_POST
def import_encrypted_fixture_backup(request):
    if "confirm_restore" not in request.POST:
        return HttpResponse(
            "Confirmation checkbox not checked.",
            status=400,
        )

    uploaded_file = request.FILES.get("backup_file")
    if not uploaded_file:
        return HttpResponse("No backup file uploaded.", status=400)

    try:
        decrypted = decrypt_data(
            uploaded_file.read(),
            settings.BACKUP_ENCRYPTION_KEY,
        )
        payload = json.loads(decrypted)
    except Exception:
        return HttpResponse("Invalid or corrupted backup.", status=400)

    if payload.get("project") != "astrolink":
        return HttpResponse("Backup does not belong to this project.", status=400)

    with tempfile.NamedTemporaryFile(
        mode="w+",
        suffix=".json",
        delete=False,
    ) as tmp:
        json.dump(payload["data"], tmp)
        tmp_path = tmp.name

    connection.close()
    call_command("flush", interactive=False)
    call_command("loaddata", tmp_path)

    return redirect("astrolink:backup_page")

@external_user_permissions_required('create_supervisor', 'create_student', 'create_association')
def backup_page(request):
    return render(request, "misc/backup.html", {"page_title": "Backup & Restore"})