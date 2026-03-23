from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.http import require_POST
from .models import GeneratedDocument, DocumentSigner, Attestation
import hashlib, hmac, os, secrets
from .generate_views import generate_pdf
from django.utils import timezone
from django.core.files import File

CONTRACT_AUTHENTICITY_KEY = settings.CONTRACT_AUTHENTICITY_KEY

def save_generated_pdf_to_model(pdf_file_path, model_file_field):
    """
    Saves a local PDF file to a Django FileField.
    """
    filename = os.path.basename(pdf_file_path)
    with open(pdf_file_path, "rb") as f:
        model_file_field.save(filename, File(f), save=False)
    
def generate_signature_id(document, signed_at=None):
    signed_at = signed_at or timezone.now()
    # Concatenate the components
    msg = f"{signed_at.isoformat()}|{document.id}"
    # Ensure the key is bytes
    key_bytes = CONTRACT_AUTHENTICITY_KEY.encode("utf-8")
    signature_id = hmac.new(key_bytes, msg.encode("utf-8"), hashlib.sha256).hexdigest()
    return signature_id

def format_signature_blob(payload: dict, short_sig: str):
    """
    payload = {
        "name": "...",
        "signed_at": "2025-01-10T14:29:00Z"
    }
    """

    name = payload["name"]
    signed_at = payload["signed_at"]

    # Human readable timestamp for PDF
    from datetime import datetime
    dt = datetime.fromisoformat(signed_at)
    timestamp = dt.strftime("%d-%m-%Y %H:%M")

    blob = (
        r"\shortstack{" +
        rf"{name} \\ " +
        rf"{timestamp} \\ " +
        rf"{short_sig}" +
        "}"
    )
    return blob


def generate_signature_salt():
    return secrets.token_hex(32)  # 64 chars hex

def compute_short_signature(signature: str):
    return signature[:12]

def sign_generated_document(request, doc_id, field_id):
    """
    Signs a field in a generated document:
      - Creates attestation
      - Updates context_data with signature blob
      - Regenerates PDF
    """
    doc = get_object_or_404(GeneratedDocument, id=doc_id)

    signer = get_object_or_404(
        DocumentSigner,
        document=doc,
        field_id=field_id,
        user=request.user
    )

    if signer.signed:
        return HttpResponse("Already signed", status=400)

    signed_at = timezone.now()

    # --- Payload stored in Attestation ---
    payload = {
        "name": request.user.username,
        "signed_at": signed_at.isoformat(),
        "document_id": str(doc.id),
        "field_name": signer.field.name,
    }

    # Generate salt for HMAC
    signature_salt = generate_signature_salt()

    attestation = Attestation.objects.create(
        document=doc,
        field=signer.field,
        payload=payload,
        signature_salt=signature_salt,
    )

    # Compute deterministic HMAC
    attestation.signature = attestation.compute_signature()
    attestation.save(update_fields=["signature"])

    # Format signature blob for LaTeX
    short_signature = compute_short_signature(attestation.signature)
    signature_blob = format_signature_blob(payload, short_signature)

    # Update signer
    signer.signature_blob = signature_blob
    signer.signed = True
    signer.signed_at = signed_at
    signer.attestation = attestation
    signer.save(update_fields=["signature_blob", "signed", "signed_at", "attestation"])

    # Update document context_data
    doc.context_data[signer.field.name] = signature_blob

    # Regenerate PDF with signature
    pdf_file_path = generate_pdf(
        doc.template,
        doc.context_data,
        output_folder="generated_pdfs",
        use_temp=False
    )

    # Replace old PDF safely
    if doc.pdf_file:
        try:
            doc.pdf_file.delete(save=False)
        except Exception:
            pass

    with open(pdf_file_path, "rb") as f:
        doc.pdf_file.save(os.path.basename(pdf_file_path), File(f), save=False)

    doc.save(update_fields=["context_data", "pdf_file"])

    # Finalize attestation
    attestation.finalize(signature_blob)

    # Optionally update overall signed status
    doc.update_signed_status()

    return redirect("documents:generated_document_view", doc_id=doc.id)