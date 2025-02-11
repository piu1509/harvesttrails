from django.urls import path
from django.contrib.auth.decorators import login_required
from apps.processor3 import views

urlpatterns = [
    path('list_processor3/', views.processor3_list, name='list_processor3'),
    path('add_processor3/', views.add_processor3, name='add_processor3'),
    path('update_processor3/<int:pk>/', views.processor3_update, name='update_processor3'),
    path('processor3_change_password/<int:pk>/', views.processor3_change_password, name='processor3_change_password'),
    path('processor3_delete/<int:pk>/', views.processor3_delete, name='processor3_delete'),
    path('add_processor3_user/<int:pk>/', views.add_processor3_user, name='add_processor3_user'),
    
    path('inbound_shipment_list/', views.inbound_shipment_list, name="inbound_shipment_list3"),
    path('inbound_shipment_view/<int:pk>/', views.inbound_shipment_view, name="inbound_shipment_view3"),
    path('inbound_shipment_edit/<int:pk>/', views.inbound_shipment_edit, name="inbound_shipment_edit3"),
    path('inbound_shipment_delete_processor3/<int:pk>/', views.inbound_shipment_delete_processor3, name="inbound_shipment_delete_processor3"),
    path('receive_shipment/', views.receive_shipment, name="receive_shipment3"),
    path('rejected_shipments_csv_download_for_t3/', views.rejected_shipments_csv_download_for_t3, name="rejected_shipments_csv_download_for_t3"),
    path('all_shipments_csv_download_for_t3/', views.all_shipments_csv_download_for_t3, name="all_shipments_csv_download_for_t3"),

    path('add_outbound_shipment_processor3/', views.add_outbound_shipment_processor3, name="add_outbound_shipment_processor3"),
    path('outbound_shipment_list_processor3/', views.outbound_shipment_list_processor3, name="outbound_shipment_list_processor3"),
    path('outbound_shipment_view_processor3/<int:pk>/', views.outbound_shipment_view_processor3, name="outbound_shipment_view_processor3"),
    path('outbound_shipment_delete_processor3/<int:pk>/', views.outbound_shipment_delete_processor3, name="outbound_shipment_delete_processor3"),
    path('outbound_shipment_processor3_csv_download/', views.outbound_shipment_processor3_csv_download, name='outbound_shipment_processor3_csv_download'),

    path('processor3_processor_management/', views.processor3_processor_management, name="processor3_processor_management"),
    path('link_processor_three/', views.link_processor_three, name="link_processor_three"),
    path('delete_link_processor_three/<int:pk>/', views.delete_link_processor_three, name="delete_link_processor_three"),

    path('inbound_production_management_processor3/', views.inbound_production_management_processor3, name="inbound_production_management_processor3"),
    path('add_volume_pulled_processor3/', views.add_volume_pulled_processor3, name="add_volume_pulled_processor3"),
    path('edit_volume_pulled_processor3/<int:pk>/', views.edit_volume_pulled_processor3, name="edit_volume_pulled_processor3"),
    path('delete_volume_pulled_processor3/<int:pk>/', views.delete_volume_pulled_processor3, name="delete_volume_pulled_processor3"),

    path('addlocation_processor3/', views.addlocation_processor3, name="addlocation_processor3"),
    path('location_list_processor3/', views.location_list_processor3, name="location_list_processor3"),
    path('location_edit_processor3/<int:pk>/', views.location_edit_processor3, name="location_edit_processor3"),
    path('location_delete_processor3/<int:pk>/', views.location_delete_processor3, name="location_delete_processor3"), 
]