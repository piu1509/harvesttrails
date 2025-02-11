from django.urls import path
from django.contrib.auth.decorators import login_required
from apps.processor2 import views

urlpatterns = [
    path('list_processor2/', views.list_processor2, name='list_processor2'),
    path('add_processor2/', views.add_processor2, name='add_processor2'),
    path('add_processor2_user/<int:pk>/', views.add_processor2_user, name='add_processor2_user'),
    path('processor2_update/<int:pk>/', views.processor2_update, name='processor2_update'),
    path('processor2_change_password/<int:pk>/', views.processor2_change_password, name='processor2_change_password'),
    path('processor2_delete/<int:pk>/', views.processor2_delete, name='processor2_delete'),

    path('add_bale_processor2/', views.add_bale_processor2, name='add_bale_processor2'),
    path('list_bale_processor2/', views.list_bale_processor2, name='list_bale_processor2'),
    path('classing_csv_list_view2/<int:pk>', views.classing_csv_list_view2, name='classing_csv_list_view2'),
    path('processor2_classing_csv_all2/', views.processor2_classing_csv_all2, name='processor2_classing_csv_all2'),
    # 19-05-23 t2_classing_ewr_report_list
    path('t2_classing_ewr_report_list/', views.t2_classing_ewr_report_list, name='t2_classing_ewr_report_list'),
    path('t2_classing_ewr_report_all_downlaod/<str:p2_id>/<str:level>', views.t2_classing_ewr_report_all_downlaod, name='t2_classing_ewr_report_all_downlaod'),
   
    path('addlocation_processor2/', views.addlocation_processor2, name="addlocation_processor2"),
    path('location_list_processor2/', views.location_list_processor2, name="location_list_processor2"),
    path('location_edit_processor2/<int:pk>/', views.location_edit_processor2, name="location_edit_processor2"),
    path('location_delete_processor2/<int:pk>/', views.location_delete_processor2, name="location_delete_processor2"),

    path('add_outbound_shipment_processor2/', views.add_outbound_shipment_processor2, name="add_outbound_shipment_processor2"),
    path('outbound_shipment_list/', views.outbound_shipment_list, name="outbound_shipment_list"),
    path('outbound_shipment_view/<int:pk>/', views.outbound_shipment_view, name="outbound_shipment_view"),
    path('outbound_shipment_delete/<int:pk>/', views.outbound_shipment_delete, name="outbound_shipment_delete"),
    path('outbound_shipment_processor2_csv_download/', views.outbound_shipment_processor2_csv_download, name="outbound_shipment_processor2_csv_download"),

    path('inbound_shipment_list/', views.inbound_shipment_list, name="inbound_shipment_list"),
    path('inbound_shipment_view/<int:pk>/', views.inbound_shipment_view, name="inbound_shipment_view"),
    path('inbound_shipment_edit/<int:pk>/', views.inbound_shipment_edit, name="inbound_shipment_edit"),
    path('inbound_shipment_delete/<int:pk>/', views.inbound_shipment_delete, name="inbound_shipment_delete"),    
    path('recive_shipment/', views.recive_shipment, name="recive_shipment"), 
    path('rejected_shipments_csv_download_for_t2/', views.rejected_shipments_csv_download_for_t2, name="rejected_shipments_csv_download_for_t2"),
    path('all_shipments_csv_download_for_t2/', views.all_shipments_csv_download_for_t2, name="all_shipments_csv_download_for_t2"),

    path('link_processor_two/', views.link_processor_two, name="link_processor_two"),
    path('processor2_processor_management/', views.processor2_processor_management, name="processor2_processor_management"),
    path('delete_link_processor_two/<int:pk>/', views.delete_link_processor_two, name="delete_link_processor_two"),
    
    path('inbound_production_management/', views.inbound_production_management, name="inbound_production_management"),
    path('add_volume_pulled_processor2/', views.add_volume_pulled_processor2, name="add_volume_pulled_processor2"),
    path('edit_volume_pulled_processor2/<int:pk>/', views.edit_volume_pulled_processor2, name="edit_volume_pulled_processor2"),
    path('delete_volume_pulled_processor2/<int:pk>/', views.delete_volume_pulled_processor2, name="delete_volume_pulled_processor2"),
]