from rest_framework.exceptions import APIException
from rest_framework import status
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

class CustomAPIException(APIException):
    """
    Custom API exception for application-specific errors.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'A server error occurred.'
    default_code = 'error'

    def __init__(self, detail=None, status_code=None, code=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail, code)

def handle_exception(exc, context=None):
    """
    Standalone exception handler for DRF EXCEPTION_HANDLER setting.
    Returns a DRF Response object with standardized error format.
    """
    from core.utils import ResponseHandler
    
    # Log the exception with context information
    request = context.get('request') if context else None
    view = context.get('view') if context else None
    
    user_info = f"User: {request.user}" if request and hasattr(request, 'user') else "Anonymous"
    view_name = view.__class__.__name__ if view else "Unknown"
    path = request.path if request else "Unknown"
    
    if isinstance(exc, APIException):
        detail = exc.detail if hasattr(exc, 'detail') else str(exc)
        status_code = exc.status_code if hasattr(exc, 'status_code') else status.HTTP_400_BAD_REQUEST
        
        # Log API exceptions as warnings
        logger.warning(
            f"API Exception: {status_code} - {detail} | {user_info} | View: {view_name} | Path: {path}"
        )
        
        return Response(
            ResponseHandler.error(message="Error", error=detail),
            status=status_code
        )
    
    # Log unexpected exceptions as errors
    logger.error(
        f"Unexpected Exception: {str(exc)} | {user_info} | View: {view_name} | Path: {path}",
        exc_info=True
    )
    
    return Response(
        ResponseHandler.error(message="Internal server error", error=str(exc)),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

class BadRequestException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Bad request.'
    default_code = 'bad_request'

class UnauthorizedException(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Unauthorized.'
    default_code = 'unauthorized'

class NotFoundException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found.'
    default_code = 'not_found'

class InternalServerErrorException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Internal server error.'
    default_code = 'internal_server_error' 