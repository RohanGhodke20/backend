"""
Views for the bookings app.
"""
from typing import Dict, Any, Optional
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Booking, ClassReview
from .serializers import (
    BookingListSerializer, BookingDetailSerializer, BookingCreateSerializer,
    BookingUpdateSerializer, BookingCancelSerializer, ClassReviewSerializer,
    ClassReviewListSerializer
)
from classes.models import Class, ClassSchedule
from core.utils import ResponseHandler
from core.exceptions import NotFoundException, BadRequestException
from core.decorators import handle_api_exceptions, log_api_request

class UserBookingListView(generics.ListAPIView):
    """
    API view to list all bookings for the current user.
    Authentication required.
    """
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'is_waitlisted']
    ordering_fields = ['booking_time', 'created_at']
    ordering = ['-booking_time']

    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset for current user's bookings with optimized queries.
        """
        user = self.request.user
        
        # Filter by status if specified
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = Booking.objects.filter(user=user, status=status_filter)
        else:
            queryset = Booking.objects.filter(user=user)
        
        # Filter by upcoming/past bookings
        upcoming_only = self.request.query_params.get('upcoming_only')
        if upcoming_only and upcoming_only.lower() == 'true':
            queryset = queryset.filter(
                class_schedule__start_time__gte=timezone.now()
            )
        
        past_only = self.request.query_params.get('past_only')
        if past_only and past_only.lower() == 'true':
            queryset = queryset.filter(
                class_schedule__start_time__lt=timezone.now()
            )
        
        return (
            queryset
            .select_related('class_schedule', 'class_schedule__class_obj', 'class_schedule__instructor')
            .order_by('-booking_time')
        )

    def list(self, request, *args, **kwargs):
        """
        Override list method to use custom response format.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response(
            ResponseHandler.success(
                message="User bookings retrieved successfully",
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )

class UserBookingDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve detailed information about a specific user booking.
    Authentication required.
    """
    serializer_class = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset for current user's bookings.
        """
        user = self.request.user
        return (
            Booking.objects
            .filter(user=user)
            .select_related('class_schedule', 'class_schedule__class_obj', 'class_schedule__instructor')
        )

    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve method to use custom response format.
        """
        try:
            instance = self.get_object()
        except Booking.DoesNotExist:
            raise NotFoundException(detail="Booking not found")
        
        serializer = self.get_serializer(instance)
        
        return Response(
            ResponseHandler.success(
                message="Booking details retrieved successfully",
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )

class BookingCreateView(generics.CreateAPIView):
    """
    API view to create a new booking.
    Authentication required.
    """
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @handle_api_exceptions
    @log_api_request
    def create(self, request, *args, **kwargs):
        """
        Override create method to use custom response format.
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            booking = serializer.save()
            
            # Prepare response data
            response_serializer = BookingDetailSerializer(booking)
            
            message = "Booking created successfully"
            if booking.is_waitlisted:
                message = f"Booking added to waitlist (position: {booking.waitlist_position})"
            
            return Response(
                ResponseHandler.success(
                    message=message,
                    data=response_serializer.data
                ),
                status=status.HTTP_201_CREATED
            )
        
        raise BadRequestException(detail=serializer.errors)

class BookingUpdateView(generics.UpdateAPIView):
    """
    API view to update booking information.
    Authentication required.
    """
    serializer_class = BookingUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset for current user's active bookings.
        """
        user = self.request.user
        return (
            Booking.objects
            .filter(user=user)
            .exclude(status=Booking.Status.CANCELLED)
            .exclude(status=Booking.Status.COMPLETED)
        )

    def update(self, request, *args, **kwargs):
        """
        Override update method to use custom response format.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            booking = serializer.save()
            response_serializer = BookingDetailSerializer(booking)
            
            return Response(
                ResponseHandler.success(
                    message="Booking updated successfully",
                    data=response_serializer.data
                ),
                status=status.HTTP_200_OK
            )
        
        raise BadRequestException(detail=serializer.errors)

class BookingCancelView(generics.UpdateAPIView):
    """
    API view to cancel a booking.
    Authentication required.
    """
    serializer_class = BookingCancelSerializer
    permission_classes = [permissions.IsAuthenticated]

    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset for current user's cancellable bookings.
        """
        user = self.request.user
        return (
            Booking.objects
            .filter(user=user)
            .exclude(status=Booking.Status.CANCELLED)
            .exclude(status=Booking.Status.COMPLETED)
        )

    def update(self, request, *args, **kwargs):
        """
        Override update method to use custom response format.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            booking = serializer.save()
            response_serializer = BookingDetailSerializer(booking)
            
            return Response(
                ResponseHandler.success(
                    message="Booking cancelled successfully",
                    data=response_serializer.data
                ),
                status=status.HTTP_200_OK
            )
        
        raise BadRequestException(detail=serializer.errors)

class ClassScheduleBookingView(generics.RetrieveAPIView):
    """
    API view to get booking information for a specific class schedule.
    Authentication required.
    """
    serializer_class = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    @handle_api_exceptions
    @log_api_request
    def get_object(self):
        """
        Get the booking for the current user and specified class schedule.
        """
        user = self.request.user
        schedule_id = self.kwargs.get('schedule_id')
        
        try:
            return (
                Booking.objects
                .filter(user=user, class_schedule_id=schedule_id)
                .select_related('class_schedule', 'class_schedule__class_obj', 'class_schedule__instructor')
                .get()
            )
        except Booking.DoesNotExist:
            raise NotFoundException(detail="No booking found for this class schedule")

    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve method to use custom response format.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response(
            ResponseHandler.success(
                message="Booking information retrieved successfully",
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )

class ClassReviewCreateView(generics.CreateAPIView):
    """
    API view to create a class review.
    Authentication required.
    """
    serializer_class = ClassReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    @handle_api_exceptions
    @log_api_request
    def create(self, request, *args, **kwargs):
        """
        Override create method to use custom response format.
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            review = serializer.save()
            response_serializer = ClassReviewSerializer(review)
            
            return Response(
                ResponseHandler.success(
                    message="Review submitted successfully",
                    data=response_serializer.data
                ),
                status=status.HTTP_201_CREATED
            )
        
        raise BadRequestException(detail=serializer.errors)

class ClassReviewListView(generics.ListAPIView):
    """
    API view to list reviews for a specific class.
    Public access allowed.
    """
    serializer_class = ClassReviewListSerializer
    permission_classes = [permissions.AllowAny]
    ordering_fields = ['rating', 'created_at']
    ordering = ['-created_at']

    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset for class reviews with filtering.
        """
        class_id = self.kwargs.get('class_id')
        
        queryset = (
            ClassReview.objects
            .filter(class_obj_id=class_id)
            .select_related('user')
        )
        
        # Filter by rating if specified
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(rating__gte=min_rating)
        
        max_rating = self.request.query_params.get('max_rating')
        if max_rating:
            queryset = queryset.filter(rating__lte=max_rating)
        
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Override list method to use custom response format.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        # Calculate review statistics
        total_reviews = queryset.count()
        avg_rating = queryset.aggregate(avg_rating=Avg('rating'))['avg_rating']
        
        response_data = {
            'reviews': serializer.data,
            'statistics': {
                'total_reviews': total_reviews,
                'average_rating': round(avg_rating, 1) if avg_rating else None,
                'rating_distribution': self._get_rating_distribution(queryset)
            }
        }
        
        return Response(
            ResponseHandler.success(
                message="Class reviews retrieved successfully",
                data=response_data
            ),
            status=status.HTTP_200_OK
        )
    
    def _get_rating_distribution(self, queryset):
        """
        Get rating distribution for the class.
        """
        distribution = {}
        for rating in range(1, 6):
            count = queryset.filter(rating=rating).count()
            distribution[str(rating)] = count
        return distribution

class UserReviewListView(generics.ListAPIView):
    """
    API view to list reviews by the current user.
    Authentication required.
    """
    serializer_class = ClassReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ['rating', 'created_at']
    ordering = ['-created_at']

    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset for current user's reviews.
        """
        user = self.request.user
        return (
            ClassReview.objects
            .filter(user=user)
            .select_related('class_obj', 'class_schedule')
        )

    def list(self, request, *args, **kwargs):
        """
        Override list method to use custom response format.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response(
            ResponseHandler.success(
                message="User reviews retrieved successfully",
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )
