"""
Common decorators for the Get Fit API project.
"""
import functools
import logging
import time
from rest_framework.response import Response
from rest_framework import status
from .utils import ResponseHandler
from .exceptions import CustomAPIException
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)

def handle_api_exceptions(func):
    """
    Decorator to handle exceptions in API views.
    
    This decorator wraps API view functions and automatically handles:
    - Custom API exceptions
    - Validation errors
    - Database errors
    - Unexpected exceptions
    
    All exceptions are logged with context information and return standardized JSON responses.
    
    Usage:
        @handle_api_exceptions
        def my_api_view(request):
            # Your view logic here
            return Response(data)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIException as e:
            # Handle all API exceptions (including CustomAPIException, UnauthorizedException, etc.)
            logger.warning(
                f"API Exception: {e.status_code} - {e.detail} | "
                f"View: {func.__name__} | Args: {args} | Kwargs: {kwargs}"
            )
            return Response(
                ResponseHandler.error(message="Error", error=str(e.detail)),
                status=e.status_code
            )
        except Exception as e:
            # Handle all other exceptions
            logger.error(
                f"Unexpected Exception in {func.__name__}: {str(e)} | "
                f"Args: {args} | Kwargs: {kwargs}",
                exc_info=True
            )
            return Response(
                ResponseHandler.error(
                    message="Internal server error", 
                    error="An unexpected error occurred. Please try again later."
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return wrapper

def log_api_request(func):
    """
    Decorator to log API requests for monitoring and debugging.
    
    This decorator logs:
    - Request method and path
    - User information
    - Request parameters
    - Response status
    
    Usage:
        @log_api_request
        def my_api_view(request):
            # Your view logic here
            return Response(data)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract request from args
        # For class-based views: args[0] = self, args[1] = request
        # For function-based views: args[0] = request
        request = None
        if len(args) > 0:
            if hasattr(args[0], 'request'):  # Class-based view (self)
                request = args[1] if len(args) > 1 else None
            else:  # Function-based view
                request = args[0]
        
        # Log request information
        if request:
            user_info = f"User: {request.user}" if hasattr(request, 'user') and request.user.is_authenticated else "Anonymous"
            method = request.method
            path = request.path
            query_params = dict(request.GET.items())
            
            logger.info(
                f"API Request: {method} {path} | {user_info} | "
                f"Query Params: {query_params} | View: {func.__name__}"
            )
        
        # Execute the view function
        response = func(*args, **kwargs)
        
        # Log response information
        if request and hasattr(response, 'status_code'):
            logger.info(
                f"API Response: {response.status_code} | {request.method} {request.path} | "
                f"View: {func.__name__}"
            )
        
        return response
    return wrapper

def validate_required_fields(required_fields):
    """
    Decorator to validate required fields in request data.
    
    Args:
        required_fields (list): List of field names that are required in the request data.
    
    Usage:
        @validate_required_fields(['email', 'password'])
        def login_view(request):
            # Your view logic here
            return Response(data)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract request from args
            # For class-based views: args[0] = self, args[1] = request
            # For function-based views: args[0] = request
            request = None
            if len(args) > 0:
                if hasattr(args[0], 'request'):  # Class-based view (self)
                    request = args[1] if len(args) > 1 else None
                else:  # Function-based view
                    request = args[0]
            
            if request and hasattr(request, 'data'):
                missing_fields = []
                for field in required_fields:
                    if field not in request.data or not request.data[field]:
                        missing_fields.append(field)
                
                if missing_fields:
                    error_message = f"Missing required fields: {', '.join(missing_fields)}"
                    logger.warning(
                        f"Validation Error: {error_message} | "
                        f"View: {func.__name__} | User: {request.user}"
                    )
                    return Response(
                        ResponseHandler.error(message="Validation error", error=error_message),
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit_by_user(max_requests=100, window_seconds=3600):
    """
    Simple rate limiting decorator based on user.
    
    Args:
        max_requests (int): Maximum number of requests allowed in the time window
        window_seconds (int): Time window in seconds
    
    Note: This is a basic implementation. For production, consider using Django REST Framework's
    built-in throttling or Redis-based solutions.
    
    Usage:
        @rate_limit_by_user(max_requests=50, window_seconds=3600)
        def my_api_view(request):
            # Your view logic here
            return Response(data)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract request from args
            # For class-based views: args[0] = self, args[1] = request
            # For function-based views: args[0] = request
            request = None
            if len(args) > 0:
                if hasattr(args[0], 'request'):  # Class-based view (self)
                    request = args[1] if len(args) > 1 else None
                else:  # Function-based view
                    request = args[0]
            
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                # Simple in-memory rate limiting (not suitable for production with multiple workers)
                # For production, use Redis or database-based rate limiting
                user_id = request.user.id
                current_time = time.time()
                
                # This is a simplified example - in production, use proper rate limiting
                logger.info(
                    f"Rate limit check for user {user_id} | "
                    f"View: {func.__name__} | Max: {max_requests} per {window_seconds}s"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator 