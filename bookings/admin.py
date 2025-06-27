from django.contrib import admin
from .models import Booking, ClassReview

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Admin for Booking model.
    """
    list_display = ('user', 'class_schedule', 'status', 'booking_time', 'is_waitlisted', 'waitlist_position')
    list_filter = ('status', 'is_waitlisted', 'booking_time', 'class_schedule')
    search_fields = ('user__email', 'class_schedule__class_obj__name')
    ordering = ('-booking_time',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ClassReview)
class ClassReviewAdmin(admin.ModelAdmin):
    """
    Admin for ClassReview model.
    """
    list_display = ('user', 'class_obj', 'class_schedule', 'rating', 'created_at')
    list_filter = ('rating', 'created_at', 'class_obj')
    search_fields = ('user__email', 'class_obj__name', 'review')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
