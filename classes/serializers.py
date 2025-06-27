"""
Serializers for the classes app.
"""
from typing import Dict, Any, Optional, List
from rest_framework import serializers
from .models import ClassCategory, Class, ClassSchedule
from users.models import User

# Serializers will be added as we implement the models 

class ClassListInCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for listing classes within a category (for category detail endpoint).
    """
    instructor_name = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = [
            'id', 'name', 'description', 'instructor_name', 'duration',
            'difficulty_level', 'max_capacity', 'location_type', 'is_active', 'image'
        ]

    def get_instructor_name(self, obj: Class) -> str:
        """
        Get the instructor's display name.
        """
        return obj.instructor.get_display_name()

class ClassCategoryListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing class categories with class count.
    """
    class_count = serializers.SerializerMethodField()

    class Meta:
        model = ClassCategory
        fields = ['id', 'name', 'description', 'icon', 'color', 'class_count']

    def get_class_count(self, obj: ClassCategory) -> int:
        return getattr(obj, 'annotated_class_count', obj.class_count)

class ClassCategoryDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for class category detail with nested class list.
    """
    classes = ClassListInCategorySerializer(many=True, read_only=True)
    class_count = serializers.SerializerMethodField()

    class Meta:
        model = ClassCategory
        fields = [
            'id', 'name', 'description', 'icon', 'color', 'class_count', 'classes'
        ]

    def get_class_count(self, obj: ClassCategory) -> int:
        return getattr(obj, 'annotated_class_count', obj.class_count)

class InstructorSerializer(serializers.ModelSerializer):
    """
    Serializer for instructor information in class details.
    """
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'display_name', 'profile_picture', 'bio', 'company_name']
    
    def get_display_name(self, obj: User) -> str:
        return obj.get_display_name()

class ClassScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for class schedules.
    """
    available_slots = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    
    class Meta:
        model = ClassSchedule
        fields = [
            'id', 'start_time', 'end_time', 'max_capacity', 'booked_slots',
            'available_slots', 'is_full', 'is_upcoming', 'status', 'notes'
        ]
    
    def get_available_slots(self, obj: ClassSchedule) -> int:
        return obj.available_slots
    
    def get_is_full(self, obj: ClassSchedule) -> bool:
        return obj.is_full
    
    def get_is_upcoming(self, obj: ClassSchedule) -> bool:
        return obj.is_upcoming

class ClassListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing classes with basic information.
    """
    instructor_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    upcoming_sessions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = [
            'id', 'name', 'description', 'instructor_name', 'category_name',
            'duration', 'difficulty_level', 'max_capacity', 'location_type',
            'location_name', 'price', 'currency', 'is_active', 'is_featured',
            'image', 'average_rating', 'review_count', 'upcoming_sessions_count'
        ]
    
    def get_instructor_name(self, obj: Class) -> str:
        return obj.instructor.get_display_name()
    
    def get_category_name(self, obj: Class) -> str:
        return obj.category.name
    
    def get_average_rating(self, obj: Class) -> Optional[float]:
        return obj.average_rating
    
    def get_review_count(self, obj: Class) -> int:
        return obj.review_count
    
    def get_upcoming_sessions_count(self, obj: Class) -> int:
        return obj.upcoming_sessions_count

class ClassDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed class information.
    """
    instructor = InstructorSerializer(read_only=True)
    category = ClassCategoryListSerializer(read_only=True)
    schedules = ClassScheduleSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    upcoming_sessions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = [
            'id', 'name', 'description', 'instructor', 'category', 'duration',
            'difficulty_level', 'max_capacity', 'location_type', 'location_name',
            'location_address', 'requirements', 'what_to_expect', 'benefits',
            'price', 'currency', 'is_active', 'is_featured', 'image', 'video_url',
            'average_rating', 'review_count', 'upcoming_sessions_count', 'schedules',
            'created_at', 'updated_at'
        ]
    
    def get_average_rating(self, obj: Class) -> Optional[float]:
        return obj.average_rating
    
    def get_review_count(self, obj: Class) -> int:
        return obj.review_count
    
    def get_upcoming_sessions_count(self, obj: Class) -> int:
        return obj.upcoming_sessions_count

class ClassSearchSerializer(serializers.ModelSerializer):
    """
    Serializer for class search results with minimal information.
    """
    instructor_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = [
            'id', 'name', 'description', 'instructor_name', 'category_name',
            'duration', 'difficulty_level', 'location_type', 'price',
            'is_featured', 'image', 'average_rating'
        ]
    
    def get_instructor_name(self, obj: Class) -> str:
        return obj.instructor.get_display_name()
    
    def get_category_name(self, obj: Class) -> str:
        return obj.category.name
    
    def get_average_rating(self, obj: Class) -> Optional[float]:
        return obj.average_rating 