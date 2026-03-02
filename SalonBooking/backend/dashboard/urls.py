from django.urls import path
from . import views

urlpatterns = [
    path('analytics/', views.admin_analytics, name='admin-analytics'),
]