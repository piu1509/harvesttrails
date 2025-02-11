from django.urls import path
from apps.assistantapp import views


urlpatterns = [
    path('helpapi/', views.helpapi, name='helpapi'),
    path('digital_crop_consultant/', views.digital_crop_consultant, name='digital_crop_consultant'),
    path('digital_crop_consultant_chatgpt/', views.digital_crop_consultant_chatgpt, name='digital_crop_consultant_chatgpt'),
    
    path('weather_section_outline/', views.weather_section_outline, name='weather_section_outline'),
]