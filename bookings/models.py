from django.db import models
from django.utils import timezone
from typing import Optional
from users.models import User

class Booking(models.Model):
    """
    Model for user bookings of class sessions.
    """
    class Status(models.TextChoices):
        BOOKED = 'booked', 'Booked'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'
        WAITLISTED = 'waitlisted', 'Waitlisted'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    class_schedule = models.ForeignKey('classes.ClassSchedule', on_delete=models.CASCADE, related_name='bookings')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.BOOKED, db_index=True)
    booking_time = models.DateTimeField(default=timezone.now, db_index=True)
    cancellation_time = models.DateTimeField(null=True, blank=True)
    is_waitlisted = models.BooleanField(default=False)
    waitlist_position = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Additional notes or requirements from the user")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'
        unique_together = ('user', 'class_schedule')
        ordering = ['-booking_time']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['class_schedule']),
            models.Index(fields=['status']),
            models.Index(fields=['is_waitlisted']),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.class_schedule} ({self.status})"

    @property
    def is_active(self) -> bool:
        """
        Check if the booking is currently active (not cancelled or completed).
        """
        return self.status == self.Status.BOOKED

    def cancel(self, reason: Optional[str] = None) -> None:
        """
        Cancel the booking and update status.
        """
        self.status = self.Status.CANCELLED
        self.cancellation_time = timezone.now()
        self.save(update_fields=['status', 'cancellation_time'])
        if reason:
            self.notes = (self.notes or '') + f"\nCancellation reason: {reason}"
            self.save(update_fields=['notes'])

class ClassReview(models.Model):
    """
    Model for user reviews/ratings of classes.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='class_reviews')
    class_schedule = models.ForeignKey('classes.ClassSchedule', on_delete=models.CASCADE, related_name='reviews')
    class_obj = models.ForeignKey('classes.Class', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(default=5, choices=[(i, str(i)) for i in range(1, 6)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'class_reviews'
        unique_together = ('user', 'class_schedule')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['class_schedule']),
            models.Index(fields=['class_obj']),
            models.Index(fields=['rating']),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.class_obj.name} ({self.rating}★)"
