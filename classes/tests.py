"""
Tests for the classes app.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
from users.models import User
from .models import ClassCategory, Class, ClassSchedule
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken


class ClassCategoryModelTest(TestCase):
    """
    Test cases for the ClassCategory model.
    """
    
    def setUp(self):
        """Set up test data."""
        self.category_data = {
            'name': 'Yoga',
            'description': 'Mind and body wellness classes',
            'icon': 'yoga-icon',
            'color': '#FF6B6B',
            'sort_order': 1
        }
    
    def test_create_class_category(self):
        """Test creating a class category."""
        category = ClassCategory.objects.create(**self.category_data)
        self.assertEqual(category.name, self.category_data['name'])
        self.assertEqual(category.description, self.category_data['description'])
        self.assertEqual(category.icon, self.category_data['icon'])
        self.assertEqual(category.color, self.category_data['color'])
        self.assertEqual(category.sort_order, self.category_data['sort_order'])
        self.assertTrue(category.is_active)
    
    def test_class_category_str(self):
        """Test string representation of class category."""
        category = ClassCategory.objects.create(**self.category_data)
        self.assertEqual(str(category), 'Yoga')
    
    def test_class_count_property(self):
        """Test class_count property."""
        category = ClassCategory.objects.create(**self.category_data)
        self.assertEqual(category.class_count, 0)
        
        # Create an instructor
        instructor = User.objects.create_user(
            email='instructor@example.com',
            password='testpass123',
            user_type=User.UserType.INSTRUCTOR
        )
        
        # Create a class in this category
        class_obj = Class.objects.create(
            name='Hatha Yoga',
            description='Traditional yoga practice',
            category=category,
            instructor=instructor,
            duration=60,
            max_capacity=20
        )
        
        self.assertEqual(category.class_count, 1)
        
        # Deactivate the class
        class_obj.is_active = False
        class_obj.save()
        
        self.assertEqual(category.class_count, 0)


class ClassModelTest(TestCase):
    """
    Test cases for the Class model.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create category
        self.category = ClassCategory.objects.create(
            name='Yoga',
            description='Mind and body wellness classes'
        )
        
        # Create instructor
        self.instructor = User.objects.create_user(
            email='instructor@example.com',
            password='testpass123',
            user_type=User.UserType.INSTRUCTOR,
            first_name='John',
            last_name='Doe'
        )
        
        self.class_data = {
            'name': 'Hatha Yoga',
            'description': 'Traditional yoga practice for all levels',
            'category': self.category,
            'instructor': self.instructor,
            'duration': 60,
            'difficulty_level': Class.DifficultyLevel.ALL_LEVELS,
            'max_capacity': 20,
            'location_type': Class.LocationType.IN_PERSON,
            'location_name': 'Main Studio',
            'requirements': 'Yoga mat, comfortable clothing',
            'what_to_expect': 'Gentle stretching and breathing exercises',
            'benefits': 'Improved flexibility and stress relief'
        }
    
    def test_create_class(self):
        """Test creating a class."""
        class_obj = Class.objects.create(**self.class_data)
        self.assertEqual(class_obj.name, self.class_data['name'])
        self.assertEqual(class_obj.description, self.class_data['description'])
        self.assertEqual(class_obj.category, self.category)
        self.assertEqual(class_obj.instructor, self.instructor)
        self.assertEqual(class_obj.duration, 60)
        self.assertEqual(class_obj.difficulty_level, Class.DifficultyLevel.ALL_LEVELS)
        self.assertEqual(class_obj.max_capacity, 20)
        self.assertTrue(class_obj.is_active)
        self.assertFalse(class_obj.is_featured)
    
    def test_class_str(self):
        """Test string representation of class."""
        class_obj = Class.objects.create(**self.class_data)
        expected_str = f"Hatha Yoga - {self.instructor.get_display_name()}"
        self.assertEqual(str(class_obj), expected_str)
    
    def test_class_duration_validation(self):
        """Test duration validation."""
        # Test minimum duration
        with self.assertRaises(ValidationError):
            class_obj = Class(**self.class_data)
            class_obj.duration = 10  # Below minimum
            class_obj.full_clean()
        
        # Test maximum duration
        with self.assertRaises(ValidationError):
            class_obj = Class(**self.class_data)
            class_obj.duration = 400  # Above maximum
            class_obj.full_clean()
    
    def test_class_capacity_validation(self):
        """Test capacity validation."""
        # Test minimum capacity
        with self.assertRaises(ValidationError):
            class_obj = Class(**self.class_data)
            class_obj.max_capacity = 0  # Below minimum
            class_obj.full_clean()
        
        # Test maximum capacity
        with self.assertRaises(ValidationError):
            class_obj = Class(**self.class_data)
            class_obj.max_capacity = 1500  # Above maximum
            class_obj.full_clean()
    
    def test_average_rating_property(self):
        """Test average_rating property."""
        class_obj = Class.objects.create(**self.class_data)
        self.assertIsNone(class_obj.average_rating)
        
        # This will be tested more thoroughly when we implement ClassReview model
        # For now, just ensure it doesn't raise an error
        self.assertIsNone(class_obj.average_rating)
    
    def test_review_count_property(self):
        """Test review_count property."""
        class_obj = Class.objects.create(**self.class_data)
        self.assertEqual(class_obj.review_count, 0)
    
    def test_upcoming_sessions_count_property(self):
        """Test upcoming_sessions_count property."""
        class_obj = Class.objects.create(**self.class_data)
        self.assertEqual(class_obj.upcoming_sessions_count, 0)
        
        # Create an upcoming schedule
        future_time = timezone.now() + timedelta(days=1)
        ClassSchedule.objects.create(
            class_obj=class_obj,
            instructor=self.instructor,
            start_time=future_time,
            end_time=future_time + timedelta(minutes=60),
            max_capacity=20
        )
        
        self.assertEqual(class_obj.upcoming_sessions_count, 1)
    
    def test_get_available_slots(self):
        """Test get_available_slots method."""
        class_obj = Class.objects.create(**self.class_data)
        
        # No schedules yet
        self.assertEqual(class_obj.get_available_slots(), 0)
        
        # Create a schedule
        future_time = timezone.now() + timedelta(days=1)
        schedule = ClassSchedule.objects.create(
            class_obj=class_obj,
            instructor=self.instructor,
            start_time=future_time,
            end_time=future_time + timedelta(minutes=60),
            max_capacity=20,
            booked_slots=5
        )
        
        # Test total available slots
        self.assertEqual(class_obj.get_available_slots(), 15)
        
        # Test specific schedule
        self.assertEqual(class_obj.get_available_slots(schedule.id), 15)


class ClassScheduleModelTest(TestCase):
    """
    Test cases for the ClassSchedule model.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create category
        self.category = ClassCategory.objects.create(
            name='Yoga',
            description='Mind and body wellness classes'
        )
        
        # Create instructor
        self.instructor = User.objects.create_user(
            email='instructor@example.com',
            password='testpass123',
            user_type=User.UserType.INSTRUCTOR,
            first_name='John',
            last_name='Doe'
        )
        
        # Create class
        self.class_obj = Class.objects.create(
            name='Hatha Yoga',
            description='Traditional yoga practice for all levels',
            category=self.category,
            instructor=self.instructor,
            duration=60,
            max_capacity=20
        )
        
        # Create user for booking tests
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
            user_type=User.UserType.USER
        )
        
        self.schedule_data = {
            'class_obj': self.class_obj,
            'instructor': self.instructor,
            'start_time': timezone.now() + timedelta(days=1),
            'end_time': timezone.now() + timedelta(days=1, hours=1),
            'max_capacity': 20,
            'booked_slots': 0,
            'waitlist_enabled': True
        }
    
    def test_create_class_schedule(self):
        """Test creating a class schedule."""
        schedule = ClassSchedule.objects.create(**self.schedule_data)
        self.assertEqual(schedule.class_obj, self.class_obj)
        self.assertEqual(schedule.instructor, self.instructor)
        self.assertEqual(schedule.max_capacity, 20)
        self.assertEqual(schedule.booked_slots, 0)
        self.assertEqual(schedule.status, ClassSchedule.Status.ACTIVE)
        self.assertTrue(schedule.waitlist_enabled)
    
    def test_class_schedule_str(self):
        """Test string representation of class schedule."""
        schedule = ClassSchedule.objects.create(**self.schedule_data)
        expected_str = f"Hatha Yoga - {schedule.start_time.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(schedule), expected_str)
    
    def test_save_method_auto_end_time(self):
        """Test that save method automatically sets end_time."""
        schedule_data = self.schedule_data.copy()
        del schedule_data['end_time']
        
        schedule = ClassSchedule.objects.create(**schedule_data)
        expected_end_time = schedule.start_time + timedelta(minutes=self.class_obj.duration)
        self.assertEqual(schedule.end_time, expected_end_time)
    
    def test_save_method_status_updates(self):
        """Test that save method updates status correctly."""
        schedule = ClassSchedule.objects.create(**self.schedule_data)
        
        # Test full status
        schedule.booked_slots = 20
        schedule.save()
        self.assertEqual(schedule.status, ClassSchedule.Status.FULL)
        
        # Test back to active
        schedule.booked_slots = 15
        schedule.save()
        self.assertEqual(schedule.status, ClassSchedule.Status.ACTIVE)
        
        # Test completed status for past class
        past_time = timezone.now() - timedelta(days=1)
        schedule.start_time = past_time
        schedule.end_time = past_time + timedelta(minutes=60)
        schedule.save()
        self.assertEqual(schedule.status, ClassSchedule.Status.COMPLETED)
    
    def test_available_slots_property(self):
        """Test available_slots property."""
        schedule = ClassSchedule.objects.create(**self.schedule_data)
        self.assertEqual(schedule.available_slots, 20)
        
        schedule.booked_slots = 5
        schedule.save()
        self.assertEqual(schedule.available_slots, 15)
        
        schedule.booked_slots = 20
        schedule.save()
        self.assertEqual(schedule.available_slots, 0)
    
    def test_is_full_property(self):
        """Test is_full property."""
        schedule = ClassSchedule.objects.create(**self.schedule_data)
        self.assertFalse(schedule.is_full)
        
        schedule.booked_slots = 20
        schedule.save()
        self.assertTrue(schedule.is_full)
    
    def test_is_upcoming_property(self):
        """Test is_upcoming property."""
        # Future schedule
        schedule = ClassSchedule.objects.create(**self.schedule_data)
        self.assertTrue(schedule.is_upcoming)
        
        # Past schedule
        past_time = timezone.now() - timedelta(days=1)
        schedule.start_time = past_time
        schedule.end_time = past_time + timedelta(minutes=60)
        schedule.save()
        self.assertFalse(schedule.is_upcoming)
    
    def test_is_past_property(self):
        """Test is_past property."""
        # Future schedule
        schedule = ClassSchedule.objects.create(**self.schedule_data)
        self.assertFalse(schedule.is_past)
        
        # Past schedule
        past_time = timezone.now() - timedelta(days=1)
        schedule.start_time = past_time
        schedule.end_time = past_time + timedelta(minutes=60)
        schedule.save()
        self.assertTrue(schedule.is_past)
    
    def test_duration_minutes_property(self):
        """Test duration_minutes property."""
        schedule = ClassSchedule.objects.create(**self.schedule_data)
        self.assertEqual(schedule.duration_minutes, 60)
    
    def test_can_book_method(self):
        """Test can_book method."""
        schedule = ClassSchedule.objects.create(**self.schedule_data)
        
        # Should be able to book
        self.assertTrue(schedule.can_book(self.user))
        
        # Test full class
        schedule.booked_slots = 20
        schedule.save()
        self.assertFalse(schedule.can_book(self.user))
        
        # Test cancelled class
        schedule.status = ClassSchedule.Status.CANCELLED
        schedule.save()
        self.assertFalse(schedule.can_book(self.user))
        
        # Test past class
        schedule.status = ClassSchedule.Status.ACTIVE
        schedule.start_time = timezone.now() - timedelta(days=1)
        schedule.end_time = timezone.now() - timedelta(days=1, hours=1)
        schedule.save()
        self.assertFalse(schedule.can_book(self.user))
    
    def test_get_waitlist_position(self):
        """Test get_waitlist_position method."""
        schedule = ClassSchedule.objects.create(**self.schedule_data)
        
        # No booking exists
        self.assertIsNone(schedule.get_waitlist_position(self.user))
        
        # This will be tested more thoroughly when we implement Booking model
        # For now, just ensure it doesn't raise an error
        self.assertIsNone(schedule.get_waitlist_position(self.user))


class ClassModelIntegrationTest(TestCase):
    """
    Integration tests for Class models.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create category
        self.category = ClassCategory.objects.create(
            name='Yoga',
            description='Mind and body wellness classes'
        )
        
        # Create instructor
        self.instructor = User.objects.create_user(
            email='instructor@example.com',
            password='testpass123',
            user_type=User.UserType.INSTRUCTOR,
            first_name='John',
            last_name='Doe'
        )
        
        # Create class
        self.class_obj = Class.objects.create(
            name='Hatha Yoga',
            description='Traditional yoga practice for all levels',
            category=self.category,
            instructor=self.instructor,
            duration=60,
            max_capacity=20
        )
    
    def test_class_category_relationship(self):
        """Test relationship between Class and ClassCategory."""
        self.assertEqual(self.class_obj.category, self.category)
        self.assertIn(self.class_obj, self.category.classes.all())
        self.assertEqual(self.category.class_count, 1)
    
    def test_class_instructor_relationship(self):
        """Test relationship between Class and User (instructor)."""
        self.assertEqual(self.class_obj.instructor, self.instructor)
        self.assertIn(self.class_obj, self.instructor.instructed_classes.all())
    
    def test_class_schedule_relationship(self):
        """Test relationship between Class and ClassSchedule."""
        schedule = ClassSchedule.objects.create(
            class_obj=self.class_obj,
            instructor=self.instructor,
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=1),
            max_capacity=20
        )
        
        self.assertEqual(schedule.class_obj, self.class_obj)
        self.assertIn(schedule, self.class_obj.schedules.all())
        self.assertEqual(self.class_obj.upcoming_sessions_count, 1)
    
    def test_recurring_schedule_relationship(self):
        """Test recurring schedule relationships."""
        parent_schedule = ClassSchedule.objects.create(
            class_obj=self.class_obj,
            instructor=self.instructor,
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=1),
            max_capacity=20,
            recurring_type=ClassSchedule.RecurringType.WEEKLY
        )
        
        child_schedule = ClassSchedule.objects.create(
            class_obj=self.class_obj,
            instructor=self.instructor,
            start_time=timezone.now() + timedelta(days=8),
            end_time=timezone.now() + timedelta(days=8, hours=1),
            max_capacity=20,
            parent_schedule=parent_schedule
        )
        
        self.assertEqual(child_schedule.parent_schedule, parent_schedule)
        self.assertIn(child_schedule, parent_schedule.recurring_instances.all())


class ClassCategoryAPITest(APITestCase):
    """
    Test cases for ClassCategory API endpoints.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            user_type=User.UserType.USER
        )
        
        # Create test categories
        self.category1 = ClassCategory.objects.create(
            name='Yoga',
            description='Mind and body wellness classes',
            icon='yoga-icon',
            color='#FF6B6B',
            sort_order=1
        )
        
        self.category2 = ClassCategory.objects.create(
            name='HIIT',
            description='High-intensity interval training',
            icon='hiit-icon',
            color='#4ECDC4',
            sort_order=2
        )
        
        # Create instructor
        self.instructor = User.objects.create_user(
            email='instructor@example.com',
            password='testpass123',
            user_type=User.UserType.INSTRUCTOR,
            first_name='John',
            last_name='Doe'
        )
        
        # Create a class in category1
        self.class_obj = Class.objects.create(
            name='Hatha Yoga',
            description='Traditional yoga practice',
            category=self.category1,
            instructor=self.instructor,
            duration=60,
            max_capacity=20
        )
        
        # Get auth token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_category_list_requires_auth(self):
        """Test that category list requires authentication."""
        self.client.credentials()  # Remove auth
        url = reverse('classes:category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_category_list_success(self):
        """Test successful category list retrieval with custom response format."""
        url = reverse('classes:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check custom response format
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], None)
        self.assertEqual(response.data['message'], 'Class categories retrieved successfully')
        
        # Check data structure
        data = response.data['data']
        self.assertEqual(len(data), 2)  # Two categories
        
        # Check first category
        category1_data = data[0]
        self.assertEqual(category1_data['id'], self.category1.id)
        self.assertEqual(category1_data['name'], 'Yoga')
        self.assertEqual(category1_data['description'], 'Mind and body wellness classes')
        self.assertEqual(category1_data['icon'], 'yoga-icon')
        self.assertEqual(category1_data['color'], '#FF6B6B')
        self.assertEqual(category1_data['class_count'], 1)  # One active class
        
        # Check second category
        category2_data = data[1]
        self.assertEqual(category2_data['id'], self.category2.id)
        self.assertEqual(category2_data['name'], 'HIIT')
        self.assertEqual(category2_data['class_count'], 0)  # No classes
    
    def test_category_detail_requires_auth(self):
        """Test that category detail requires authentication."""
        self.client.credentials()  # Remove auth
        url = reverse('classes:category-detail', kwargs={'id': self.category1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_category_detail_success(self):
        """Test successful category detail retrieval with custom response format."""
        url = reverse('classes:category-detail', kwargs={'id': self.category1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check custom response format
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], None)
        self.assertEqual(response.data['message'], 'Class category retrieved successfully')
        
        # Check data structure
        data = response.data['data']
        self.assertEqual(data['id'], self.category1.id)
        self.assertEqual(data['name'], 'Yoga')
        self.assertEqual(data['description'], 'Mind and body wellness classes')
        self.assertEqual(data['icon'], 'yoga-icon')
        self.assertEqual(data['color'], '#FF6B6B')
        self.assertEqual(data['class_count'], 1)
        
        # Check nested classes
        self.assertIn('classes', data)
        classes = data['classes']
        self.assertEqual(len(classes), 1)
        
        class_data = classes[0]
        self.assertEqual(class_data['id'], self.class_obj.id)
        self.assertEqual(class_data['name'], 'Hatha Yoga')
        self.assertEqual(class_data['instructor_name'], 'John Doe')
    
    def test_category_detail_not_found(self):
        """Test 404 handling for non-existent category with custom response format."""
        url = reverse('classes:category-detail', kwargs={'id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Check custom error response format
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertIn('error', response.data)
        self.assertIsNotNone(response.data['error'])
        self.assertIn('detail', response.data['error'])
        self.assertEqual(response.data['error']['detail'], 'Class category not found')
