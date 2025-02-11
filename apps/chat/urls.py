from django.urls import path
from apps.chat import views

urlpatterns = [
  # path('', views.index, name='index'),
  # path('<str:room_name>/', views.room, name='room'),
  path('chat_ag/', views.chat_ag, name='chat_ag'),
  path('chat_ag/<int:pk>/', views.chatroom_ag, name='chatroom_ag'),
  path('save_msg/<str:user_id>/<str:main_id>/<str:chat_with>/<str:sender>/<str:roomName>/<str:message>/', views.save_msg, name='save_msg'),
  path('get_msg/<str:user_id>/<str:roomName>/<str:chat_with>/<str:get_msg_reciver>/', views.get_msg, name='get_msg'),
  
  path('processor_last_login/<int:pk>/', views.processor_last_login, name='processor_last_login'),
  path('ajax_msg_board/<int:user_id>/', views.ajax_msg_board, name='ajax_msg_board'),
  path('read_msg_status/<str:username>/', views.read_msg_status, name='read_msg_status'),
  
  path('get_msg/<str:user_id>/<str:roomName>/', views.get_msg, name='get_msg'),
  path('notification_chat_msg/<str:user_id>/', views.notification_chat_msg, name='notification_chat_msg'),

]