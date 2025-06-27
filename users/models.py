from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from typing import Optional

# Create your models here.

class UserManager(BaseUserManager):
    """
    Custom manager for User model where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email: str, password: Optional[str] = None, **extra_fields) -> 'User':
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

    def create_superuser(self, email: str, password: Optional[str] = None, **extra_fields) -> 'User':
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
    instead of username for the fitness class booking platform.
    """
    class UserType(models.TextChoices):
        USER = 'user', 'User'
        INSTRUCTOR = 'instructor', 'Gym Instructor'
        ADMIN = 'admin', 'Admin'

    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    user_type = models.CharField(
        max_length=12,
        choices=UserType.choices,
        default=UserType.USER
    )
    is_active = models.BooleanField(default=True, db_index=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now, db_index=True)
    last_login = models.DateTimeField(null=True, blank=True)
    profile_picture = models.URLField(blank=True, null=True)
    
    # Fitness platform specific fields
    bio = models.TextField(blank=True, help_text="User's bio or instructor's description")
    company_name = models.CharField(max_length=100, blank=True, help_text="Gym or company name for instructors")
    date_of_birth = models.DateField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=17, blank=True, validators=[phone_regex])
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    fitness_goals = models.TextField(blank=True, help_text="User's fitness goals")
    medical_conditions = models.TextField(blank=True, help_text="Any medical conditions to be aware of")
    preferred_class_types = models.JSONField(default=list, blank=True, help_text="List of preferred class types")

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

    def __str__(self) -> str:
        """
        String representation of the User.
        """
        return self.email

    @property
    def full_name(self) -> str:
        """
        Return the full name of the user.
        """
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_instructor(self) -> bool:
        """
        Check if user is an instructor.
        """
        return self.user_type == self.UserType.INSTRUCTOR

    @property
    def is_admin(self) -> bool:
        """
        Check if user is an admin.
        """
        return self.user_type == self.UserType.ADMIN

    def get_display_name(self) -> str:
        """
        Get display name for the user.
        """
        if self.full_name:
            return self.full_name
        return self.email.split('@')[0]

    @property
    def display_name(self) -> str:
        """
        Return the display name of the user.
        """
        return self.get_display_name()

    def update_last_login(self) -> None:
        """
        Update the last login timestamp.
        """
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])

    def get_age(self) -> Optional[int]:
        """
        Calculate and return user's age.
        """
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

class UserProfile(models.Model):
    """
    Extended profile information for users in the fitness platform.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Fitness preferences
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    
    # Physical information
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Height in cm")
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Weight in kg")
    
    # Fitness tracking
    weekly_workout_goal = models.PositiveIntegerField(default=3, help_text="Target workouts per week")
    preferred_workout_duration = models.PositiveIntegerField(default=60, help_text="Preferred workout duration in minutes")
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    
    # Privacy settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('private', 'Private'),
            ('friends_only', 'Friends Only'),
        ],
        default='public'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        indexes = [
            models.Index(fields=['experience_level']),
            models.Index(fields=['profile_visibility']),
        ]
    
    def __str__(self) -> str:
        return f"Profile for {self.user.email}"
    
    def get_bmi(self) -> Optional[float]:
        """
        Calculate and return BMI if height and weight are available.
        """
        if self.height and self.weight:
            height_m = float(self.height) / 100  # Convert cm to meters
            weight_kg = float(self.weight)
            return round(weight_kg / (height_m ** 2), 2)
        return None
    
    def get_bmi_category(self) -> Optional[str]:
        """
        Get BMI category based on calculated BMI.
        """
        bmi = self.get_bmi()
        if bmi is None:
            return None
        
        if bmi < 18.5:
            return 'underweight'
        elif bmi < 25:
            return 'normal'
        elif bmi < 30:
            return 'overweight'
        else:
            return 'obese'


# Django signals
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender: type[User], instance: User, created: bool, **kwargs) -> None:
    """
    Create a UserProfile when a new User is created.
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender: type[User], instance: User, **kwargs) -> None:
    """
    Save the UserProfile when the User is saved.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
