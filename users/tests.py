from django.test import TestCase
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, UserProfile
from .serializers import UserRegistrationSerializer, UserDetailSerializer
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date

User = get_user_model()

class UserModelTest(TestCase):
    """
    Test cases for the User model.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '+1234567890',
            'user_type': User.UserType.USER,
        }
    
    def test_create_user(self):
        """
        Test creating a regular user.
        """
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertEqual(user.user_type, User.UserType.USER)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser(self):
        """
        Test creating a superuser.
        """
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)
    
    def test_user_full_name(self):
        """
        Test the full_name property.
        """
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.full_name, 'John Doe')
        
        # Test with only first name
        user.last_name = ''
        self.assertEqual(user.full_name, 'John')
        
        # Test with only last name
        user.first_name = ''
        user.last_name = 'Doe'
        self.assertEqual(user.full_name, 'Doe')
        
        # Test with no names
        user.first_name = ''
        user.last_name = ''
        self.assertEqual(user.full_name, '')
    
    def test_user_str_representation(self):
        """
        Test string representation of user.
        """
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(str(user), 'test@example.com')
    
    def test_user_type_properties(self):
        """
        Test user type properties.
        """
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.is_instructor)
        self.assertFalse(user.is_admin)
        
        # Test instructor
        user.user_type = User.UserType.INSTRUCTOR
        self.assertTrue(user.is_instructor)
        self.assertFalse(user.is_admin)
        
        # Test admin
        user.user_type = User.UserType.ADMIN
        self.assertFalse(user.is_instructor)
        self.assertTrue(user.is_admin)
    
    def test_user_display_name(self):
        """
        Test get_display_name method.
        """
        user_with_name = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        user_without_name = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        
        self.assertEqual(user_with_name.get_display_name(), 'John Doe')
        self.assertEqual(user_without_name.get_display_name(), 'test2')
    
    def test_user_age_calculation(self):
        """
        Test age calculation.
        """
        user = User.objects.create_user(**self.user_data)
        self.assertIsNone(user.get_age())
        
        # Test with date of birth
        user.date_of_birth = date(1990, 1, 1)
        current_year = timezone.now().year
        expected_age = current_year - 1990
        self.assertEqual(user.get_age(), expected_age)
    
    def test_user_update_last_login(self):
        """
        Test updating last login.
        """
        user = User.objects.create_user(**self.user_data)
        initial_login = user.last_login
        user.update_last_login()
        self.assertIsNotNone(user.last_login)
        self.assertNotEqual(user.last_login, initial_login)


class UserProfileModelTest(TestCase):
    """
    Test cases for the UserProfile model.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
    
    def test_user_profile_creation(self):
        """
        Test that UserProfile is automatically created.
        """
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)
    
    def test_user_profile_defaults(self):
        """
        Test UserProfile default values.
        """
        profile = self.user.profile
        self.assertEqual(profile.experience_level, 'beginner')
        self.assertEqual(profile.weekly_workout_goal, 3)
        self.assertEqual(profile.preferred_workout_duration, 60)
        self.assertTrue(profile.email_notifications)
        self.assertFalse(profile.sms_notifications)
        self.assertTrue(profile.push_notifications)
        self.assertEqual(profile.profile_visibility, 'public')
    
    def test_bmi_calculation(self):
        """
        Test BMI calculation.
        """
        profile = self.user.profile
        
        # Test with no height/weight
        self.assertIsNone(profile.get_bmi())
        
        # Test with height and weight
        profile.height = 170  # 170 cm
        profile.weight = 70   # 70 kg
        expected_bmi = 70 / (1.7 ** 2)  # 24.22
        self.assertAlmostEqual(profile.get_bmi(), expected_bmi, places=2)
    
    def test_bmi_category(self):
        """
        Test BMI category classification.
        """
        profile = self.user.profile
        
        # Test underweight
        profile.height = 170
        profile.weight = 50
        self.assertEqual(profile.get_bmi_category(), 'underweight')
        
        # Test normal
        profile.weight = 70
        self.assertEqual(profile.get_bmi_category(), 'normal')
        
        # Test overweight
        profile.weight = 80
        self.assertEqual(profile.get_bmi_category(), 'overweight')
        
        # Test obese
        profile.weight = 100
        self.assertEqual(profile.get_bmi_category(), 'obese')
    
    def test_user_profile_str(self):
        """
        Test UserProfile string representation.
        """
        profile = self.user.profile
        self.assertEqual(str(profile), f"Profile for {self.user.email}")


class UserSerializerTest(TestCase):
    """
    Test cases for user serializers.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '+1234567890',
            'user_type': User.UserType.USER,
            'company_name': 'Test Gym',
            'bio': 'Fitness enthusiast',
            'fitness_goals': 'Build muscle and improve endurance',
            'preferred_class_types': ['yoga', 'hiit']
        }
    
    def test_user_registration_serializer_valid(self):
        """
        Test valid user registration serializer.
        """
        serializer = UserRegistrationSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())
    
    def test_user_registration_serializer_invalid_password_mismatch(self):
        """
        Test user registration serializer with password mismatch.
        """
        invalid_data = self.user_data.copy()
        invalid_data['confirm_password'] = 'differentpassword'
        serializer = UserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_user_registration_serializer_weak_password(self):
        """
        Test user registration serializer with weak password.
        """
        invalid_data = self.user_data.copy()
        invalid_data['password'] = '123'
        invalid_data['confirm_password'] = '123'
        serializer = UserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
    
    def test_user_detail_serializer(self):
        """
        Test user detail serializer.
        """
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        serializer = UserDetailSerializer(user)
        data = serializer.data
        
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['full_name'], 'John Doe')


class UserViewsTest(APITestCase):
    """
    Test cases for user views.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
    
    def get_tokens_for_user(self, user):
        """
        Get JWT tokens for a user.
        """
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    
    def test_user_registration_success(self):
        """
        Test successful user registration.
        """
        url = reverse('users:register')
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'confirm_password': 'newpass123',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone_number': '+1234567890',
            'user_type': User.UserType.USER,
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)  # Including admin user
    
    def test_user_registration_invalid_data(self):
        """
        Test user registration with invalid data.
        """
        url = reverse('users:register')
        data = {
            'email': 'invalid-email',
            'password': 'short',
            'confirm_password': 'different',
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_login_success(self):
        """
        Test successful user login.
        """
        url = reverse('users:login')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123',
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_user_login_invalid_credentials(self):
        """
        Test user login with invalid credentials.
        """
        url = reverse('users:login')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword',
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_profile_get(self):
        """
        Test getting user profile.
        """
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
    
    def test_user_profile_update(self):
        """
        Test updating user profile.
        """
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        url = reverse('users:profile')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'Updated bio',
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
    
    def test_user_list_authenticated(self):
        """
        Test getting user list when authenticated.
        """
        tokens = self.get_tokens_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        url = reverse('users:user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_user_list_unauthenticated(self):
        """
        Test getting user list when not authenticated.
        """
        url = reverse('users:user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@pytest.mark.django_db
class TestUserModelPytest:
    """
    Pytest-style tests for User model.
    """
    
    def test_create_user_with_email(self):
        """
        Test creating user with email.
        """
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
    
    def test_create_user_without_email_raises_error(self):
        """
        Test creating user without email raises error.
        """
        with pytest.raises(ValueError):
            User.objects.create_user(email='')
    
    def test_create_superuser(self):
        """
        Test creating superuser.
        """
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        assert superuser.is_staff is True
        assert superuser.is_superuser is True
        assert superuser.is_active is True
