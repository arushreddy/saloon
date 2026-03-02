from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.list_services, name='list-services'),
    path('categories/', views.service_categories, name='service-categories'),
    path('<int:pk>/', views.service_detail, name='service-detail'),

    # Admin
    path('create/', views.create_service, name='create-service'),
    path('<int:pk>/update/', views.update_service, name='update-service'),
    path('<int:pk>/delete/', views.delete_service, name='delete-service'),
]