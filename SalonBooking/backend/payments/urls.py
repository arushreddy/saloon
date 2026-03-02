from django.urls import path
from . import views

urlpatterns = [
    path('create-order/', views.create_order, name='create-order'),
    path('verify/', views.verify_payment, name='verify-payment'),
    path('status/<str:booking_id>/', views.payment_status, name='payment-status'),
    path('admin/all/', views.admin_all_payments, name='admin-all-payments'),
]