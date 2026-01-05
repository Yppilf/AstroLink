from django.db import models
from authentication.models import User, SupervisorProfile

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

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    supervisor = models.ForeignKey(SupervisorProfile, on_delete=models.CASCADE, related_name="projects")
    time_estimate = models.CharField(max_length=16, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now_add=True)

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
        ("UNHANDLED", "Not yet handled"),
        ("INPROGRESS", "Handling in progress"),
        ("HANDLED", "Handled"),
    ]

    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name="member")
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL, related_name="project")
    case_study = models.ForeignKey(CaseStudy, null=True, blank=True, on_delete=models.SET_NULL, related_name="case_study")
    experience = models.TextField()
    motivation = models.TextField()
    interest = models.TextField()
    comments = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="UNHANDLED")

    def __str__(self):
        return self.member.display_name()
    
    @property
    def status_display(self):
        return self.get_status_display()