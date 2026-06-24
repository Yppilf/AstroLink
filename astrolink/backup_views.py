from permissions.utils import external_user_permissions_required, has_permission
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
import json, tempfile, django, os, subprocess
from io import StringIO
from django.core.management import call_command
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from django.views.decorators.http import require_POST
from .encryption_utils import encrypt_file, decrypt_file
from django.db import connection
from django.http import FileResponse

DB = settings.DATABASES["default"]

@external_user_permissions_required(
    "create_supervisor",
    "create_student",
    "create_association",
)
def export_encrypted_backup(request):

    db = settings.DATABASES["default"]

    dump_file = tempfile.NamedTemporaryFile(
        suffix=".dump",
        delete=False,
    )
    dump_file.close()

    encrypted_file = tempfile.NamedTemporaryFile(
        suffix=".enc",
        delete=False,
    )
    encrypted_file.close()

    env = os.environ.copy()
    env["PGPASSWORD"] = db["PASSWORD"]

    subprocess.run(
        [
            "pg_dump",
            "-Fc",
            "-h", db["HOST"],
            "-p", str(db["PORT"]),
            "-U", db["USER"],
            "-d", db["NAME"],
            "-f", dump_file.name,
        ],
        env=env,
        check=True,
    )

    encrypt_file(
        dump_file.name,
        encrypted_file.name,
        settings.BACKUP_ENCRYPTION_KEY,
    )

    os.remove(dump_file.name)

    filename = (
        f"astrolink_"
        f"{timezone.now():%Y%m%d_%H%M%S}"
        ".backup.enc"
    )

    response = FileResponse(
        open(encrypted_file.name, "rb"),
        as_attachment=True,
        filename=filename,
    )

    return response

@external_user_permissions_required(
    "create_supervisor",
    "create_student",
    "create_association",
)
@require_POST
def import_encrypted_backup(request):

    if "confirm_restore" not in request.POST:
        return HttpResponse(
            "Confirmation checkbox not checked.",
            status=400,
        )

    uploaded = request.FILES.get("backup_file")

    if not uploaded:
        return HttpResponse(
            "No backup file uploaded.",
            status=400,
        )

    encrypted_file = tempfile.NamedTemporaryFile(
        suffix=".enc",
        delete=False,
    )

    for chunk in uploaded.chunks():
        encrypted_file.write(chunk)

    encrypted_file.close()

    dump_file = tempfile.NamedTemporaryFile(
        suffix=".dump",
        delete=False,
    )
    dump_file.close()

    try:
        decrypt_file(
            encrypted_file.name,
            dump_file.name,
            settings.BACKUP_ENCRYPTION_KEY,
        )

    except Exception:

        os.remove(encrypted_file.name)
        os.remove(dump_file.name)

        return HttpResponse(
            "Invalid or corrupted backup.",
            status=400,
        )

    db = settings.DATABASES["default"]

    connection.close()

    env = os.environ.copy()
    env["PGPASSWORD"] = db["PASSWORD"]

    subprocess.run(
        [
            "pg_restore",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
            "-h", db["HOST"],
            "-p", str(db["PORT"]),
            "-U", db["USER"],
            "-d", db["NAME"],
            dump_file.name,
        ],
        env=env,
        check=True,
    )

    os.remove(encrypted_file.name)
    os.remove(dump_file.name)

    return redirect("astrolink:backup_page")

@external_user_permissions_required('create_supervisor', 'create_student', 'create_association')
def backup_page(request):
    return render(request, "misc/backup.html", {"page_title": "Backup & Restore"})