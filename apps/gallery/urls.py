'''For URL Routing'''
from django.urls import path
from apps.gallery import views




urlpatterns = [
    path('', views.GalleryView.as_view(), name='gallery'),
    path('create/', views.GalleryCreateView.as_view(), name='gallery-create'),
    path('email/',views.EmailSender.as_view(), name="emailsender"),
    path('multiemail/',views.MultiEmailSender.as_view(),name="multiemailsender"),
    path('growerdetails/',views.GrowerDetails.as_view(),name="growerdetails"),
]
