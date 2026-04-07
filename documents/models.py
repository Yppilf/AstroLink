from django.db import models
from authentication.models import User, Role
import uuid, hashlib, hmac, json, os
from django.utils import timezone
from django.core.files import File

def template_upload_path(instance, filename):
    return f"documents/templates/{instance.name}/{filename}"

class DocumentTemplate(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    latex_file = models.FileField(upload_to=template_upload_path)

    name_template = models.CharField(max_length=255,blank=True,help_text="e.g. Registration Form - {name}")

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User,null=True,blank=True,on_delete=models.SET_NULL)

    def __str__(self):
        return self.name
    
class TemplateField(models.Model):
    FIELD_TYPES = [
        ("text", "Text"),
        ("integer", "Integer"),
        ("float", "Float"),
        ("date", "Date"),
        ("choice", "Choice"),
        ("boolean", "Boolean"),
        ("signature", "Signature"),
    ]

    template = models.ForeignKey(DocumentTemplate,on_delete=models.CASCADE,related_name="fields")

    name = models.CharField(max_length=100)
    label = models.CharField(max_length=255)

    field_type = models.CharField(max_length=50, choices=FIELD_TYPES)
    choices = models.JSONField(blank=True, null=True)

    required = models.BooleanField(default=False)

    default_value = models.CharField(max_length=255, blank=True, null=True)

    allowed_roles = models.ManyToManyField(Role,blank=True,related_name="template_fields")

    def __str__(self):
        return f"{self.label} ({self.template.name})"
    
class TemplateAsset(models.Model):
    template = models.ForeignKey(DocumentTemplate,on_delete=models.CASCADE,related_name="assets")

    file = models.FileField(upload_to="documents/template_assets/")

    # how LaTeX refers to the asset
    name = models.CharField(max_length=255,help_text="Filename used inside LaTeX (e.g. logo.png or style.sty)")

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.template.name})"
    
class GeneratedDocument(models.Model):
    template = models.ForeignKey(DocumentTemplate,null=True,on_delete=models.SET_NULL)

    context_data = models.JSONField()

    pdf_file = models.FileField(upload_to="documents/generated/",blank=True,null=True)

    name = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User,null=True,blank=True,on_delete=models.SET_NULL)

    is_locked = models.BooleanField(default=False)
    last_edited_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_fully_signed(self):
        signature_fields = self.template.fields.filter(field_type="signature")

        total_fields = signature_fields.count()
        total_signers = self.signers.count()

        # Condition 1: all signature fields have assigned signers
        if total_fields != total_signers:
            return False

        # Condition 2: all signers have signed
        return not self.signers.filter(signed=False).exists()

    def update_context(self, new_context_data: dict):
        """
        Safely update document content:
        - Prevent editing if locked
        - Wipe all signatures
        - Regenerate PDF
        """
        if self.is_locked:
            raise ValueError("Document is locked and cannot be edited.")

        # 1. Update context
        self.context_data = new_context_data
        self.last_edited_at = timezone.now()

        # 2. Wipe signatures
        self._reset_signatures()

        # 3. Regenerate PDF
        from .generate_views import generate_pdf
        from .utils import build_render_context
        render_context = build_render_context(self)
        pdf_path = generate_pdf(self.template, render_context, use_temp=False)

        if self.pdf_file:
            try:
                self.pdf_file.delete(save=False)
            except Exception:
                pass

        with open(pdf_path, "rb") as f:
            self.pdf_file.save(os.path.basename(pdf_path), File(f), save=False)

        self.save()

    def _reset_signatures(self):
        # Delete attestations
        Attestation.objects.filter(document=self).delete()

        # Reset signers
        for signer in self.signers.all():
            signer.signed = False
            signer.signed_at = None
            signer.signature_blob = None
            signer.signature_salt = None
            signer.attestation = None
            signer.save()

    def lock(self):
        self.is_locked = True
        self.save(update_fields=["is_locked"])

    def unlock(self):
        self.is_locked = False
        self.save(update_fields=["is_locked"])

    def save(self, *args, **kwargs):
        if not self.name and self.template and self.template.name_template:
            try:
                self.name = self.template.name_template.format(**self.context_data)
            except KeyError:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or f"Document {self.id}"
    
class Attestation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    document = models.ForeignKey(GeneratedDocument,on_delete=models.CASCADE,related_name="attestations")

    field = models.ForeignKey(TemplateField,on_delete=models.CASCADE,)

    payload = models.JSONField(null=True, blank=True)

    signature_salt = models.CharField(max_length=128, blank=True, null=True)
    signature = models.CharField(max_length=128, blank=True, null=True)

    blob_hash = models.CharField(max_length=128, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    finalized = models.BooleanField(default=False)

    def compute_signature(self):
        if not self.signature_salt or not self.payload:
            return None

        payload_str = json.dumps(self.payload, sort_keys=True)
        key = self.signature_salt.encode("utf-8")

        return hmac.new(key, payload_str.encode("utf-8"), hashlib.sha256).hexdigest()

    def finalize(self, signature_blob: str):
        if self.finalized:
            return

        if not isinstance(signature_blob, str):
            signature_blob = signature_blob.decode("utf-8")

        self.blob_hash = hashlib.sha256(signature_blob.encode("utf-8")).hexdigest()
        self.signature = self.compute_signature()
        self.finalized = True

        self.save(update_fields=["blob_hash", "signature", "finalized"])

class DocumentSigner(models.Model):
    document = models.ForeignKey(GeneratedDocument,on_delete=models.CASCADE,related_name="signers")

    field = models.ForeignKey(TemplateField,on_delete=models.CASCADE)

    user = models.ForeignKey(User,null=True,blank=True,on_delete=models.SET_NULL)

    signed = models.BooleanField(default=False)
    signed_at = models.DateTimeField(null=True, blank=True)

    signature_blob = models.TextField(blank=True, null=True)
    signature_salt = models.CharField(max_length=128, blank=True, null=True)

    attestation = models.OneToOneField(Attestation,null=True,blank=True,on_delete=models.SET_NULL)

    class Meta:
        unique_together = ("document", "field")

    def can_user_sign(self, user):
        """Check if given user is allowed based on template role restriction"""
        allowed_roles = self.field.allowed_roles.all()

        if not allowed_roles.exists():
            return True

        return user.role in allowed_roles

    def __str__(self):
        return f"{self.user} → {self.document}"