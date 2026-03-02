from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('slots/', views.get_available_slots, name='available-slots'),
    path('dates/', views.get_available_dates, name='available-dates'),

    # User
    path('create/', views.create_booking, name='create-booking'),
    path('my/', views.my_bookings, name='my-bookings'),
    path('<str:booking_id>/cancel/', views.cancel_booking, name='cancel-booking'),

    # Admin
    path('admin/all/', views.admin_all_bookings, name='admin-all-bookings'),
    path('admin/slot/', views.admin_update_slot, name='admin-update-slot'),
    path('admin/<str:booking_id>/status/', views.admin_update_booking_status, name='admin-update-status'),
]