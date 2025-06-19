from rest_framework.exceptions import APIException
from rest_framework import status

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

class ErrorHandler:
    """
    Utility class to handle exceptions and format error responses.
    """
    @staticmethod
    def handle_exception(exc, context=None):
        from core.utils import ResponseHandler
        # If it's a DRF exception, use its details
        if isinstance(exc, APIException):
            detail = exc.detail if hasattr(exc, 'detail') else str(exc)
            status_code = exc.status_code if hasattr(exc, 'status_code') else status.HTTP_400_BAD_REQUEST
            return ResponseHandler.error(message="Error", error=detail), status_code
        # For other exceptions, return a generic error
        return ResponseHandler.error(message="Internal server error", error=str(exc)), status.HTTP_500_INTERNAL_SERVER_ERROR 

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