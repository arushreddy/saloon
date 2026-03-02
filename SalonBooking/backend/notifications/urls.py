from django.urls import path
from . import views

urlpatterns = [
    path('test-whatsapp/', views.test_whatsapp, name='test-whatsapp'),
]