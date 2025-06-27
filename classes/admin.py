from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ClassCategory, Class, ClassSchedule


@admin.register(ClassCategory)
class ClassCategoryAdmin(admin.ModelAdmin):
    """
    Admin for ClassCategory model.
    """
    list_display = ('name', 'class_count', 'is_active', 'sort_order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('sort_order', 'name')
    list_editable = ('is_active', 'sort_order')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Display Settings', {
            'fields': ('icon', 'color', 'sort_order')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'class_count')
    
    def class_count(self, obj: ClassCategory) -> int:
        """
        Display the number of classes in this category.
        """
        return obj.class_count
    class_count.short_description = 'Classes'


class ClassScheduleInline(admin.TabularInline):
    """
    Inline admin for ClassSchedule model.
    """
    model = ClassSchedule
    extra = 0
    readonly_fields = ('booked_slots', 'available_slots', 'status')
    fields = ('start_time', 'end_time', 'max_capacity', 'booked_slots', 'available_slots', 'status', 'instructor')
    
    def available_slots(self, obj: ClassSchedule) -> int:
        """
        Display available slots.
        """
        return obj.available_slots
    available_slots.short_description = 'Available'


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    """
    Admin for Class model.
    """
    inlines = [ClassScheduleInline]
    list_display = ('name', 'category', 'instructor', 'difficulty_level', 'duration', 'max_capacity', 'is_active', 'is_featured', 'upcoming_sessions_count')
    list_filter = ('category', 'difficulty_level', 'location_type', 'is_active', 'is_featured', 'created_at')
    search_fields = ('name', 'description', 'instructor__email', 'instructor__first_name', 'instructor__last_name')
    ordering = ('-is_featured', '-created_at')
    list_editable = ('is_active', 'is_featured')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'instructor')
        }),
        ('Class Details', {
            'fields': ('duration', 'difficulty_level', 'max_capacity')
        }),
        ('Location', {
            'fields': ('location_type', 'location_name', 'location_address')
        }),
        ('Requirements & Information', {
            'fields': ('requirements', 'what_to_expect', 'benefits'),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('price', 'currency'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('image', 'video_url'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'upcoming_sessions_count', 'average_rating_display', 'review_count')
    
    def upcoming_sessions_count(self, obj: Class) -> int:
        """
        Display the number of upcoming sessions.
        """
        return obj.upcoming_sessions_count
    upcoming_sessions_count.short_description = 'Upcoming Sessions'
    
    def average_rating_display(self, obj: Class) -> str:
        """
        Display average rating with stars.
        """
        rating = obj.average_rating
        if rating:
            stars = '★' * int(rating) + '☆' * (5 - int(rating))
            return format_html('<span style="color: gold;">{} ({})</span>', stars, rating)
        return 'No ratings'
    average_rating_display.short_description = 'Average Rating'
    
    def review_count(self, obj: Class) -> int:
        """
        Display the number of reviews.
        """
        return obj.review_count
    review_count.short_description = 'Reviews'
    
    def get_queryset(self, request):
        """
        Optimize queryset with select_related and prefetch_related.
        """
        return super().get_queryset(request).select_related('category', 'instructor').prefetch_related('schedules')


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    """
    Admin for ClassSchedule model.
    """
    list_display = ('class_name', 'instructor', 'start_time', 'end_time', 'capacity_display', 'status', 'recurring_type')
    list_filter = ('status', 'recurring_type', 'start_time', 'created_at')
    search_fields = ('class_obj__name', 'instructor__email', 'instructor__first_name', 'instructor__last_name')
    ordering = ('-start_time',)
    list_editable = ('status',)
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Class Information', {
            'fields': ('class_obj', 'instructor')
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time', 'duration_minutes_display')
        }),
        ('Capacity & Booking', {
            'fields': ('max_capacity', 'booked_slots', 'available_slots_display', 'waitlist_enabled')
        }),
        ('Recurring Schedule', {
            'fields': ('recurring_type', 'recurring_end_date', 'parent_schedule'),
            'classes': ('collapse',)
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes', 'cancellation_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'duration_minutes_display', 'available_slots_display')
    
    def class_name(self, obj: ClassSchedule) -> str:
        """
        Display class name with link.
        """
        url = reverse('admin:classes_class_change', args=[obj.class_obj.id])
        return format_html('<a href="{}">{}</a>', url, obj.class_obj.name)
    class_name.short_description = 'Class'
    class_name.admin_order_field = 'class_obj__name'
    
    def capacity_display(self, obj: ClassSchedule) -> str:
        """
        Display capacity information.
        """
        if obj.is_full:
            return format_html('<span style="color: red;">{}/{} (Full)</span>', obj.booked_slots, obj.max_capacity)
        return f"{obj.booked_slots}/{obj.max_capacity}"
    capacity_display.short_description = 'Capacity'
    
    def available_slots_display(self, obj: ClassSchedule) -> int:
        """
        Display available slots.
        """
        return obj.available_slots
    available_slots_display.short_description = 'Available Slots'
    
    def duration_minutes_display(self, obj: ClassSchedule) -> int:
        """
        Display duration in minutes.
        """
        return obj.duration_minutes
    duration_minutes_display.short_description = 'Duration (minutes)'
    
    def get_queryset(self, request):
        """
        Optimize queryset with select_related.
        """
        return super().get_queryset(request).select_related('class_obj', 'instructor', 'parent_schedule')
    
    def get_list_display(self, request):
        """
        Add location type to list display if needed.
        """
        list_display = list(super().get_list_display(request))
        if 'location_type' not in list_display:
            list_display.insert(-1, 'location_type')
        return list_display
    
    def location_type(self, obj: ClassSchedule) -> str:
        """
        Display location type.
        """
        return obj.class_obj.location_type
    location_type.short_description = 'Location Type'
    location_type.admin_order_field = 'class_obj__location_type'
