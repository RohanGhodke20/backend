"""
Serializers for the bookings app.
"""
from typing import Dict, Any, Optional
from rest_framework import serializers
from django.utils import timezone
from .models import Booking, ClassReview
from classes.models import Class, ClassSchedule
from users.models import User

class ClassScheduleBookingSerializer(serializers.ModelSerializer):
    """
    Serializer for class schedule information in booking context.
    """
    class_name = serializers.SerializerMethodField()
    instructor_name = serializers.SerializerMethodField()
    available_slots = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    
    class Meta:
        model = ClassSchedule
        fields = [
            'id', 'start_time', 'end_time', 'max_capacity', 'booked_slots',
            'available_slots', 'is_full', 'class_name', 'instructor_name', 'status'
        ]
    
    def get_class_name(self, obj: ClassSchedule) -> str:
        return obj.class_obj.name
    
    def get_instructor_name(self, obj: ClassSchedule) -> str:
        return obj.instructor.get_display_name()
    
    def get_available_slots(self, obj: ClassSchedule) -> int:
        return obj.available_slots
    
    def get_is_full(self, obj: ClassSchedule) -> bool:
        return obj.is_full

class BookingListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing user bookings with basic information.
    """
    class_name = serializers.SerializerMethodField()
    instructor_name = serializers.SerializerMethodField()
    schedule_info = ClassScheduleBookingSerializer(source='class_schedule', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'status', 'booking_time', 'cancellation_time', 'is_waitlisted',
            'waitlist_position', 'class_name', 'instructor_name', 'schedule_info'
        ]
    
    def get_class_name(self, obj: Booking) -> str:
        return obj.class_schedule.class_obj.name
    
    def get_instructor_name(self, obj: Booking) -> str:
        return obj.class_schedule.instructor.get_display_name()

class BookingDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed booking information.
    """
    class_info = serializers.SerializerMethodField()
    schedule_info = ClassScheduleBookingSerializer(source='class_schedule', read_only=True)
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'status', 'booking_time', 'cancellation_time', 'is_waitlisted',
            'waitlist_position', 'notes', 'class_info', 'schedule_info', 'user_info',
            'created_at', 'updated_at'
        ]
    
    def get_class_info(self, obj: Booking) -> Dict[str, Any]:
        class_obj = obj.class_schedule.class_obj
        return {
            'id': class_obj.id,
            'name': class_obj.name,
            'description': class_obj.description,
            'duration': class_obj.duration,
            'difficulty_level': class_obj.difficulty_level,
            'location_type': class_obj.location_type,
            'location_name': class_obj.location_name,
            'requirements': class_obj.requirements,
            'image': class_obj.image
        }
    
    def get_user_info(self, obj: Booking) -> Dict[str, Any]:
        return {
            'id': obj.user.id,
            'email': obj.user.email,
            'full_name': obj.user.full_name
        }

class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new bookings.
    """
    class Meta:
        model = Booking
        fields = ['class_schedule', 'notes']
    
    def validate_class_schedule(self, value: ClassSchedule) -> ClassSchedule:
        """
        Validate that the class schedule is available for booking.
        """
        # Check if schedule is active
        if value.status != ClassSchedule.Status.ACTIVE:
            raise serializers.ValidationError("This class session is not available for booking.")
        
        # Check if schedule is in the future
        if value.start_time <= timezone.now():
            raise serializers.ValidationError("Cannot book past class sessions.")
        
        # Check if user already has a booking for this schedule
        user = self.context['request'].user
        if Booking.objects.filter(user=user, class_schedule=value).exists():
            raise serializers.ValidationError("You already have a booking for this class session.")
        
        return value
    
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Additional validation for booking creation.
        """
        class_schedule = attrs['class_schedule']
        user = self.context['request'].user
        
        # Check if class is full
        if class_schedule.is_full:
            # Check if waitlist is enabled
            if class_schedule.waitlist_enabled:
                attrs['is_waitlisted'] = True
                attrs['status'] = Booking.Status.WAITLISTED
                # Calculate waitlist position
                waitlist_count = Booking.objects.filter(
                    class_schedule=class_schedule,
                    is_waitlisted=True
                ).count()
                attrs['waitlist_position'] = waitlist_count + 1
            else:
                raise serializers.ValidationError("This class session is full and waitlist is not enabled.")
        
        return attrs
    
    def create(self, validated_data: Dict[str, Any]) -> Booking:
        """
        Create booking and update class schedule booked slots.
        """
        user = self.context['request'].user
        class_schedule = validated_data['class_schedule']
        
        # Create the booking
        booking = Booking.objects.create(
            user=user,
            **validated_data
        )
        
        # Update class schedule booked slots if not waitlisted
        if not booking.is_waitlisted:
            class_schedule.booked_slots += 1
            class_schedule.save(update_fields=['booked_slots'])
        
        return booking

class BookingUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating booking information.
    """
    class Meta:
        model = Booking
        fields = ['notes']
    
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate booking update.
        """
        booking = self.instance
        
        # Check if booking can be updated
        if booking.status == Booking.Status.CANCELLED:
            raise serializers.ValidationError("Cannot update a cancelled booking.")
        
        if booking.status == Booking.Status.COMPLETED:
            raise serializers.ValidationError("Cannot update a completed booking.")
        
        return attrs

class BookingCancelSerializer(serializers.ModelSerializer):
    """
    Serializer for cancelling bookings.
    """
    cancellation_reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    class Meta:
        model = Booking
        fields = ['cancellation_reason']
    
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate booking cancellation.
        """
        booking = self.instance
        
        # Check if booking can be cancelled
        if booking.status == Booking.Status.CANCELLED:
            raise serializers.ValidationError("Booking is already cancelled.")
        
        if booking.status == Booking.Status.COMPLETED:
            raise serializers.ValidationError("Cannot cancel a completed booking.")
        
        # Check cancellation policy (e.g., must be cancelled 24 hours before class)
        class_schedule = booking.class_schedule
        cancellation_deadline = class_schedule.start_time - timezone.timedelta(hours=24)
        
        if timezone.now() > cancellation_deadline:
            raise serializers.ValidationError(
                "Bookings must be cancelled at least 24 hours before the class starts."
            )
        
        return attrs
    
    def update(self, instance: Booking, validated_data: Dict[str, Any]) -> Booking:
        """
        Cancel the booking and update related data.
        """
        cancellation_reason = validated_data.get('cancellation_reason', '')
        
        # Cancel the booking
        instance.cancel(reason=cancellation_reason)
        
        # Update class schedule booked slots if not waitlisted
        if not instance.is_waitlisted:
            class_schedule = instance.class_schedule
            class_schedule.booked_slots = max(0, class_schedule.booked_slots - 1)
            class_schedule.save(update_fields=['booked_slots'])
        
        return instance

class ClassReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for class reviews and ratings.
    """
    user_name = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ClassReview
        fields = [
            'id', 'rating', 'review', 'user_name', 'class_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user_name', 'class_name', 'created_at', 'updated_at']
    
    def get_user_name(self, obj: ClassReview) -> str:
        return obj.user.get_display_name()
    
    def get_class_name(self, obj: ClassReview) -> str:
        return obj.class_obj.name
    
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate review creation.
        """
        user = self.context['request'].user
        class_schedule = attrs['class_schedule']
        
        # Check if user has attended this class
        booking = Booking.objects.filter(
            user=user,
            class_schedule=class_schedule,
            status=Booking.Status.COMPLETED
        ).first()
        
        if not booking:
            raise serializers.ValidationError(
                "You can only review classes you have attended."
            )
        
        # Check if user already reviewed this class
        if ClassReview.objects.filter(
            user=user,
            class_schedule=class_schedule
        ).exists():
            raise serializers.ValidationError(
                "You have already reviewed this class session."
            )
        
        return attrs
    
    def create(self, validated_data: Dict[str, Any]) -> ClassReview:
        """
        Create review and set class_obj automatically.
        """
        class_schedule = validated_data['class_schedule']
        validated_data['class_obj'] = class_schedule.class_obj
        
        return super().create(validated_data)

class ClassReviewListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing class reviews.
    """
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ClassReview
        fields = ['id', 'rating', 'review', 'user_name', 'created_at']
    
    def get_user_name(self, obj: ClassReview) -> str:
        return obj.user.get_display_name() 