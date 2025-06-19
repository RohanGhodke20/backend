from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new user with email and password.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'confirm_password', 'first_name', 'last_name', 
                 'phone_number', 'user_type', 'company_name', 'license_number', 'bio', 'website')

    def validate(self, attrs):
        """
        Validate that passwords match and meet requirements.
        """
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate password strength
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({'password': e.messages})
        
        return attrs

    def create(self, validated_data):
        """
        Create and return a new user using the validated data.
        """
        validated_data.pop('confirm_password', None)
        user = User.objects.create_user(**validated_data)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile updates.
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number', 'company_name', 
                 'license_number', 'bio', 'website', 'profile_picture')
        read_only_fields = ('email', 'user_type', 'is_verified')

    def update(self, instance, validated_data):
        """
        Update user profile information.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed user information (read-only).
    """
    full_name = serializers.CharField(read_only=True)
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'full_name', 'display_name',
                 'phone_number', 'user_type', 'is_verified', 'date_joined', 'last_login',
                 'company_name', 'license_number', 'bio', 'website', 'profile_picture')
        read_only_fields = fields

    def get_display_name(self, obj):
        return obj.display_name

class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change functionality.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, attrs):
        """
        Validate password change data.
        """
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError("New passwords don't match")
        
        # Validate new password strength
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})
        
        return attrs

    def validate_old_password(self, value):
        """
        Validate that the old password is correct.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value

class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users (minimal information).
    """
    full_name = serializers.CharField(read_only=True)
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'display_name', 'user_type', 'is_verified', 'date_joined')
        read_only_fields = fields

    def get_display_name(self, obj):
        return obj.display_name 