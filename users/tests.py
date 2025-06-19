from django.test import TestCase
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import UserRegistrationSerializer, UserDetailSerializer

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
            'user_type': User.UserType.AGENT,
            'company_name': 'Test Company',
            'license_number': 'LIC123456',
            'bio': 'Test bio',
            'website': 'https://test.com'
        }
    
    def test_create_user(self):
        """
        Test creating a new user.
        """
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name']
        )
        
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.first_name, self.user_data['first_name'])
        self.assertEqual(user.last_name, self.user_data['last_name'])
        self.assertTrue(user.check_password(self.user_data['password']))
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
        
        self.assertEqual(superuser.email, 'admin@example.com')
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.check_password('adminpass123'))
    
    def test_user_str_representation(self):
        """
        Test string representation of user.
        """
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(str(user), 'test@example.com')
    
    def test_user_full_name_property(self):
        """
        Test full_name property.
        """
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(user.full_name, 'John Doe')
    
    def test_user_type_properties(self):
        """
        Test user type properties.
        """
        agent = User.objects.create_user(
            email='agent@example.com',
            password='testpass123',
            user_type=User.UserType.AGENT
        )
        investor = User.objects.create_user(
            email='investor@example.com',
            password='testpass123',
            user_type=User.UserType.INVESTOR
        )
        
        self.assertTrue(agent.is_agent)
        self.assertFalse(agent.is_investor)
        self.assertTrue(investor.is_investor)
        self.assertFalse(investor.is_agent)
    
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
            'user_type': User.UserType.AGENT,
            'company_name': 'Test Company',
            'license_number': 'LIC123456',
            'bio': 'Test bio',
            'website': 'https://test.com'
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
        self.assertEqual(data['display_name'], 'John Doe')

class UserViewsTest(APITestCase):
    """
    Test cases for user views.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        self.client = APIClient()
        self.register_url = reverse('user-register')
        self.login_url = reverse('user-login')
        self.profile_url = reverse('user-profile')
        self.change_password_url = reverse('change-password')
        self.user_list_url = reverse('user-list')
        
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '+1234567890',
            'user_type': User.UserType.AGENT,
            'company_name': 'Test Company',
            'license_number': 'LIC123456',
            'bio': 'Test bio',
            'website': 'https://test.com'
        }
        
        # Create a test user
        self.user = User.objects.create_user(
            email='existing@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith'
        )
    
    def test_user_registration_success(self):
        """
        Test successful user registration.
        """
        response = self.client.post(self.register_url, self.user_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'User registered successfully')
        self.assertIn('data', response.data)
        self.assertIn('user_id', response.data['data'])
        self.assertIn('email', response.data['data'])
        
        # Check if user was created in database
        user = User.objects.get(email=self.user_data['email'])
        self.assertEqual(user.first_name, self.user_data['first_name'])
        self.assertEqual(user.last_name, self.user_data['last_name'])
    
    def test_user_registration_invalid_data(self):
        """
        Test user registration with invalid data.
        """
        invalid_data = self.user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        response = self.client.post(self.register_url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Registration failed')
        self.assertIn('error', response.data)
    
    def test_user_login_success(self):
        """
        Test successful user login.
        """
        login_data = {
            'email': 'existing@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Login successful')
        self.assertIn('data', response.data)
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])
        self.assertIn('user', response.data['data'])
    
    def test_user_login_invalid_credentials(self):
        """
        Test user login with invalid credentials.
        """
        login_data = {
            'email': 'existing@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Login failed')
        self.assertIn('error', response.data)
    
    def test_user_profile_get(self):
        """
        Test getting user profile.
        """
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Profile retrieved successfully')
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['email'], self.user.email)
    
    def test_user_profile_update(self):
        """
        Test updating user profile.
        """
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'Updated bio'
        }
        
        response = self.client.put(self.profile_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Profile updated successfully')
        
        # Check if user was updated in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.bio, 'Updated bio')
    
    def test_password_change_success(self):
        """
        Test successful password change.
        """
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        password_data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_new_password': 'newpass123'
        }
        
        response = self.client.post(self.change_password_url, password_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Password changed successfully')
        
        # Check if password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))
    
    def test_password_change_invalid_old_password(self):
        """
        Test password change with invalid old password.
        """
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        password_data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpass123',
            'confirm_new_password': 'newpass123'
        }
        
        response = self.client.post(self.change_password_url, password_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Password change failed')
    
    def test_user_list_authenticated(self):
        """
        Test getting user list when authenticated.
        """
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.get(self.user_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Data retrieved successfully')
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
    
    def test_user_list_unauthenticated(self):
        """
        Test getting user list when not authenticated.
        """
        response = self.client.get(self.user_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

@pytest.mark.django_db
class TestUserModelPytest:
    """
    Pytest-style tests for User model.
    """
    
    def test_create_user_with_email(self):
        """
        Test creating a user with email.
        """
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert user.is_active is True
        assert user.is_staff is False
    
    def test_create_user_without_email_raises_error(self):
        """
        Test creating a user without email raises error.
        """
        with pytest.raises(ValueError, match='The Email field must be set'):
            User.objects.create_user(email='', password='testpass123')
    
    def test_create_superuser(self):
        """
        Test creating a superuser.
        """
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        assert superuser.is_staff is True
        assert superuser.is_superuser is True
        assert superuser.check_password('adminpass123')
