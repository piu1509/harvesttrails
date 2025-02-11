from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.DsLoginView.as_view(), name='ds_login'),
    path('callback/', views.DsCallback.as_view(), name='ds_callback'),
    path('must_authenticate/', views.DsMustAuthenticate.as_view(), name='ds_must_authenticate'),
    path('return/', views.DsReturn.as_view(), name='ds_return'),
    path('', views.CoreIndex.as_view(), name='core_index'),
    path('index/', views.CoreRIndex.as_view(), name='core_r_index'),
    path('last_30/', views.DocusignEnvelopeApi.as_view(), name='envelope_status'),
]
