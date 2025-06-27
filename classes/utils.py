"""
Utility functions for the classes app.
"""
from typing import Union
from datetime import datetime


def validate_class_capacity(capacity: int) -> bool:
    """
    Validate class capacity.
    
    Args:
        capacity (int): The class capacity
        
    Returns:
        bool: True if valid, False otherwise
    """
    return capacity > 0 and capacity <= 1000


def calculate_available_slots(total_capacity: int, booked_slots: int) -> int:
    """
    Calculate available slots for a class.
    
    Args:
        total_capacity (int): Total class capacity
        booked_slots (int): Number of booked slots
        
    Returns:
        int: Number of available slots
    """
    return max(0, total_capacity - booked_slots) 