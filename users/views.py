import logging
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer,
    UserDetailSerializer, PasswordChangeSerializer, UserListSerializer
)
from .models import User
from core.utils import ResponseHandler
from core.decorators import handle_api_exceptions, log_api_request, validate_required_fields
from core.exceptions import BadRequestException, UnauthorizedException

# Set up logging
logger = logging.getLogger(__name__)

# Create your views here.

class UserRegistrationView(APIView):
    """
    API view to handle user registration via email and password.
    """
    permission_classes = [AllowAny]
    
    @handle_api_exceptions
    @log_api_request
    @validate_required_fields(['email', 'password'])
    def post(self, request):
        """
        Handle POST request to register a new user.
        Returns a success response with user info or error details.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                ResponseHandler.success(
                    message="User registered successfully",
                    data={"user_id": user.id, "email": user.email}
                ),
                status=status.HTTP_201_CREATED
            )
        
        # If serializer is not valid, raise exception - decorator will handle it
        raise BadRequestException(detail=serializer.errors)

class UserLoginView(APIView):
    """
    Custom login view that returns JWT tokens in our standard response format.
    """
    permission_classes = [AllowAny]
    
    @handle_api_exceptions
    @log_api_request
    @validate_required_fields(['email', 'password'])
    def post(self, request):
        """
        Handle POST request to authenticate user and return JWT tokens.
        """
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = authenticate(email=email, password=password)
        
        if not user:
            raise UnauthorizedException(detail="Invalid email or password")
        
        # Update last login
        user.update_last_login()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response(
            ResponseHandler.success(
                message="Login successful",
                data={
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "user_type": user.user_type
                    }
                }
            ),
            status=status.HTTP_200_OK
        )

class UserProfileView(APIView):
    """
    API view to handle user profile operations.
    """
    permission_classes = [IsAuthenticated]
    
    @handle_api_exceptions
    @log_api_request
    def get(self, request):
        """
        Get current user's profile information.
        """
        serializer = UserDetailSerializer(request.user)
        return Response(
            ResponseHandler.success(
                message="Profile retrieved successfully",
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )
    
    @handle_api_exceptions
    @log_api_request
    def put(self, request):
        """
        Update current user's profile information.
        """
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                ResponseHandler.success(
                    message="Profile updated successfully",
                    data=UserDetailSerializer(user).data
                ),
                status=status.HTTP_200_OK
            )
        
        raise BadRequestException(detail=serializer.errors)

class PasswordChangeView(APIView):
    """
    API view to handle password change functionality.
    """
    permission_classes = [IsAuthenticated]
    
    @handle_api_exceptions
    @log_api_request
    @validate_required_fields(['old_password', 'new_password'])
    def post(self, request):
        """
        Change user's password.
        """
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                ResponseHandler.success(
                    message="Password changed successfully"
                ),
                status=status.HTTP_200_OK
            )
        
        raise BadRequestException(detail=serializer.errors)

class UserListView(generics.ListAPIView):
    """
    API view to list users with filtering and search capabilities.
    """
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['user_type', 'is_verified', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'company_name']
    ordering_fields = ['date_joined', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset with optional filtering by user type.
        """
        queryset = User.objects.filter(is_active=True)
        
        # Filter by user type if specified
        user_type = self.request.query_params.get('user_type', None)
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        # Filter by verification status if specified
        is_verified = self.request.query_params.get('is_verified', None)
        if is_verified is not None:
            is_verified = is_verified.lower() == 'true'
            queryset = queryset.filter(is_verified=is_verified)
        
        return queryset.select_related()

class UserDetailView(generics.RetrieveAPIView):
    """
    API view to get detailed information about a specific user.
    """
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.filter(is_active=True)
    
    @handle_api_exceptions
    @log_api_request
    def get(self, request, *args, **kwargs):
        """
        Get detailed information about a specific user.
        """
        return super().get(request, *args, **kwargs)
