from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth import views as auth_views

from .api_urls import router
from apps.accounts.forms import LoginForm
# from apps.accounts.views import AccountLoginView
from apps.accounts.views import *


# handler404_account = 'apps.accounts.views.handler404_account'
# handler500_account = 'apps.accounts.views.handler500_account'
# handler404 = 'apps.growerpayments.views.error404_payment'
# handler500 = 'apps.growerpayments.views.error500_payment'


urlpatterns = [
    path('privacy/', privacy, name='privacy'),
    path('terms/', terms_and_conditions, name='terms_and_conditions'),
    path('', main_page, name='main_page'),
    
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('login/', AccountLoginView.as_view(
        redirect_authenticated_user=True,
        template_name='registration/login.html',
        authentication_form=LoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset.html',
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/passowrd_reset_email_format.html',
             success_url='/password-reset/done/'
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),

    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    path('accounts/', include('apps.accounts.urls')),
    path('farms/', include('apps.farms.urls')),
    path('field/', include('apps.field.urls')),
    path('gallery/', include('apps.gallery.urls')),
    path('grower/',include('apps.grower.urls')),
    path('survey/', include('apps.survey.urls')),
    path('growersurvey/', include('apps.growersurvey.urls')),
    path('notesandupdate/', include('apps.notesandupdate.urls')),
    path('documents/', include('apps.documents.urls')),
    path('contracts/', include('apps.contracts.urls')),
    # sdp
    path('storage/', include('apps.storage.urls')),
    path('processor/', include('apps.processor.urls')),
    path('chat/', include('apps.chat.urls')),
    path('farmsmart/', include('apps.farmsmart.urls')),
    path('growerpayments/', include('apps.growerpayments.urls')),
    path('processor2/', include('apps.processor2.urls')),
    path('processor3/', include('apps.processor3.urls')),
    path('processor4/', include('apps.processor4.urls')),
    path('assistantapp/', include('apps.assistantapp.urls')),
    path('tracemodule/', include('apps.tracemodule.urls')),
    path('warehouse/', include('apps.warehouseManagement.urls')),
    path('quickbooks/', include('apps.quickbooks_integration.urls')),  

    path("select2/", include("django_select2.urls")),  
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


admin.site.site_header = 'Agreeta Solutions (AgFarm Admin Panel)'
