"""
Utility functions for the bookings app.
"""
from typing import Union
from datetime import datetime, timedelta


def validate_booking_time(class_schedule, booking_time: datetime) -> bool:
    """
    Validate if booking time is within class schedule.
    
    Args:
        class_schedule: ClassSchedule instance
        booking_time (datetime): datetime of booking
        
    Returns:
        bool: True if valid, False otherwise
    """
    return class_schedule.start_time <= booking_time <= class_schedule.end_time


def can_cancel_booking(booking, current_time: datetime) -> bool:
    """
    Check if a booking can be cancelled based on cancellation policy.
    
    Args:
        booking: Booking instance
        current_time (datetime): Current datetime
        
    Returns:
        bool: True if can be cancelled, False otherwise
    """
    # Allow cancellation up to 24 hours before class
    cancellation_deadline = booking.class_schedule.start_time - timedelta(hours=24)
    return current_time < cancellation_deadline 