"""
URL configuration for classes app.
"""
from django.urls import path
from . import views

app_name = 'classes'

urlpatterns = [
    # Class Categories
    path('categories/', views.ClassCategoryListView.as_view(), name='category-list'),
    path('categories/<int:id>/', views.ClassCategoryDetailView.as_view(), name='category-detail'),
    
    # Classes
    path('', views.ClassListView.as_view(), name='class-list'),
    path('<int:id>/', views.ClassDetailView.as_view(), name='class-detail'),
    path('search/', views.ClassSearchView.as_view(), name='class-search'),
    path('calendar/', views.ClassCalendarView.as_view(), name='class-calendar'),
    
    # Instructor Classes
    path('instructor/<int:instructor_id>/', views.InstructorClassListView.as_view(), name='instructor-classes'),
    
    # Admin Dashboard
    path('admin/classes/', views.AdminClassManagementView.as_view(), name='admin-classes'),
    path('admin/classes/<int:id>/', views.AdminClassDetailView.as_view(), name='admin-class-detail'),
    path('admin/categories/', views.AdminCategoryManagementView.as_view(), name='admin-categories'),
    path('admin/analytics/', views.AdminAnalyticsView.as_view(), name='admin-analytics'),
    
    # Instructor Dashboard
    path('instructor/dashboard/', views.InstructorDashboardView.as_view(), name='instructor-dashboard'),
    path('instructor/schedules/', views.InstructorClassScheduleView.as_view(), name='instructor-schedules'),
    path('instructor/performance/', views.InstructorPerformanceView.as_view(), name='instructor-performance'),
] 