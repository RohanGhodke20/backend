from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserRegistrationSerializer
from core.utils import ResponseHandler

# Create your views here.

class UserRegistrationView(APIView):
    """
    API view to handle user registration via email and password.
    """
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
        # If serializer is not valid, return error details
        return Response(
            ResponseHandler.error(
                message="Registration failed",
                error=serializer.errors
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
