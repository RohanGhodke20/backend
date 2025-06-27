"""
URL configuration for bookings app.
"""
from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # User Bookings
    path('my-bookings/', views.UserBookingListView.as_view(), name='user-bookings'),
    path('my-bookings/<int:pk>/', views.UserBookingDetailView.as_view(), name='user-booking-detail'),
    path('my-bookings/<int:pk>/update/', views.BookingUpdateView.as_view(), name='booking-update'),
    path('my-bookings/<int:pk>/cancel/', views.BookingCancelView.as_view(), name='booking-cancel'),
    
    # Booking Creation
    path('create/', views.BookingCreateView.as_view(), name='booking-create'),
    
    # Class Schedule Booking Info
    path('schedule/<int:schedule_id>/', views.ClassScheduleBookingView.as_view(), name='schedule-booking'),
    
    # Reviews
    path('reviews/create/', views.ClassReviewCreateView.as_view(), name='review-create'),
    path('reviews/my-reviews/', views.UserReviewListView.as_view(), name='user-reviews'),
    path('reviews/class/<int:class_id>/', views.ClassReviewListView.as_view(), name='class-reviews'),
] 