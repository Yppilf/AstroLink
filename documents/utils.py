from .models import DocumentSigner

def build_render_context(doc):
    context = doc.context_data.copy()

    for signer in doc.signers.all():
        if signer.signature_blob:
            context[signer.field.name] = signer.signature_blob

    return context

def sync_signers(doc, context_data):
    existing_signers = {
        signer.field_id: signer for signer in doc.signers.all()
    }

    for field in doc.template.fields.filter(field_type="signature"):
        user_id = context_data.get(field.name)
        existing = existing_signers.get(field.id)

        if user_id:
            if not existing:
                # ➕ New signer
                DocumentSigner.objects.create(
                    document=doc,
                    field=field,
                    user_id=user_id
                )
            else:
                # Signer changed
                if existing.user_id != user_id:
                    # Delete old attestation if exists
                    if existing.attestation:
                        existing.attestation.delete()

                    existing.user_id = user_id
                    existing.signed = False
                    existing.signed_at = None
                    existing.signature_blob = None
                    existing.signature_salt = None
                    existing.attestation = None
                    existing.save()

        else:
            # Signer removed
            if existing:
                # Delete attestation before deleting signer
                if existing.attestation:
                    existing.attestation.delete()

                existing.delete()