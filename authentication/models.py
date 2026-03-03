from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.utils.text import slugify

class Role(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'roles'
        verbose_name = "role"

    def __str__(self):
        return self.name

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

def generate_unique_username(first_name, last_name):
    base = slugify(f"{first_name}{last_name}") or "user"
    username = base
    counter = 1

    from .models import User  # local import to avoid circular issues

    while User.objects.filter(username=username).exists():
        counter += 1
        username = f"{base}{counter}"

    return username

class User(AbstractBaseUser, PermissionsMixin):
    username = models.SlugField(max_length=150,unique=True,blank=True,editable=False,db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    legal_name = models.CharField(max_length=255, blank=True, editable=False)
    screen_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=255, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) # required for Django admin

    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',  # Unique related_name for groups
        blank=True,
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions_set',  # Unique related_name for permissions
        blank=True,
        help_text='Specific permissions for this user.',
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = "user"

    def __str__(self):
        return self.display_name()
    
    def display_name(self):
        return self.screen_name or self.legal_name
    
    def save(self, *args, **kwargs):
        full_name = f"{self.first_name} {self.last_name}".strip()
        self.legal_name = full_name

        if self.email:
            self.email = self.email.lower()

        if not self.username:
            self.username = generate_unique_username(
                self.first_name,
                self.last_name
            )

        super().save(*args, **kwargs)


# ----------------------
# Role-specific profiles
# ----------------------
class BaseProfile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name="%(class)s")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    @property
    def name(self):
        """Return the display name of the associated user"""
        return self.user.display_name()

    @property
    def email(self):
        """Return the email of the associated user"""
        return self.user.email
    
    def __str__(self):
        return self.user.display_name()

def supervisor_profile_picture_path(instance, filename):
    return f"supervisors/{instance.user.id}/{filename}"

class SupervisorProfile(BaseProfile):
    biography = models.TextField(blank=True)
    pnumber = models.CharField(max_length=64, null=True, blank=True)
    profile_picture = models.ImageField(upload_to=supervisor_profile_picture_path,null=True,blank=True)

    academic_supervisor = models.ForeignKey("self",null=True,blank=True,on_delete=models.SET_NULL,related_name="phd_students")

    def is_phd_student(self):
        return self.academic_supervisor is not None

class StudentProfile(BaseProfile):
    biography = models.TextField(blank=True)
    snumber = models.CharField(max_length=64, null=True, blank=True)
    level = models.CharField(max_length=64, null=True, blank=True)
    study_programme = models.CharField(max_length=128, blank=True)    

def association_profile_picture_path(instance, filename):
    return f"associations/{instance.user.id}/{filename}"

class AssociationProfile(BaseProfile):
    biography = models.TextField(blank=True)
    website = models.CharField(max_length=64, null=True, blank=True)
    profile_picture = models.ImageField(upload_to=association_profile_picture_path,null=True,blank=True)

