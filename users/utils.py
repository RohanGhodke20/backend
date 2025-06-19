import re
import logging
from typing import Dict, Any, Optional
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from django.db.models import Q
from .models import User

logger = logging.getLogger(__name__)

def validate_phone_number(phone_number: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone_number (str): Phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not phone_number:
        return True  # Allow empty phone numbers
    
    # International phone number regex
    pattern = r'^\+?1?\d{9,15}$'
    return bool(re.match(pattern, phone_number))

def validate_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate user registration data.
    
    Args:
        data (Dict[str, Any]): User data to validate
        
    Returns:
        Dict[str, Any]: Validated data with any corrections
        
    Raises:
        ValidationError: If data is invalid
    """
    errors = {}
    
    # Validate email
    email = data.get('email', '').strip()
    if not email:
        errors['email'] = 'Email is required'
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors['email'] = 'Enter a valid email address'
    
    # Validate password
    password = data.get('password', '')
    if len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters long'
    
    # Validate phone number
    phone_number = data.get('phone_number', '')
    if phone_number and not validate_phone_number(phone_number):
        errors['phone_number'] = 'Enter a valid phone number'
    
    # Validate user type
    user_type = data.get('user_type', '')
    valid_user_types = [choice[0] for choice in User.UserType.choices]
    if user_type and user_type not in valid_user_types:
        errors['user_type'] = f'User type must be one of: {", ".join(valid_user_types)}'
    
    if errors:
        raise ValidationError(errors)
    
    return data

def check_email_availability(email: str) -> bool:
    """
    Check if email is available for registration.
    
    Args:
        email (str): Email to check
        
    Returns:
        bool: True if available, False if already taken
    """
    return not User.objects.filter(email=email).exists()

def get_user_statistics() -> Dict[str, Any]:
    """
    Get user statistics for admin dashboard.
    
    Returns:
        Dict[str, Any]: User statistics
    """
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    verified_users = User.objects.filter(is_verified=True).count()
    
    # Count by user type
    user_types = {}
    for choice in User.UserType.choices:
        user_types[choice[1]] = User.objects.filter(user_type=choice[0]).count()
    
    # Recent registrations (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recent_registrations = User.objects.filter(
        date_joined__gte=thirty_days_ago
    ).count()
    
    return {
        'total_users': total_users,
        'active_users': active_users,
        'verified_users': verified_users,
        'user_types': user_types,
        'recent_registrations': recent_registrations
    }

def search_users(query: str, user_type: Optional[str] = None) -> list:
    """
    Search users by name, email, or company name.
    
    Args:
        query (str): Search query
        user_type (Optional[str]): Filter by user type
        
    Returns:
        list: List of matching users
    """
    queryset = User.objects.filter(is_active=True)
    
    if user_type:
        queryset = queryset.filter(user_type=user_type)
    
    if query:
        queryset = queryset.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(company_name__icontains=query)
        )
    
    return list(queryset.select_related())

def update_user_last_login(user: User) -> None:
    """
    Update user's last login timestamp.
    
    Args:
        user (User): User to update
    """
    try:
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        logger.info(f"Updated last login for user: {user.email}")
    except Exception as e:
        logger.error(f"Failed to update last login for user {user.email}: {str(e)}")

def verify_user_email(user: User) -> bool:
    """
    Mark user as verified.
    
    Args:
        user (User): User to verify
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        logger.info(f"User verified: {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to verify user {user.email}: {str(e)}")
        return False

def deactivate_user(user: User, reason: str = "") -> bool:
    """
    Deactivate a user account.
    
    Args:
        user (User): User to deactivate
        reason (str): Reason for deactivation
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        user.is_active = False
        user.save(update_fields=['is_active'])
        logger.info(f"User deactivated: {user.email}, Reason: {reason}")
        return True
    except Exception as e:
        logger.error(f"Failed to deactivate user {user.email}: {str(e)}")
        return False

def get_user_by_email_or_id(identifier: str) -> Optional[User]:
    """
    Get user by email or ID.
    
    Args:
        identifier (str): Email or ID
        
    Returns:
        Optional[User]: User object if found, None otherwise
    """
    try:
        # Try to get by ID first
        if identifier.isdigit():
            return User.objects.get(id=int(identifier))
        # Then try by email
        return User.objects.get(email=identifier)
    except User.DoesNotExist:
        return None
    except (ValueError, TypeError):
        return None

def format_user_data_for_response(user: User) -> Dict[str, Any]:
    """
    Format user data for API response.
    
    Args:
        user (User): User object
        
    Returns:
        Dict[str, Any]: Formatted user data
    """
    return {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.full_name,
        'display_name': user.get_display_name(),
        'phone_number': user.phone_number,
        'user_type': user.user_type,
        'is_verified': user.is_verified,
        'is_active': user.is_active,
        'date_joined': user.date_joined.isoformat() if user.date_joined else None,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'company_name': user.company_name,
        'license_number': user.license_number,
        'bio': user.bio,
        'website': user.website,
        'profile_picture': user.profile_picture
    } 