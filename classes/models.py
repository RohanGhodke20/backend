from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from typing import Optional, List
from users.models import User


class ClassCategory(models.Model):
    """
    Model for different categories/types of fitness classes.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, help_text="Description of the class category")
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name or identifier")
    color = models.CharField(max_length=7, blank=True, help_text="Hex color code for the category")
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0, help_text="Order for display purposes")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'class_categories'
        ordering = ['sort_order', 'name']
        verbose_name = 'Class Category'
        verbose_name_plural = 'Class Categories'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['sort_order']),
        ]
    
    def __str__(self) -> str:
        return self.name
    
    @property
    def class_count(self) -> int:
        """
        Get the number of active classes in this category, using annotation if present.
        """
        if 'annotated_class_count' in self.__dict__:
            return self.__dict__['annotated_class_count']
        return self.classes.filter(is_active=True).count()


class Class(models.Model):
    """
    Model for fitness class definitions.
    """
    class DifficultyLevel(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'
        ALL_LEVELS = 'all_levels', 'All Levels'
    
    class LocationType(models.TextChoices):
        IN_PERSON = 'in_person', 'In Person'
        VIRTUAL = 'virtual', 'Virtual'
        HYBRID = 'hybrid', 'Hybrid'
    
    # Basic Information
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(help_text="Detailed description of the class")
    category = models.ForeignKey(
        ClassCategory, 
        on_delete=models.CASCADE, 
        related_name='classes',
        help_text="Category this class belongs to"
    )
    instructor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='instructed_classes',
        limit_choices_to={'user_type': User.UserType.INSTRUCTOR},
        help_text="Instructor for this class"
    )
    
    # Class Details
    duration = models.PositiveIntegerField(
        help_text="Duration in minutes",
        validators=[MinValueValidator(15), MaxValueValidator(300)]
    )
    difficulty_level = models.CharField(
        max_length=15,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.ALL_LEVELS
    )
    max_capacity = models.PositiveIntegerField(
        default=20,
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        help_text="Maximum number of participants"
    )
    
    # Location and Type
    location_type = models.CharField(
        max_length=10,
        choices=LocationType.choices,
        default=LocationType.IN_PERSON
    )
    location_name = models.CharField(max_length=200, blank=True, help_text="Gym name or virtual platform")
    location_address = models.TextField(blank=True, help_text="Physical address for in-person classes")
    
    # Requirements and Information
    requirements = models.TextField(blank=True, help_text="What participants need to bring or prepare")
    what_to_expect = models.TextField(blank=True, help_text="What participants can expect from the class")
    benefits = models.TextField(blank=True, help_text="Benefits of taking this class")
    
    # Pricing (optional for now, can be extended later)
    price = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Price per class session"
    )
    currency = models.CharField(max_length=3, default='USD', help_text="Currency code")
    
    # Status and Visibility
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    
    # Media
    image = models.URLField(blank=True, help_text="URL to class image")
    video_url = models.URLField(blank=True, help_text="URL to promotional video")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'classes'
        ordering = ['-is_featured', '-created_at']
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['instructor']),
            models.Index(fields=['difficulty_level']),
            models.Index(fields=['location_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} - {self.instructor.get_display_name()}"
    
    @property
    def average_rating(self) -> Optional[float]:
        """
        Calculate average rating from reviews.
        """
        from bookings.models import ClassReview
        reviews = ClassReview.objects.filter(class_obj=self)
        if reviews.exists():
            return round(reviews.aggregate(avg=models.Avg('rating'))['avg'], 1)
        return None
    
    @property
    def review_count(self) -> int:
        """
        Get the number of reviews for this class.
        """
        from bookings.models import ClassReview
        return ClassReview.objects.filter(class_obj=self).count()
    
    @property
    def upcoming_sessions_count(self) -> int:
        """
        Get the number of upcoming sessions for this class.
        """
        return self.schedules.filter(
            start_time__gte=timezone.now(),
            status=ClassSchedule.Status.ACTIVE
        ).count()
    
    def get_available_slots(self, schedule_id: Optional[int] = None) -> int:
        """
        Get available slots for a specific schedule or all upcoming schedules.
        """
        from .utils import calculate_available_slots
        
        if schedule_id:
            try:
                schedule = self.schedules.get(id=schedule_id)
                return calculate_available_slots(schedule.max_capacity, schedule.booked_slots)
            except ClassSchedule.DoesNotExist:
                return 0
        
        # Get total available slots across all upcoming sessions
        upcoming_schedules = self.schedules.filter(
            start_time__gte=timezone.now(),
            status=ClassSchedule.Status.ACTIVE
        )
        total_available = 0
        for schedule in upcoming_schedules:
            total_available += calculate_available_slots(schedule.max_capacity, schedule.booked_slots)
        
        return total_available


class ClassSchedule(models.Model):
    """
    Model for individual class sessions/schedules.
    """
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'
        FULL = 'full', 'Full'
    
    class RecurringType(models.TextChoices):
        NONE = 'none', 'No Recurring'
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
    
    # Class and Schedule Information
    class_obj = models.ForeignKey(
        Class, 
        on_delete=models.CASCADE, 
        related_name='schedules',
        help_text="The class this schedule belongs to"
    )
    instructor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='scheduled_classes',
        limit_choices_to={'user_type': User.UserType.INSTRUCTOR},
        help_text="Instructor for this session"
    )
    
    # Time and Date
    start_time = models.DateTimeField(db_index=True, help_text="Start time of the class")
    end_time = models.DateTimeField(help_text="End time of the class")
    
    # Capacity and Booking
    max_capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        help_text="Maximum capacity for this session"
    )
    booked_slots = models.PositiveIntegerField(
        default=0,
        help_text="Number of booked slots"
    )
    waitlist_enabled = models.BooleanField(default=True, help_text="Enable waitlist when full")
    
    # Recurring Schedule
    recurring_type = models.CharField(
        max_length=10,
        choices=RecurringType.choices,
        default=RecurringType.NONE,
        help_text="Type of recurring schedule"
    )
    recurring_end_date = models.DateField(
        null=True, 
        blank=True,
        help_text="End date for recurring schedule"
    )
    parent_schedule = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recurring_instances',
        help_text="Parent schedule for recurring instances"
    )
    
    # Status and Notes
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True
    )
    notes = models.TextField(blank=True, help_text="Additional notes for this session")
    cancellation_reason = models.TextField(blank=True, help_text="Reason for cancellation if applicable")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'class_schedules'
        ordering = ['start_time']
        verbose_name = 'Class Schedule'
        verbose_name_plural = 'Class Schedules'
        indexes = [
            models.Index(fields=['class_obj']),
            models.Index(fields=['instructor']),
            models.Index(fields=['start_time']),
            models.Index(fields=['status']),
            models.Index(fields=['recurring_type']),
            models.Index(fields=['parent_schedule']),
        ]
    
    def __str__(self) -> str:
        return f"{self.class_obj.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs) -> None:
        """
        Override save to automatically set end_time and update status.
        """
        # Set end_time based on class duration if not provided
        if not self.end_time:
            self.end_time = self.start_time + timezone.timedelta(minutes=self.class_obj.duration)
        
        # Update status based on capacity
        if self.booked_slots >= self.max_capacity:
            self.status = self.Status.FULL
        elif self.status == self.Status.FULL and self.booked_slots < self.max_capacity:
            self.status = self.Status.ACTIVE
        
        # Update status for past classes
        if self.start_time < timezone.now() and self.status == self.Status.ACTIVE:
            self.status = self.Status.COMPLETED
        
        super().save(*args, **kwargs)
    
    @property
    def available_slots(self) -> int:
        """
        Calculate available slots for this schedule.
        """
        from .utils import calculate_available_slots
        return calculate_available_slots(self.max_capacity, self.booked_slots)
    
    @property
    def is_full(self) -> bool:
        """
        Check if the class is full.
        """
        return self.booked_slots >= self.max_capacity
    
    @property
    def is_upcoming(self) -> bool:
        """
        Check if the class is in the future.
        """
        return self.start_time > timezone.now()
    
    @property
    def is_past(self) -> bool:
        """
        Check if the class is in the past.
        """
        return self.start_time < timezone.now()
    
    @property
    def duration_minutes(self) -> int:
        """
        Calculate duration in minutes.
        """
        return int((self.end_time - self.start_time).total_seconds() / 60)
    
    def can_book(self, user: User) -> bool:
        """
        Check if a user can book this class.
        """
        # Check if class is active and not full
        if self.status != self.Status.ACTIVE or self.is_full:
            return False
        
        # Check if class is in the future
        if not self.is_upcoming:
            return False
        
        # Check if user already has a booking for this schedule
        from bookings.models import Booking
        if Booking.objects.filter(user=user, class_schedule=self).exists():
            return False
        
        return True

    def get_waitlist_position(self, user: User) -> Optional[int]:
        """
        Get user's position in waitlist if applicable.
        """
        from bookings.models import Booking
        try:
            booking = Booking.objects.get(user=user, class_schedule=self)
            if booking.is_waitlisted:
                return booking.waitlist_position
        except Booking.DoesNotExist:
            pass
        return None
