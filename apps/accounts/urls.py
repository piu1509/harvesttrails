from django.urls import path

from apps.accounts import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('user_create/', views.UserCreateView.as_view(), name='user-create'),
    path('account_list/', views.AccountListView.as_view(), name='account-list'),
    path('account/<int:pk>/update/', views.AccountUpdateView.as_view(), name='account-update'),
    path('account/<int:pk>/detail/', views.AccountDetailView.as_view(), name='account-detail'),
    path('account/<int:pk>/delete/', views.AccountDeleteView.as_view(), name='account-delete'),
    path('account/<int:pk>/emailresend/', views.EmailSendView.as_view(), name='email-resend'),
    path('account_create/', views.AccountCreateView.as_view(), name='account-create'),
    path('account_user/', views.account_user, name='account_user'),
    path('add_consultant/', views.ConsultantCreateView.as_view(), name='add-consultant'),
    path('user/', views.UserListView.as_view(), name='user-list'),
    path('user/<int:pk>/update/', views.UserUpdateView.as_view(), name='user-update'),
    path('user/<int:pk>/detail/', views.UserDetailView.as_view(), name='user-detail'),
    path('user/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user-delete'),
    path('role/create/', views.RoleCreateView.as_view(), name='role-create'),
    path('role/', views.RoleListView.as_view(), name='role-list'),
    path('role/<int:pk>/update/', views.RoleUpdateView.as_view(), name='role-update'),
    path('role/<int:pk>/delete/', views.RoleDeleteView.as_view(), name='role-delete'),
    path('super_account_create/', views.SuperAccountCreateView.as_view(), name='super-account-create'),
    #code
    path('change_password/', views.change_password, name='change_password'),
    path('user_change_password/<int:pk>', views.user_change_password, name='user_change_password'),
    path('show_notification_counter/', views.show_notification_counter, name='show_notification_counter'),
    path('show_notification/', views.show_notification, name='show_notification'),
    # 12-04-23
    path('show_log/', views.show_log, name='show_log'),
    # 16-06-23 
    path('grower_sign_up/', views.grower_sign_up, name='grower_sign_up'),
    path('userstate_change/', views.userstate_change, name='userstate_change'),

    path('version_update/', views.version_update, name='version_update'),
    path('version_update_list/', views.version_update_list, name='version_update_list'),
    
]
