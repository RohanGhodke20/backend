from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserProfile

# Register your models here.

class UserProfileInline(admin.StackedInline):
    """
    Inline admin for UserProfile model.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fieldsets = (
        ('Fitness Information', {
            'fields': ('experience_level', 'height', 'weight', 'weekly_workout_goal', 'preferred_workout_duration')
        }),
        ('Notification Preferences', {
            'fields': ('email_notifications', 'sms_notifications', 'push_notifications')
        }),
        ('Privacy Settings', {
            'fields': ('profile_visibility',)
        }),
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for User model.
    """
    inlines = (UserProfileInline,)
    list_display = ('email', 'full_name', 'user_type', 'is_active', 'is_verified', 'date_joined', 'last_login')
    list_filter = ('user_type', 'is_active', 'is_verified', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth', 'profile_picture')
        }),
        ('Fitness Information', {
            'fields': ('bio', 'company_name', 'fitness_goals', 'medical_conditions', 'preferred_class_types')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact', 'emergency_contact_name'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type'),
        }),
    )
    
    def get_queryset(self, request):
        """
        Optimize queryset with select_related for profile.
        """
        return super().get_queryset(request).select_related('profile')
    
    def full_name_display(self, obj: User) -> str:
        """
        Display full name with styling.
        """
        if obj.full_name:
            return format_html('<strong>{}</strong>', obj.full_name)
        return format_html('<em>No name provided</em>')
    full_name_display.short_description = 'Full Name'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin for UserProfile model.
    """
    list_display = ('user_email', 'experience_level', 'profile_visibility', 'bmi_display', 'created_at')
    list_filter = ('experience_level', 'profile_visibility', 'email_notifications', 'sms_notifications', 'push_notifications')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'bmi_display', 'bmi_category_display')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Fitness Information', {
            'fields': ('experience_level', 'height', 'weight', 'bmi_display', 'bmi_category_display')
        }),
        ('Fitness Goals', {
            'fields': ('weekly_workout_goal', 'preferred_workout_duration')
        }),
        ('Notification Preferences', {
            'fields': ('email_notifications', 'sms_notifications', 'push_notifications')
        }),
        ('Privacy Settings', {
            'fields': ('profile_visibility',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj: UserProfile) -> str:
        """
        Display user email.
        """
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def bmi_display(self, obj: UserProfile) -> str:
        """
        Display BMI with formatting.
        """
        bmi = obj.get_bmi()
        if bmi:
            return f"{bmi} kg/m²"
        return "Not available"
    bmi_display.short_description = 'BMI'
    
    def bmi_category_display(self, obj: UserProfile) -> str:
        """
        Display BMI category with color coding.
        """
        category = obj.get_bmi_category()
        if category:
            color_map = {
                'underweight': 'orange',
                'normal': 'green',
                'overweight': 'orange',
                'obese': 'red'
            }
            color = color_map.get(category, 'black')
            return format_html('<span style="color: {};">{}</span>', color, category.title())
        return "Not available"
    bmi_category_display.short_description = 'BMI Category'
