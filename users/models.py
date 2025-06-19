from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

# Create your models here.

class UserManager(BaseUserManager):
    """
    Custom manager for User model where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a user with an email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model that uses email as the unique identifier
    instead of username.
    """
    class UserType(models.TextChoices):
        AGENT = 'agent', 'Agent'
        INVESTOR = 'investor', 'Investor'
        ADMIN = 'admin', 'Admin'
        USER = 'user', 'User'

    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.USER
    )
    is_active = models.BooleanField(default=True, db_index=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now, db_index=True)
    last_login = models.DateTimeField(null=True, blank=True)
    profile_picture = models.URLField(blank=True, null=True)
    
    # Additional fields for property platform
    company_name = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['date_joined']),
        ]

    def __str__(self):
        """
        String representation of the User.
        """
        return self.email

    @property
    def full_name(self):
        """
        Return the full name of the user.
        """
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_agent(self):
        """
        Check if user is an agent.
        """
        return self.user_type == self.UserType.AGENT

    @property
    def is_investor(self):
        """
        Check if user is an investor.
        """
        return self.user_type == self.UserType.INVESTOR

    def get_display_name(self):
        """
        Get display name for the user.
        """
        if self.full_name:
            return self.full_name
        return self.email.split('@')[0]

    @property
    def display_name(self):
        """
        Return the display name of the user.
        """
        return self.get_display_name()

    def update_last_login(self):
        """
        Update the last login timestamp.
        """
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])
