from django.urls import path
from django.contrib.auth.decorators import login_required
from apps.processor4 import views


urlpatterns = [
    path('add_processor4/', views.add_processor4, name='add_processor4'),
    path('list_processor4/', views.processor4_list, name="list_processor4"),
    path('update_processor4/<int:pk>/', views.processor4_update, name='update_processor4'),
    path('processor4_change_password/<int:pk>/', views.processor4_change_password, name='processor4_change_password'),
    path('processor4_delete/<int:pk>/', views.processor4_delete, name='processor4_delete'),
    path('add_processor4_user/<int:pk>/', views.add_processor4_user, name='add_processor4_user'),

    path('inbound_shipment_list_processor4/', views.inbound_shipment_list, name="inbound_shipment_list4"),
    path('inbound_shipment_view_processor4/<int:pk>/', views.inbound_shipment_view, name="inbound_shipment_view4"),
    path('inbound_shipment_edit_processor4/<int:pk>/', views.inbound_shipment_edit, name="inbound_shipment_edit4"),
    path('inbound_shipment_delete_processor4/<int:pk>/', views.inbound_shipment_delete_processor4, name="inbound_shipment_delete_processor4"),
    path('receive_shipment_processor4/', views.receive_shipment, name="receive_shipment4"),

    path('inbound_production_management_processor4/', views.inbound_production_management_processor4, name="inbound_production_management_processor4"),
    path('add_volume_pulled_processor4/', views.add_volume_pulled_processor4, name="add_volume_pulled_processor4"),
    path('edit_volume_pulled_processor4/<int:pk>/', views.edit_volume_pulled_processor4, name="edit_volume_pulled_processor4"),
    path('delete_volume_pulled_processor4/<int:pk>/', views.delete_volume_pulled_processor4, name="delete_volume_pulled_processor4"),

    
    path('rejected_shipments_csv_download_f4/', views.rejected_shipments_csv_download_for_t4, name="rejected_shipments_csv_download_f4"),
    path('all_shipments_csv_download_t4/', views.all_shipments_csv_download_for_t4, name="all_shipments_csv_download_t4"),

    path('addlocation_processor4/', views.addlocation_processor4, name="addlocation_processor4"),
    path('location_list_processor4/', views.location_list_processor4, name="location_list_processor4"),
    path('location_edit_processor4/<int:pk>/', views.location_edit_processor4, name="location_edit_processor4"),
    path('location_delete_processor4/<int:pk>/', views.location_delete_processor4, name="location_delete_processor4"), 

]
