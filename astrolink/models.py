from django.db import models
from authentication.models import User, SupervisorProfile, StudentProfile, AssociationProfile
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from pathlib import Path

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    is_system = models.BooleanField(default=False,help_text="System tags cannot be deleted through the UI.")

    def __str__(self):
        return self.name

def supervisor_profile_picture_path(instance, filename):
    """Dynamically generates upload path for supervisor profile pictures"""
    return f"supervisors/{instance.id}/{filename}"

class Reference(models.Model):
    supervisor = models.ForeignKey(SupervisorProfile, on_delete=models.CASCADE, related_name="references")
    title = models.CharField(max_length=128)
    description = models.TextField()
    link = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return self.title

class Interest(models.Model):
    student = models.ForeignKey(StudentProfile,on_delete=models.CASCADE,related_name="interests")
    topic = models.CharField(max_length=128)
    experience = models.TextField(help_text="Describe your background or experience with this topic")

    def __str__(self):
        return self.topic


class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    supervisor = models.ForeignKey(SupervisorProfile, on_delete=models.CASCADE, related_name="projects")
    time_estimate = models.CharField(max_length=16, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now_add=True)
    is_open = models.BooleanField(default=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="projects")

    def __str__(self):
        return self.title

def company_logo_path(instance, filename):
    """Dynamically generates upload path for company"""
    return f"company/{instance.id}/{filename}"

class Company(models.Model):
    STATUS_CHOICES = [
        ("UNDER_CONTRACT", "Under Contract (DO NOT CONTACT)"),
        ("EXTERN_LEADS", "Extern Leads (DO NOT CONTACT)"),
        ("COMMITTEE_LEADS", "Committee Leads — ask board before contacting"),
        ("OTHER", "Other — ask board before contacting"),
    ]

    name = models.CharField(max_length=64)
    description = models.TextField()
    email = models.CharField(max_length=64)
    contact_name = models.CharField(max_length=64)
    contact_phone = models.CharField(max_length=64, null=True, blank=True)
    website = models.CharField(max_length=64, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    logo = models.ImageField(upload_to=company_logo_path, null=True, blank=True)
    association = models.ForeignKey(AssociationProfile, on_delete=models.CASCADE, related_name="companies")

    def __str__(self):
        return self.name

def casestudy_logo_path(instance, filename):
    """Dynamically generates upload path for case study logos"""
    return f"casestudylogos/{instance.id}/{filename}"

class CaseStudy(models.Model):
    title = models.CharField(max_length=200)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="case_studies")
    logo = models.ImageField(
        upload_to=casestudy_logo_path, 
        null=True, 
        blank=True
    )
    description = models.TextField()
    time_estimate = models.CharField(max_length=16)
    revenue_split_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now_add=True)
    is_open = models.BooleanField(default=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="case_studies")

    def __str__(self):
        return f"{self.title} ({self.company.name})"

class ResearchGroup(models.Model):
    name = models.CharField(max_length=200)
    lead_professor = models.CharField(max_length=150)
    description = models.TextField()
    contact_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Application(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending review"),
        ("ACCEPTED", "Accepted by supervisor"),
        ("REJECTED", "Rejected by supervisor"),
        ("CONFIRMED", "Confirmed by student"),
    ]

    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name="member")
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL, related_name="project")
    case_study = models.ForeignKey(CaseStudy, null=True, blank=True, on_delete=models.SET_NULL, related_name="case_study")
    association = models.ForeignKey(AssociationProfile,null=True, blank=True,on_delete=models.SET_NULL,related_name="applications",help_text="Required for general applications")
    experience = models.TextField()
    motivation = models.TextField()
    interest = models.TextField()
    comments = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="PENDING")
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    supervisor_comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.member.display_name()
    
    @property
    def is_pending(self):
        return self.status == "PENDING"

    @property
    def is_accepted(self):
        return self.status == "ACCEPTED"

    @property
    def is_rejected(self):
        return self.status == "REJECTED"

    @property
    def is_confirmed(self):
        return self.status == "CONFIRMED"
    
    @property
    def status_display(self):
        return self.get_status_display()
    
    @property
    def is_general(self):
        return not self.project and not self.case_study
    
    @property
    def confirmation_deadline(self):
        if not self.accepted_at:
            return None
        return self.accepted_at + timedelta(days=settings.APPLICATION_CONFIRMATION_DAYS)
    
    @property
    def is_expired(self):
        if not self.is_accepted or not self.confirmation_deadline:
            return False
        return timezone.now() > self.confirmation_deadline
    
    @property
    def can_confirm(self):
        return self.is_accepted and not self.is_expired
    
class IgnoredApplication(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="ignored_applications")
    application = models.ForeignKey(Application,on_delete=models.CASCADE,related_name="ignored_by")

    ignored_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "application")

class Attachment(models.Model):
    project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name="attachments",null=True,blank=True)
    case_study = models.ForeignKey(CaseStudy,on_delete=models.CASCADE,related_name="attachments",null=True,blank=True)

    file = models.FileField(upload_to="attachments/")
    original_filename = models.CharField(max_length=255)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_filename
    
    @property
    def is_image(self):
        return (
            Path(self.original_filename)
            .suffix.lower()
            in {
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
                ".svg",
            }
        )