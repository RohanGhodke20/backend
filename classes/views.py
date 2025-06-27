"""
Views for the classes app.
"""
from typing import Dict, Any, Optional
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Prefetch, Q, Avg
from django.db import models
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ClassCategory, Class, ClassSchedule
from users.models import User
from .serializers import (
    ClassCategoryListSerializer, ClassCategoryDetailSerializer,
    ClassListSerializer, ClassDetailSerializer, ClassSearchSerializer,
    ClassScheduleSerializer
)
from core.utils import ResponseHandler
from core.exceptions import NotFoundException
from core.decorators import handle_api_exceptions, log_api_request

# Views will be added as we implement the models

class ClassCategoryListView(generics.ListAPIView):
    """
    API view to list all active class categories with class count.
    Public access allowed for browsing.
    Optimized with annotation.
    """
    serializer_class = ClassCategoryListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """
        Get queryset with optimized annotations.
        """
        # Only active categories, annotate with count of active classes
        return (
            ClassCategory.objects
            .filter(is_active=True)
            .annotate(annotated_class_count=Count('classes', filter=models.Q(classes__is_active=True)))
            .order_by('sort_order', 'name')
        )

    def list(self, request, *args, **kwargs):
        """
        Override list method to use custom response format.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response(
            ResponseHandler.success(
                message="Class categories retrieved successfully",
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )

class ClassCategoryDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve a class category with its active classes.
    Public access allowed for browsing.
    Optimized with prefetch and annotation.
    """
    serializer_class = ClassCategoryDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'

    def get_queryset(self):
        """
        Get queryset with optimized prefetch and annotations.
        """
        # Prefetch only active classes and their instructors
        return (
            ClassCategory.objects
            .filter(is_active=True)
            .annotate(annotated_class_count=Count('classes', filter=models.Q(classes__is_active=True)))
            .prefetch_related(
                Prefetch(
                    'classes',
                    queryset=Class.objects.filter(is_active=True).select_related('instructor')
                )
            )
        )

    @handle_api_exceptions
    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve method to use custom response format and provide a specific 404 message.
        """
        try:
            instance = self.get_object()
        except Http404:
            raise NotFoundException(detail="Class category not found")
        serializer = self.get_serializer(instance)
        
        return Response(
            ResponseHandler.success(
                message="Class category retrieved successfully",
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )

class ClassListView(generics.ListAPIView):
    """
    API view to list all active classes with filtering and search capabilities.
    Public access allowed for browsing.
    """
    serializer_class = ClassListSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['category', 'difficulty_level', 'location_type', 'is_featured']
    search_fields = ['name', 'description', 'instructor__first_name', 'instructor__last_name']
    ordering_fields = ['name', 'duration', 'price', 'created_at', 'average_rating']
    ordering = ['-is_featured', '-created_at']

    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset with optimized queries and filtering.
        """
        queryset = (
            Class.objects
            .filter(is_active=True)
            .select_related('instructor', 'category')
            .prefetch_related('schedules')
        )
        
        # Filter by instructor if specified
        instructor_id = self.request.query_params.get('instructor_id')
        if instructor_id:
            queryset = queryset.filter(instructor_id=instructor_id)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filter by duration range
        min_duration = self.request.query_params.get('min_duration')
        max_duration = self.request.query_params.get('max_duration')
        if min_duration:
            queryset = queryset.filter(duration__gte=min_duration)
        if max_duration:
            queryset = queryset.filter(duration__lte=max_duration)
        
        # Filter by upcoming sessions
        has_upcoming = self.request.query_params.get('has_upcoming')
        if has_upcoming and has_upcoming.lower() == 'true':
            queryset = queryset.filter(
                schedules__start_time__gte=timezone.now(),
                schedules__status=ClassSchedule.Status.ACTIVE
            ).distinct()
        
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Override list method to use custom response format.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response(
            ResponseHandler.success(
                message="Classes retrieved successfully",
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )

class ClassDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve detailed information about a specific class.
    Public access allowed for browsing.
    """
    serializer_class = ClassDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'

    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset with optimized prefetch for detailed view.
        """
        return (
            Class.objects
            .filter(is_active=True)
            .select_related('instructor', 'category')
            .prefetch_related(
                Prefetch(
                    'schedules',
                    queryset=ClassSchedule.objects.filter(
                        start_time__gte=timezone.now()
                    ).order_by('start_time')
                )
            )
        )

    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve method to use custom response format.
        """
        try:
            instance = self.get_object()
        except Http404:
            raise NotFoundException(detail="Class not found")
        
        serializer = self.get_serializer(instance)
        
        return Response(
            ResponseHandler.success(
                message="Class details retrieved successfully",
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )

class ClassSearchView(generics.ListAPIView):
    """
    API view for advanced class search with multiple parameters.
    Public access allowed for browsing.
    Enhanced with calendar integration and time-based filtering.
    """
    serializer_class = ClassSearchSerializer
    permission_classes = [permissions.AllowAny]

    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset with advanced search filtering including calendar integration.
        """
        queryset = (
            Class.objects
            .filter(is_active=True)
            .select_related('instructor', 'category')
            .prefetch_related('schedules')
        )
        
        # Search query with improved relevance
        search_query = self.request.query_params.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(instructor__first_name__icontains=search_query) |
                Q(instructor__last_name__icontains=search_query) |
                Q(category__name__icontains=search_query) |
                Q(location_name__icontains=search_query)
            )
        
        # Category filter
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Difficulty level filter
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        # Location type filter
        location_type = self.request.query_params.get('location_type')
        if location_type:
            queryset = queryset.filter(location_type=location_type)
        
        # Instructor filter
        instructor_id = self.request.query_params.get('instructor_id')
        if instructor_id:
            queryset = queryset.filter(instructor_id=instructor_id)
        
        # Price range filter
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Duration range filter
        min_duration = self.request.query_params.get('min_duration')
        max_duration = self.request.query_params.get('max_duration')
        if min_duration:
            queryset = queryset.filter(duration__gte=min_duration)
        if max_duration:
            queryset = queryset.filter(duration__lte=max_duration)
        
        # Featured classes filter
        featured_only = self.request.query_params.get('featured_only')
        if featured_only and featured_only.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # Available classes filter (has upcoming sessions)
        available_only = self.request.query_params.get('available_only')
        if available_only and available_only.lower() == 'true':
            queryset = queryset.filter(
                schedules__start_time__gte=timezone.now(),
                schedules__status=ClassSchedule.Status.ACTIVE
            ).distinct()
        
        # Calendar-based filtering
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date or end_date:
            schedule_filter = Q()
            if start_date:
                try:
                    start_datetime = timezone.datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                    schedule_filter &= Q(schedules__start_time__gte=start_datetime)
                except ValueError:
                    pass
            if end_date:
                try:
                    end_datetime = timezone.datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                    end_datetime = end_datetime + timezone.timedelta(days=1)  # Include the entire day
                    schedule_filter &= Q(schedules__start_time__lt=end_datetime)
                except ValueError:
                    pass
            
            if schedule_filter:
                queryset = queryset.filter(schedule_filter).distinct()
        
        # Time of day filtering
        time_of_day = self.request.query_params.get('time_of_day')
        if time_of_day:
            if time_of_day == 'morning':
                queryset = queryset.filter(
                    schedules__start_time__hour__gte=6,
                    schedules__start_time__hour__lt=12
                ).distinct()
            elif time_of_day == 'afternoon':
                queryset = queryset.filter(
                    schedules__start_time__hour__gte=12,
                    schedules__start_time__hour__lt=17
                ).distinct()
            elif time_of_day == 'evening':
                queryset = queryset.filter(
                    schedules__start_time__hour__gte=17,
                    schedules__start_time__hour__lt=22
                ).distinct()
            elif time_of_day == 'night':
                queryset = queryset.filter(
                    Q(schedules__start_time__hour__gte=22) |
                    Q(schedules__start_time__hour__lt=6)
                ).distinct()
        
        # Day of week filtering
        day_of_week = self.request.query_params.get('day_of_week')
        if day_of_week:
            try:
                day_num = int(day_of_week)  # 0=Monday, 6=Sunday
                queryset = queryset.filter(
                    schedules__start_time__week_day=day_num + 1  # Django uses 1=Sunday, 2=Monday
                ).distinct()
            except ValueError:
                pass
        
        # Rating filter
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            try:
                min_rating_float = float(min_rating)
                # This would require a more complex query with annotations
                # For now, we'll filter by classes that have reviews with the minimum rating
                queryset = queryset.filter(
                    reviews__rating__gte=min_rating_float
                ).distinct()
            except ValueError:
                pass
        
        # Capacity filter
        min_capacity = self.request.query_params.get('min_capacity')
        max_capacity = self.request.query_params.get('max_capacity')
        if min_capacity:
            queryset = queryset.filter(max_capacity__gte=min_capacity)
        if max_capacity:
            queryset = queryset.filter(max_capacity__lte=max_capacity)
        
        return queryset.order_by('-is_featured', '-created_at')

    def list(self, request, *args, **kwargs):
        """
        Override list method to use custom response format with search metadata.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        # Prepare search metadata
        search_metadata = {
            'total_results': queryset.count(),
            'search_query': request.query_params.get('q', ''),
            'filters_applied': self._get_applied_filters(request),
            'suggestions': self._get_search_suggestions(request)
        }
        
        response_data = {
            'results': serializer.data,
            'metadata': search_metadata
        }
        
        return Response(
            ResponseHandler.success(
                message="Class search completed successfully",
                data=response_data
            ),
            status=status.HTTP_200_OK
        )
    
    def _get_applied_filters(self, request):
        """
        Get list of filters that were applied to the search.
        """
        filters = []
        filter_mapping = {
            'category_id': 'Category',
            'difficulty': 'Difficulty Level',
            'location_type': 'Location Type',
            'instructor_id': 'Instructor',
            'min_price': 'Min Price',
            'max_price': 'Max Price',
            'min_duration': 'Min Duration',
            'max_duration': 'Max Duration',
            'featured_only': 'Featured Only',
            'available_only': 'Available Only',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'time_of_day': 'Time of Day',
            'day_of_week': 'Day of Week',
            'min_rating': 'Min Rating',
            'min_capacity': 'Min Capacity',
            'max_capacity': 'Max Capacity'
        }
        
        for param, display_name in filter_mapping.items():
            value = request.query_params.get(param)
            if value:
                filters.append({
                    'name': display_name,
                    'value': value,
                    'param': param
                })
        
        return filters
    
    def _get_search_suggestions(self, request):
        """
        Get search suggestions based on current query.
        """
        suggestions = []
        search_query = request.query_params.get('q', '').strip()
        
        if search_query:
            # Get popular class names that match the search
            popular_classes = (
                Class.objects
                .filter(name__icontains=search_query, is_active=True)
                .values_list('name', flat=True)
                .distinct()[:5]
            )
            suggestions.extend([f"Class: {name}" for name in popular_classes])
            
            # Get instructor names that match the search
            instructor_names = (
                User.objects
                .filter(
                    Q(first_name__icontains=search_query) | 
                    Q(last_name__icontains=search_query),
                    user_type=User.UserType.INSTRUCTOR,
                    is_active=True
                )
                .values_list('first_name', 'last_name')
                .distinct()[:5]
            )
            suggestions.extend([f"Instructor: {first} {last}" for first, last in instructor_names])
            
            # Get category names that match the search
            category_names = (
                ClassCategory.objects
                .filter(name__icontains=search_query, is_active=True)
                .values_list('name', flat=True)
                .distinct()[:3]
            )
            suggestions.extend([f"Category: {name}" for name in category_names])
        
        return suggestions

class InstructorClassListView(generics.ListAPIView):
    """
    API view to list classes for a specific instructor.
    Authentication required for instructor-specific data.
    """
    serializer_class = ClassListSerializer
    permission_classes = [permissions.IsAuthenticated]

    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset for instructor's classes.
        """
        instructor_id = self.kwargs.get('instructor_id')
        return (
            Class.objects
            .filter(
                instructor_id=instructor_id,
                instructor__user_type=User.UserType.INSTRUCTOR,
                is_active=True
            )
            .select_related('instructor', 'category')
            .order_by('-is_featured', '-created_at')
        )

    def list(self, request, *args, **kwargs):
        """
        Override list method to use custom response format.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response(
            ResponseHandler.success(
                message="Instructor classes retrieved successfully",
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )

class ClassCalendarView(generics.ListAPIView):
    """
    API view for calendar integration - returns class schedules in calendar format.
    Public access allowed for browsing.
    """
    serializer_class = ClassScheduleSerializer
    permission_classes = [permissions.AllowAny]

    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset for calendar view with date range filtering.
        """
        # Get date range parameters
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        # Default to current month if no dates provided
        if not start_date:
            start_date = timezone.now().replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            # Get last day of current month
            next_month = timezone.now().replace(day=1) + timezone.timedelta(days=32)
            end_date = (next_month.replace(day=1) - timezone.timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Convert to datetime objects
        try:
            start_datetime = timezone.datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            end_datetime = timezone.datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc) + timezone.timedelta(days=1)
        except ValueError:
            # Fallback to current month
            start_datetime = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = start_datetime + timezone.timedelta(days=32)
            end_datetime = next_month.replace(day=1)
        
        queryset = (
            ClassSchedule.objects
            .filter(
                start_time__gte=start_datetime,
                start_time__lt=end_datetime,
                status=ClassSchedule.Status.ACTIVE
            )
            .select_related('class_obj', 'instructor')
        )
        
        # Filter by class if specified
        class_id = self.request.query_params.get('class_id')
        if class_id:
            queryset = queryset.filter(class_obj_id=class_id)
        
        # Filter by instructor if specified
        instructor_id = self.request.query_params.get('instructor_id')
        if instructor_id:
            queryset = queryset.filter(instructor_id=instructor_id)
        
        # Filter by category if specified
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(class_obj__category_id=category_id)
        
        return queryset.order_by('start_time')

    def _group_by_date(self, queryset, serialized_data):
        """
        Group calendar events by date for easier frontend consumption.
        """
        grouped_data = {}
        
        for schedule, data in zip(queryset, serialized_data):
            date_key = schedule.start_time.strftime('%Y-%m-%d')
            
            if date_key not in grouped_data:
                grouped_data[date_key] = {
                    'date': date_key,
                    'day_name': schedule.start_time.strftime('%A'),
                    'events': []
                }
            
            # Add class information to the event
            event_data = {
                'id': data['id'],
                'title': schedule.class_obj.name,
                'start_time': data['start_time'],
                'end_time': data['end_time'],
                'instructor': schedule.instructor.get_display_name(),
                'available_slots': data['available_slots'],
                'is_full': data['is_full'],
                'class_id': schedule.class_obj.id,
                'instructor_id': schedule.instructor.id,
                'category': schedule.class_obj.category.name,
                'difficulty_level': schedule.class_obj.difficulty_level,
                'location_type': schedule.class_obj.location_type,
                'location_name': schedule.class_obj.location_name
            }
            
            grouped_data[date_key]['events'].append(event_data)
        
        # Sort events within each day by start time
        for date_data in grouped_data.values():
            date_data['events'].sort(key=lambda x: x['start_time'])
        
        return list(grouped_data.values())

    def list(self, request, *args, **kwargs):
        """
        Override list method to return calendar-friendly format.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        # Group by date for calendar view
        calendar_data = self._group_by_date(queryset, serializer.data)
        
        # Get date range info
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        response_data = {
            'calendar_events': serializer.data,
            'grouped_by_date': calendar_data,
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'total_events': queryset.count()
        }
        
        return Response(
            ResponseHandler.success(
                message="Calendar data retrieved successfully",
                data=response_data
            ),
            status=status.HTTP_200_OK
        )

class AdminClassManagementView(generics.ListCreateAPIView):
    """
    API view for admin class management - list and create classes.
    Admin authentication required.
    """
    serializer_class = ClassDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['category', 'difficulty_level', 'location_type', 'is_active', 'is_featured']
    search_fields = ['name', 'description', 'instructor__first_name', 'instructor__last_name']
    ordering_fields = ['name', 'created_at', 'is_featured']
    ordering = ['-created_at']

    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset for admin class management.
        """
        # Check if user is admin
        if not self.request.user.is_admin:
            raise permissions.PermissionDenied("Admin access required")
        
        return (
            Class.objects
            .select_related('instructor', 'category')
            .prefetch_related('schedules')
        )

    def list(self, request, *args, **kwargs):
        """
        Override list method to include admin-specific data.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        # Get admin statistics
        stats = self._get_admin_statistics()
        
        response_data = {
            'classes': serializer.data,
            'statistics': stats
        }
        
        return Response(
            ResponseHandler.success(
                message="Admin class data retrieved successfully",
                data=response_data
            ),
            status=status.HTTP_200_OK
        )
    
    def _get_admin_statistics(self):
        """
        Get admin statistics for the dashboard.
        """
        total_classes = Class.objects.count()
        active_classes = Class.objects.filter(is_active=True).count()
        featured_classes = Class.objects.filter(is_featured=True).count()
        total_schedules = ClassSchedule.objects.count()
        active_schedules = ClassSchedule.objects.filter(status=ClassSchedule.Status.ACTIVE).count()
        
        # Get class distribution by category
        category_stats = (
            ClassCategory.objects
            .annotate(class_count=Count('classes'))
            .values('name', 'class_count')
        )
        
        # Get class distribution by difficulty
        difficulty_stats = (
            Class.objects
            .values('difficulty_level')
            .annotate(count=Count('id'))
        )
        
        return {
            'total_classes': total_classes,
            'active_classes': active_classes,
            'featured_classes': featured_classes,
            'total_schedules': total_schedules,
            'active_schedules': active_schedules,
            'category_distribution': list(category_stats),
            'difficulty_distribution': list(difficulty_stats)
        }

class AdminClassDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for admin class detail management.
    Admin authentication required.
    """
    serializer_class = ClassDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset for admin class management.
        """
        # Check if user is admin
        if not self.request.user.is_admin:
            raise permissions.PermissionDenied("Admin access required")
        
        return (
            Class.objects
            .select_related('instructor', 'category')
            .prefetch_related('schedules')
        )

    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve method to include admin-specific data.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Get booking statistics for this class
        booking_stats = self._get_class_booking_statistics(instance)
        
        response_data = {
            'class_data': serializer.data,
            'booking_statistics': booking_stats
        }
        
        return Response(
            ResponseHandler.success(
                message="Admin class details retrieved successfully",
                data=response_data
            ),
            status=status.HTTP_200_OK
        )
    
    def _get_class_booking_statistics(self, class_obj):
        """
        Get booking statistics for a specific class.
        """
        from bookings.models import Booking
        
        total_bookings = Booking.objects.filter(class_schedule__class_obj=class_obj).count()
        active_bookings = Booking.objects.filter(
            class_schedule__class_obj=class_obj,
            status=Booking.Status.BOOKED
        ).count()
        waitlisted_bookings = Booking.objects.filter(
            class_schedule__class_obj=class_obj,
            status=Booking.Status.WAITLISTED
        ).count()
        completed_bookings = Booking.objects.filter(
            class_schedule__class_obj=class_obj,
            status=Booking.Status.COMPLETED
        ).count()
        
        return {
            'total_bookings': total_bookings,
            'active_bookings': active_bookings,
            'waitlisted_bookings': waitlisted_bookings,
            'completed_bookings': completed_bookings
        }

class AdminCategoryManagementView(generics.ListCreateAPIView):
    """
    API view for admin category management.
    Admin authentication required.
    """
    serializer_class = ClassCategoryDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']
    ordering = ['sort_order', 'name']

    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset for admin category management.
        """
        # Check if user is admin
        if not self.request.user.is_admin:
            raise permissions.PermissionDenied("Admin access required")
        
        return (
            ClassCategory.objects
            .annotate(annotated_class_count=Count('classes'))
            .prefetch_related('classes')
        )

    def list(self, request, *args, **kwargs):
        """
        Override list method to include admin-specific data.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        # Get category statistics
        stats = self._get_category_statistics()
        
        response_data = {
            'categories': serializer.data,
            'statistics': stats
        }
        
        return Response(
            ResponseHandler.success(
                message="Admin category data retrieved successfully",
                data=response_data
            ),
            status=status.HTTP_200_OK
        )
    
    def _get_category_statistics(self):
        """
        Get category statistics for the admin dashboard.
        """
        total_categories = ClassCategory.objects.count()
        active_categories = ClassCategory.objects.filter(is_active=True).count()
        
        # Get top categories by class count
        top_categories = (
            ClassCategory.objects
            .annotate(class_count=Count('classes'))
            .filter(class_count__gt=0)
            .order_by('-class_count')[:5]
            .values('name', 'class_count')
        )
        
        return {
            'total_categories': total_categories,
            'active_categories': active_categories,
            'top_categories': list(top_categories)
        }

class AdminAnalyticsView(generics.ListAPIView):
    """
    API view for admin analytics and reporting.
    Admin authentication required.
    """
    permission_classes = [permissions.IsAuthenticated]

    @handle_api_exceptions
    @log_api_request
    def get(self, request, *args, **kwargs):
        """
        Get comprehensive analytics for the admin dashboard.
        """
        # Check if user is admin
        if not request.user.is_admin:
            raise permissions.PermissionDenied("Admin access required")
        
        # Get analytics data
        analytics_data = self._get_analytics_data(request)
        
        return Response(
            ResponseHandler.success(
                message="Admin analytics retrieved successfully",
                data=analytics_data
            ),
            status=status.HTTP_200_OK
        )
    
    def _get_analytics_data(self, request):
        """
        Get comprehensive analytics data.
        """
        from bookings.models import Booking
        from users.models import User
        
        # Time period filter
        period = request.query_params.get('period', 'month')  # week, month, year
        
        if period == 'week':
            start_date = timezone.now() - timezone.timedelta(days=7)
        elif period == 'month':
            start_date = timezone.now() - timezone.timedelta(days=30)
        elif period == 'year':
            start_date = timezone.now() - timezone.timedelta(days=365)
        else:
            start_date = timezone.now() - timezone.timedelta(days=30)
        
        # User statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        new_users = User.objects.filter(date_joined__gte=start_date).count()
        instructors = User.objects.filter(user_type=User.UserType.INSTRUCTOR).count()
        
        # Class statistics
        total_classes = Class.objects.count()
        active_classes = Class.objects.filter(is_active=True).count()
        new_classes = Class.objects.filter(created_at__gte=start_date).count()
        
        # Booking statistics
        total_bookings = Booking.objects.count()
        recent_bookings = Booking.objects.filter(booking_time__gte=start_date).count()
        active_bookings = Booking.objects.filter(status=Booking.Status.BOOKED).count()
        waitlisted_bookings = Booking.objects.filter(status=Booking.Status.WAITLISTED).count()
        
        # Revenue statistics (if pricing is implemented)
        total_revenue = 0
        if Class.objects.filter(price__isnull=False).exists():
            # This would need to be implemented based on actual payment system
            pass
        
        # Popular classes
        popular_classes = (
            Class.objects
            .annotate(booking_count=Count('schedules__bookings'))
            .filter(booking_count__gt=0)
            .order_by('-booking_count')[:10]
            .values('name', 'booking_count', 'instructor__first_name', 'instructor__last_name')
        )
        
        # Popular instructors
        popular_instructors = (
            User.objects
            .filter(user_type=User.UserType.INSTRUCTOR)
            .annotate(class_count=Count('instructed_classes'))
            .filter(class_count__gt=0)
            .order_by('-class_count')[:10]
            .values('first_name', 'last_name', 'class_count')
        )
        
        # Booking trends (daily for the period)
        booking_trends = []
        current_date = start_date.date()
        end_date = timezone.now().date()
        
        while current_date <= end_date:
            daily_bookings = Booking.objects.filter(
                booking_time__date=current_date
            ).count()
            
            booking_trends.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'bookings': daily_bookings
            })
            
            current_date += timezone.timedelta(days=1)
        
        return {
            'period': period,
            'user_statistics': {
                'total_users': total_users,
                'active_users': active_users,
                'new_users': new_users,
                'instructors': instructors
            },
            'class_statistics': {
                'total_classes': total_classes,
                'active_classes': active_classes,
                'new_classes': new_classes
            },
            'booking_statistics': {
                'total_bookings': total_bookings,
                'recent_bookings': recent_bookings,
                'active_bookings': active_bookings,
                'waitlisted_bookings': waitlisted_bookings
            },
            'revenue_statistics': {
                'total_revenue': total_revenue
            },
            'popular_classes': list(popular_classes),
            'popular_instructors': list(popular_instructors),
            'booking_trends': booking_trends
        }

class InstructorDashboardView(generics.ListAPIView):
    """
    API view for instructor dashboard - overview of instructor's classes and statistics.
    Instructor authentication required.
    """
    serializer_class = ClassListSerializer
    permission_classes = [permissions.IsAuthenticated]

    @handle_api_exceptions
    @log_api_request
    def get(self, request, *args, **kwargs):
        """
        Get instructor dashboard data.
        """
        # Check if user is instructor
        if not request.user.is_instructor:
            raise permissions.PermissionDenied("Instructor access required")
        
        # Get instructor's classes
        classes = (
            Class.objects
            .filter(instructor=request.user, is_active=True)
            .select_related('category')
            .prefetch_related('schedules')
            .order_by('-created_at')
        )
        
        # Get dashboard statistics
        stats = self._get_instructor_statistics(request.user)
        
        # Get upcoming classes
        upcoming_classes = (
            ClassSchedule.objects
            .filter(
                class_obj__instructor=request.user,
                start_time__gte=timezone.now(),
                status=ClassSchedule.Status.ACTIVE
            )
            .select_related('class_obj')
            .order_by('start_time')[:10]
        )
        
        response_data = {
            'statistics': stats,
            'classes': ClassListSerializer(classes, many=True).data,
            'upcoming_classes': ClassScheduleSerializer(upcoming_classes, many=True).data
        }
        
        return Response(
            ResponseHandler.success(
                message="Instructor dashboard data retrieved successfully",
                data=response_data
            ),
            status=status.HTTP_200_OK
        )
    
    def _get_instructor_statistics(self, instructor):
        """
        Get instructor-specific statistics.
        """
        from bookings.models import Booking
        
        # Class statistics
        total_classes = Class.objects.filter(instructor=instructor).count()
        active_classes = Class.objects.filter(instructor=instructor, is_active=True).count()
        featured_classes = Class.objects.filter(instructor=instructor, is_featured=True).count()
        
        # Schedule statistics
        total_schedules = ClassSchedule.objects.filter(class_obj__instructor=instructor).count()
        upcoming_schedules = ClassSchedule.objects.filter(
            class_obj__instructor=instructor,
            start_time__gte=timezone.now(),
            status=ClassSchedule.Status.ACTIVE
        ).count()
        
        # Booking statistics
        total_bookings = Booking.objects.filter(class_schedule__class_obj__instructor=instructor).count()
        active_bookings = Booking.objects.filter(
            class_schedule__class_obj__instructor=instructor,
            status=Booking.Status.BOOKED
        ).count()
        completed_bookings = Booking.objects.filter(
            class_schedule__class_obj__instructor=instructor,
            status=Booking.Status.COMPLETED
        ).count()
        
        # Review statistics
        total_reviews = ClassReview.objects.filter(class_schedule__class_obj__instructor=instructor).count()
        avg_rating = ClassReview.objects.filter(
            class_schedule__class_obj__instructor=instructor
        ).aggregate(avg_rating=Avg('rating'))['avg_rating']
        
        return {
            'total_classes': total_classes,
            'active_classes': active_classes,
            'featured_classes': featured_classes,
            'total_schedules': total_schedules,
            'upcoming_schedules': upcoming_schedules,
            'total_bookings': total_bookings,
            'active_bookings': active_bookings,
            'completed_bookings': completed_bookings,
            'total_reviews': total_reviews,
            'average_rating': round(avg_rating, 1) if avg_rating else None
        }

class InstructorClassScheduleView(generics.ListAPIView):
    """
    API view for instructor's class schedules with participant information.
    Instructor authentication required.
    """
    serializer_class = ClassScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    @handle_api_exceptions
    @log_api_request
    def get_queryset(self):
        """
        Get queryset for instructor's class schedules.
        """
        # Check if user is instructor
        if not self.request.user.is_instructor:
            raise permissions.PermissionDenied("Instructor access required")
        
        queryset = (
            ClassSchedule.objects
            .filter(class_obj__instructor=self.request.user)
            .select_related('class_obj')
            .prefetch_related('bookings', 'bookings__user')
        )
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = timezone.datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                queryset = queryset.filter(start_time__gte=start_datetime)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_datetime = timezone.datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc) + timezone.timedelta(days=1)
                queryset = queryset.filter(start_time__lt=end_datetime)
            except ValueError:
                pass
        
        return queryset.order_by('start_time')

    def list(self, request, *args, **kwargs):
        """
        Override list method to include participant information.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        # Add participant information to each schedule
        schedules_with_participants = []
        for schedule, data in zip(queryset, serializer.data):
            participants = self._get_schedule_participants(schedule)
            schedule_data = data.copy()
            schedule_data['participants'] = participants
            schedules_with_participants.append(schedule_data)
        
        return Response(
            ResponseHandler.success(
                message="Instructor schedules retrieved successfully",
                data=schedules_with_participants
            ),
            status=status.HTTP_200_OK
        )
    
    def _get_schedule_participants(self, schedule):
        """
        Get participant information for a specific schedule.
        """
        from bookings.models import Booking
        
        participants = []
        bookings = schedule.bookings.all().select_related('user')
        
        for booking in bookings:
            participant_data = {
                'booking_id': booking.id,
                'user_id': booking.user.id,
                'user_name': booking.user.get_display_name(),
                'user_email': booking.user.email,
                'status': booking.status,
                'is_waitlisted': booking.is_waitlisted,
                'waitlist_position': booking.waitlist_position,
                'booking_time': booking.booking_time,
                'notes': booking.notes
            }
            participants.append(participant_data)
        
        return participants

class InstructorPerformanceView(generics.ListAPIView):
    """
    API view for instructor performance analytics.
    Instructor authentication required.
    """
    permission_classes = [permissions.IsAuthenticated]

    @handle_api_exceptions
    @log_api_request
    def get(self, request, *args, **kwargs):
        """
        Get instructor performance analytics.
        """
        # Check if user is instructor
        if not request.user.is_instructor:
            raise permissions.PermissionDenied("Instructor access required")
        
        # Get performance data
        performance_data = self._get_performance_data(request)
        
        return Response(
            ResponseHandler.success(
                message="Instructor performance data retrieved successfully",
                data=performance_data
            ),
            status=status.HTTP_200_OK
        )
    
    def _get_performance_data(self, request):
        """
        Get instructor performance analytics data.
        """
        from bookings.models import Booking
        
        # Time period filter
        period = request.query_params.get('period', 'month')  # week, month, year
        
        if period == 'week':
            start_date = timezone.now() - timezone.timedelta(days=7)
        elif period == 'month':
            start_date = timezone.now() - timezone.timedelta(days=30)
        elif period == 'year':
            start_date = timezone.now() - timezone.timedelta(days=365)
        else:
            start_date = timezone.now() - timezone.timedelta(days=30)
        
        instructor = request.user
        
        # Class performance
        total_classes_taught = ClassSchedule.objects.filter(
            class_obj__instructor=instructor,
            start_time__gte=start_date,
            status=ClassSchedule.Status.COMPLETED
        ).count()
        
        # Booking performance
        total_bookings = Booking.objects.filter(
            class_schedule__class_obj__instructor=instructor,
            booking_time__gte=start_date
        ).count()
        
        completed_bookings = Booking.objects.filter(
            class_schedule__class_obj__instructor=instructor,
            status=Booking.Status.COMPLETED,
            class_schedule__start_time__gte=start_date
        ).count()
        
        # Attendance rate
        attendance_rate = 0
        if total_bookings > 0:
            attendance_rate = (completed_bookings / total_bookings) * 100
        
        # Review performance
        reviews = ClassReview.objects.filter(
            class_schedule__class_obj__instructor=instructor,
            created_at__gte=start_date
        )
        
        total_reviews = reviews.count()
        avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        
        # Rating distribution
        rating_distribution = {}
        for rating in range(1, 6):
            count = reviews.filter(rating=rating).count()
            rating_distribution[str(rating)] = count
        
        # Popular classes
        popular_classes = (
            Class.objects
            .filter(instructor=instructor)
            .annotate(booking_count=Count('schedules__bookings'))
            .filter(booking_count__gt=0)
            .order_by('-booking_count')[:5]
            .values('name', 'booking_count')
        )
        
        # Monthly trends
        monthly_trends = []
        current_date = start_date.date()
        end_date = timezone.now().date()
        
        while current_date <= end_date:
            month_start = current_date.replace(day=1)
            month_end = (month_start + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)
            
            monthly_bookings = Booking.objects.filter(
                class_schedule__class_obj__instructor=instructor,
                booking_time__date__gte=month_start,
                booking_time__date__lte=month_end
            ).count()
            
            monthly_trends.append({
                'month': month_start.strftime('%Y-%m'),
                'bookings': monthly_bookings
            })
            
            current_date = (month_start + timezone.timedelta(days=32)).replace(day=1)
        
        return {
            'period': period,
            'class_performance': {
                'total_classes_taught': total_classes_taught
            },
            'booking_performance': {
                'total_bookings': total_bookings,
                'completed_bookings': completed_bookings,
                'attendance_rate': round(attendance_rate, 1)
            },
            'review_performance': {
                'total_reviews': total_reviews,
                'average_rating': round(avg_rating, 1) if avg_rating else None,
                'rating_distribution': rating_distribution
            },
            'popular_classes': list(popular_classes),
            'monthly_trends': monthly_trends
        }
