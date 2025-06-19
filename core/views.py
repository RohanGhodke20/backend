"""
Core views for the Get Fit API project.
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .utils import ResponseHandler
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """
    API root endpoint providing information about available endpoints.
    """
    logger.info(f"API root accessed by user: {request.user}")
    return Response(ResponseHandler.success(
        message="Get Fit API v1",
        data={
            'version': '1.0.0',
            'endpoints': {
                'users': '/api/v1/users/',
                'admin': '/admin/',
                'swagger': '/swagger/',
                'redoc': '/redoc/',
            }
        }
    ))

def handler404(request, exception=None):
    """
    Custom 404 error handler for API requests.
    Returns JSON response for all requests.
    """
    logger.warning(f"404 error: {request.path} - User: {request.user}")
    return JsonResponse(
        ResponseHandler.error(
            message="Resource not found",
            error="The requested resource was not found on this server."
        ),
        status=404
    )

def handler500(request):
    """
    Custom 500 error handler for API requests.
    Returns JSON response for all requests.
    """
    logger.error(f"500 error: {request.path} - User: {request.user}")
    return JsonResponse(
        ResponseHandler.error(
            message="Internal server error",
            error="An internal server error occurred. Please try again later."
        ),
        status=500
    )

def handler403(request, exception=None):
    """
    Custom 403 error handler for API requests.
    Returns JSON response for all requests.
    """
    logger.warning(f"403 error: {request.path} - User: {request.user}")
    return JsonResponse(
        ResponseHandler.error(
            message="Permission denied",
            error="You don't have permission to access this resource."
        ),
        status=403
    )

def handler400(request, exception=None):
    """
    Custom 400 error handler for API requests.
    Returns JSON response for all requests.
    """
    logger.warning(f"400 error: {request.path} - User: {request.user}")
    return JsonResponse(
        ResponseHandler.error(
            message="Bad request",
            error="The request could not be processed due to invalid syntax."
        ),
        status=400
    ) 