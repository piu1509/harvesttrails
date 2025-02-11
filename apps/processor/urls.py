from django.urls import path
from django.contrib.auth.decorators import login_required
from apps.processor import views

urlpatterns = [
    path('list_processor/', views.ListProcessorView, name='list-processor'),
    #14
    path('add_processor/', views.AddProcessorView, name='add-processor'),
    #14
    path('add_processor_user/<int:pk>/', views.add_processor_user, name='add_processor_user'),
    path('processor_update/<int:pk>/', views.ProcessorUpdate, name='update-processor'),
    path('processor_delete/<int:pk>/', views.ProcessorDelete, name='delete-processor'),
    path('add_location/', views.addlocation, name='add-location'),
    path('list_location/', views.location_list, name='list-location'),
    path('location_update/<int:pk>/', views.location_edit, name='location-edit'),
    path('location_delete/<int:pk>/', views.LocationDelete, name='delete-location'),
    path('link_grower_processor', views.LinkGrowertoProcessor, name='link_grower_processor'),
    path('grower_processor_management', views.GrowerProcessorManagement, name='grower_processor_management'),
    path('grower_processor_management_delete/<int:pk>/', views.GrowerProcessorManagementDelete, name='delete-grower-processor'),
    path('all_grower_map_to_processor', views.all_grower_map_to_processor, name='all_grower_map_to_processor'),
    path('grower_map_to_processor/<int:pk>/', views.grower_map_to_processor, name='grower_map_to_processor'),
    # code
    path('grower_shipment/', views.grower_shipment, name='grower_shipment'),  # add grower shipment
    path('qr_code_view/<int:pk>/', views.qr_code_view, name='qr_code_view'),
    path('grower_shipment_list/', views.grower_shipment_list, name='grower_shipment_list'),
    path('grower_shipment_view/<int:pk>/', views.grower_shipment_view, name='grower_shipment_view'),
    path('grower_shipment_delete/<int:pk>/', views.grower_shipment_delete, name='grower_shipment_delete'),
    path('processor_inbound_management/', views.processor_inbound_management, name='processor_inbound_management'),
    path('processor_upcoming_inbound_management/', views.processor_upcoming_inbound_management, name='processor_upcoming_inbound_management'),
    path('processor_inbound_management_view/<int:pk>/', views.processor_inbound_management_view, name='processor_inbound_management_view'),
    
    path('processor_inbound_management_delete/<int:pk>/', views.processor_inbound_management_delete, name='processor_inbound_management_delete'),
    path('processor_inbound_management_edit/<int:pk>/', views.processor_inbound_management_edit, name='processor_inbound_management_edit'),
    path('delete_link_processor_one/<int:pk>/', views.delete_link_processor_one, name="delete_link_processor_one"),
    
    # path('processor_location_assign/<int:pk>/', views.processor_location_assign, name='processor_location_assign'),
    path('processor_outbound_list', views.processor_outbound_list, name='processor_outbound_list'),
    path('processor_outbound_delete/<int:pk>/', views.processor_outbound_delete, name='processor_outbound_delete'),
    path('processor_process_material/<int:pk>/', views.processor_process_material, name='processor_process_material'),
    path('processor_process_material_edit/<int:pk>/', views.processor_process_material_edit, name='processor_process_material_edit'),
    #code
    path('processor_receive_delivery', views.processor_receive_delivery, name='processor_receive_delivery'),
    
    # working
    # path('classing_report_upload', views.classing_report_upload, name='classing_report_upload'),
    # code
    # path('classing_report_farmfield_upload', views.classing_report_farmfield_upload, name='classing_report_farmfield_upload'),
    # path('classing_report_csv_farmfield_list', views.classing_report_csv_farmfield_list, name='classing_report_csv_farmfield_list'),
    # path('classing_report_farmfield_list', views.classing_report_farmfield_list, name='classing_report_farmfield_list'),

    path('classing_report_farmfield_delete/<int:pk>', views.classing_report_farmfield_delete, name='classing_report_farmfield_delete'),
    # working
    path('production_report_upload', views.production_report_upload, name='production_report_upload'),
    
    # work
    # path('classing_report_list', views.classing_report_list, name='classing_report_list'),
    path('production_report_list/', views.production_report_list, name='production_report_list'),
    path('classing_report_delete/<int:pk>', views.classing_report_delete, name='classing_report_delete'),
    path('production_report_delete/<int:pk>', views.production_report_delete, name='production_report_delete'),
    
    
    path('classing_ewr_report_list', views.classing_ewr_report_list, name='classing_ewr_report_list'),
    path('classing_ewr_report_all_downlaod', views.classing_ewr_report_all_downlaod, name='classing_ewr_report_all_downlaod'),
    path('classing_ewr_selected_level_downlaod/<str:selected_level>', views.classing_ewr_selected_level_downlaod, name='classing_ewr_selected_level_downlaod'),
    path('classing_ewr_selectedprocessor_downlaod/<int:selectedprocessor>', views.classing_ewr_selectedprocessor_downlaod, name='classing_ewr_selectedprocessor_downlaod'),
    path('classing_ewr_selectedlevel_selectedprocessor_downlaod/<int:selectedprocessor>/<str:selected_level>', views.classing_ewr_selectedlevel_selectedprocessor_downlaod, name='classing_ewr_selectedlevel_selectedprocessor_downlaod'),
    
    # working
    # path('classing_report_csv_list', views.classing_report_csv_list, name='classing_report_csv_list'),
    # path('production_report_csv_create', views.production_report_csv_create, name='production_report_csv_create'),
    
    # working
    path('production_report_csv_list', views.production_report_csv_list, name='production_report_csv_list'),
    # working
    path('bale_report_list', views.bale_report_list, name='bale_report_list'),
    path('processor_change_password/<int:pk>', views.processor_change_password, name='processor_change_password'),
    # 07/12/2022
    path('classing_upload', views.classing_upload, name='classing_upload'),
    # 14
    path('classing_csv_list', views.classing_csv_list, name='classing_csv_list'),
    path('classing_csv_list_view/<int:pk>', views.classing_csv_list_view, name='classing_csv_list_view'),
    path('classing_list', views.classing_list, name='classing_list'),
    path('classing_delete/<int:pk>', views.classing_delete, name='classing_delete'),
    path('classing_edit/<int:pk>', views.classing_edit, name='classing_edit'),
    path('classing_upload_via_dat', views.classing_upload_via_dat, name='classing_upload_via_dat'),

    # path('classing_ajax_list', views.classing_ajax_list, name='classing_ajax_list'),
    path('classing_csv_list_grower/<int:pk>', views.classing_csv_list_grower, name='classing_csv_list_grower'),
    path('classing_csv_all', views.classing_csv_all, name='classing_csv_all'),
    # BaleReportFarmField Update for Level
    path('classing_csv_all_level_check', views.classing_csv_all_level_check, name='classing_csv_all_level_check'),
    # BaleReportFarmField Update for Certificate
    path('classing_csv_all_certificate_check', views.classing_csv_all_certificate_check, name='classing_csv_all_certificate_check'),
    # BaleReportFarmField Update for Crop Variety
    path('classing_csv_all_crop_variety_check', views.classing_csv_all_crop_variety_check, name='classing_csv_all_crop_variety_check'),
    # BaleReportFarmField Update for Grower Id and Grower Name
    path('classing_report_update', views.classing_report_update, name='classing_report_update'),
    # BaleReportFarmField Update for warehouse_wh_id from wh_id
    path('classing_csv_all_warehouse_wh_id_update', views.classing_csv_all_warehouse_wh_id_update, name='classing_csv_all_warehouse_wh_id_update'),
    # 11-01-23
    path('grower_field_yield_variance/', views.grower_field_yield_variance, name='grower_field_yield_variance'),
    # 12-01-23
    path('grower_field_yield_variance_download/<str:selectedCrop>/<str:selectedFarm_id>/<str:selectedField_id>/<str:selectedGrower_id>/', views.grower_field_yield_variance_download, name='grower_field_yield_variance_download'),
    # 25-01-23
    path('unassign_bale_processor2/<str:bale_id>', views.unassign_bale_processor2, name='unassign_bale_processor2'),
    #06-02-23
    path('inbound_production_mgmt/', views.inbound_production_mgmt, name='inbound_production_mgmt'),
    path('add_volume_pulled/', views.add_volume_pulled, name='add_volume_pulled'),
    path('edit_volume_pulled/<int:pk>/', views.edit_volume_pulled, name='edit_volume_pulled'),
    path('delete_volume_pulled/<int:pk>/', views.delete_volume_pulled, name='delete_volume_pulled'),
    path('inbound_production_mgmt_csv_download/', views.inbound_production_mgmt_csv_download, name='inbound_production_mgmt_csv_download'),
    path('outbound_shipment_mgmt/', views.outbound_shipment_mgmt, name='outbound_shipment_mgmt'),
    # path('add_outbound_shipment/', views.add_outbound_shipment, name='add_outbound_shipment'),
    path('delete_outbound_shipment/<int:pk>/', views.delete_outbound_shipment, name='delete_outbound_shipment'),
    path('edit_outbound_shipment/<int:pk>/', views.edit_outbound_shipment, name='edit_outbound_shipment'),
    path('outbound_shipment_mgmt_csv_download/', views.outbound_shipment_mgmt_csv_download, name='outbound_shipment_mgmt_csv_download'),
    # 04-05-23
    path('rejected_shipments_csv_download/', views.rejected_shipments_csv_download, name='rejected_shipments_csv_download'),
    # 08-05-23
    path('all_shipments_csv_download/', views.all_shipments_csv_download, name='all_shipments_csv_download'),
    #15-03-2024
    path('outbound_shipment_mgmt_view/<int:pk>/', views.outbound_shipment_mgmt_view, name='outbound_shipment_mgmt_view'),
    
    # path('link_processor1_to_processor/', views.link_processor1_to_processor, name="link_processor1_to_processor"),
    path('add_outbound_shipment/', views.add_outbound_shipment_processor1, name="add_outbound_shipment"),
    path('ProcessorToProcessorManagement/', views.Processor1ToProcessorManagement, name="Processor1ToProcessorManagement"),
    path('link_processor_one/', views.link_processor_one, name="link_processor_one"),

    path('autocomplete_suggestions_sku/<int:pro_id>/<str:pro_type>/', views.autocomplete_suggestions_sku, name='autocomplete_suggestions_sku'),

    path('change_passowrd_admin/', views.change_passowrd_admin, name="change_passowrd_admin"),
    
]