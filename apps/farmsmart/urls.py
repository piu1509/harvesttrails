from django.urls import path
from apps.farmsmart import views


urlpatterns = [
    # Login API
    path('login_user_api', views.login_user_api, name='login_user_api'),

    # grower farm list
    path('grower_farm_list_api', views.grower_farm_list_api, name='grower_farm_list_api'),
    path('grower_farm_list_search_api', views.grower_farm_list_search_api, name='grower_farm_list_search_api'),
    # grower farm view
    path('grower_farm_view_api', views.grower_farm_view_api, name='grower_farm_view_api'),
    # grower farm create 
    path('grower_farm_create_api', views.grower_farm_create_api, name='grower_farm_create_api'),
    # grower farm edit
    path('grower_farm_edit_api', views.grower_farm_edit_api, name='grower_farm_edit_api'),
    # grower farm delete
    path('grower_farm_delete_api', views.grower_farm_delete_api, name='grower_farm_delete_api'),


    # grower field list
    path('grower_field_list_api', views.grower_field_list_api, name='grower_field_list_api'),
    path('grower_field_list_search_api', views.grower_field_list_search_api, name='grower_field_list_search_api'),
    # grower field view 
    path('grower_field_view_api', views.grower_field_view_api, name='grower_field_view_api'),
    # grower field create 
    path('grower_field_create_api', views.grower_field_create_api, name='grower_field_create_api'),
    # farm dropdown for field.....
    path('grower_farmdwopdown_forfield_api', views.grower_farmdwopdown_forfield_api, name='grower_farmdwopdown_forfield_api'),
    # grower field edit
    path('grower_field_edit_api', views.grower_field_edit_api, name='grower_field_edit_api'),
    # grower field delete 
    path('grower_field_delete_api', views.grower_field_delete_api, name='grower_field_delete_api'),


    # grower dashboard
    path('grower_dashboard_api', views.grower_dashboard_api, name='grower_dashboard_api'),

    # grower shipmant list 
    path('grower_shipment_list_api', views.grower_shipment_list_api, name='grower_shipment_list_api'),
    path('grower_shipment_list_search_api', views.grower_shipment_list_search_api, name='grower_shipment_list_search_api'),
    # grower shipmant QR
    path('grower_shipment_qrcode_api', views.grower_shipment_qrcode_api, name='grower_shipment_qrcode_api'),

    
    # grower shipmant view
    path('grower_shipment_view_api', views.grower_shipment_view_api, name='grower_shipment_view_api'),
    # grower send shipmant 
    path('grower_send_shipment_api', views.grower_send_shipment_api, name='grower_send_shipment_api'),
    # grower stogare for shipmant
    path('grower_send_shipment_storage_name_api', views.grower_send_shipment_storage_name_api, name='grower_send_shipment_storage_name_api'),
    # grower field for shipmant
    path('grower_send_shipment_field_name_api', views.grower_send_shipment_field_name_api, name='grower_send_shipment_field_name_api'),
    # grower shipment delete 
    path('grower_shipment_delete_api', views.grower_shipment_delete_api, name='grower_shipment_delete_api'),
    
    
    # processor_linked_grower_storage_api
    path('processor_linked_grower_storage_api', views.processor_linked_grower_storage_api, name='processor_linked_grower_storage_api'),
    # processor_linked_grower_field_api
    path('processor_linked_grower_field_api', views.processor_linked_grower_field_api, name='processor_linked_grower_field_api'),

    # processor inbound list
    path('processor_inbound_list_api', views.processor_inbound_list_api, name='processor_inbound_list_api'),
    path('processor_inbound_list_search_api', views.processor_inbound_list_search_api, name='processor_inbound_list_search_api'),
    # processor upcomming_inbound_list_api
    path('processor_upcomming_inbound_list_api', views.processor_upcomming_inbound_list_api, name='processor_upcomming_inbound_list_api'),
    path('processor_upcomming_inbound_list_search_api', views.processor_upcomming_inbound_list_search_api, name='processor_upcomming_inbound_list_search_api'),
    # processor inbound view
    path('processor_inbound_view_api', views.processor_inbound_view_api, name='processor_inbound_view_api'),
    # processor inbound delete
    path('processor_inbound_delete_api', views.processor_inbound_delete_api, name='processor_inbound_delete_api'),
    # processor with linked grower
    path('processor_linked_grower_api', views.processor_linked_grower_api, name='processor_linked_grower_api'),
    # processor location list
    path('processor_location_list_api', views.processor_location_list_api, name='processor_location_list_api'),
    # processor location add inbound management
    path('processor_inbound_management_location_add_api', views.processor_inbound_management_location_add_api, name='processor_inbound_management_location_add_api'),
    # processor receive delivery
    path('processor_receive_delivery_api', views.processor_receive_delivery_api, name='processor_receive_delivery_api'),
    # processor outbound list
    path('processor_outbound_list_api', views.processor_outbound_list_api, name='processor_outbound_list_api'),
    path('processor_outbound_list_search_api', views.processor_outbound_list_search_api, name='processor_outbound_list_search_api'),
    
    # processor outbound view
    path('processor_outbound_view_api', views.processor_outbound_view_api, name='processor_outbound_view_api'),
    # processor process material
    path('processor_process_material_api', views.processor_process_material_api, name='processor_process_material_api'),
    # processor Scan Qr Code
    path('processor_scan_qr_code_api', views.processor_scan_qr_code_api, name='processor_scan_qr_code_api'),
    # processor Scan Qr STATUS CHECk
    path('processor_scanqrcode_status_approved_api', views.processor_scanqrcode_status_approved_api, name='processor_scanqrcode_status_approved_api'),
    # 24/01/23
    # processor classing list
    path('classing_list_api', views.classing_list_api, name='classing_list_api'),
    # processor classing all report list
    path('classing_csv_list_api', views.classing_csv_list_api, name='classing_csv_list_api'),
    # processor classing view popup report
    path('classing_csv_list_view_api', views.classing_csv_list_view_api, name='classing_csv_list_view_api'),
    # 09-03-23
    # PRODUCTION MANAGEMENT
    path('production_management_list_api', views.production_management_list_api, name='production_management_list_api'),
    path('get_total_rice_volume_api', views.get_total_rice_volume_api, name='get_total_rice_volume_api'),
    path('add_volume_pulled_api', views.add_volume_pulled_api, name='add_volume_pulled_api'),
    # 16-03-23
    # SHIPMENT MANAGEMENT
    path('outbound_shipment_management_list_api', views.outbound_shipment_management_list_api, name='outbound_shipment_management_list_api'),
    path('get_rice_volume_from_bin_location_pulled_api', views.get_rice_volume_from_bin_location_pulled_api, name='get_rice_volume_from_bin_location_pulled_api'),
    path('add_outbound_shipment_management_api', views.add_outbound_shipment_management_api, name='add_outbound_shipment_management_api'),
    # 13-05-23 grower_grower_payments
    path('grower_grower_payments_list', views.grower_grower_payments_list, name='grower_grower_payments_list'),
    path('grower_grower_payments_view', views.grower_grower_payments_view, name='grower_grower_payments_view'),
    path('grower_grower_payments_cal_details', views.grower_grower_payments_cal_details, name='grower_grower_payments_cal_details'),
    # 23-05-23 Tier2 processor
    path('t2_processor_dashboard_api', views.t2_processor_dashboard_api, name='t2_processor_dashboard_api'),
    # 23-05-23 EWR Reprt Download for processor
    path('t2_processor_EWR_reprt_download', views.t2_processor_EWR_reprt_download, name='t2_processor_EWR_reprt_download'),
    path('processor_EWR_reprt_download', views.processor_EWR_reprt_download, name='processor_EWR_reprt_download'),
    # 27-05-23
    path('t2_processor_classing_list_api', views.t2_processor_classing_list_api, name='t2_processor_classing_list_api'),
    path('t2_processor_classing_view_api', views.t2_processor_classing_view_api, name='t2_processor_classing_view_api'),
    # 29-05-23 Grower Dropdown for Tier 2 Processor
    path('t2_processor_grower_dropdown_api', views.t2_processor_grower_dropdown_api, name='t2_processor_grower_dropdown_api'),
    # 25-07-23 Grower Dashboard
    path('grower_dashboard_graph_api', views.grower_dashboard_graph_api, name='grower_dashboard_graph_api'),
    # 31-07-23 Digital crop consultant
    path('grower_digital_crop_consultant_api', views.grower_digital_crop_consultant_api, name='grower_digital_crop_consultant_api'),
    # 31-07-23 Digital crop consultant CHAT API
    path('grower_digital_crop_consultant_chat_api', views.grower_digital_crop_consultant_chat_api, name='grower_digital_crop_consultant_chat_api'),
    path('grower_digital_crop_consultant_get_chat_api', views.grower_digital_crop_consultant_get_chat_api, name='grower_digital_crop_consultant_get_chat_api'),
    # 17-08-23
    path('grower_profile_api', views.grower_profile_api, name='grower_profile_api'),
    # 21-08-23
    path('grower_storage_list_api', views.grower_storage_list_api, name='grower_storage_list_api'),
    path('grower_storage_map_api', views.grower_storage_map_api, name='grower_storage_map_api'),
    path('grower_field_map_api', views.grower_field_map_api, name='grower_field_map_api'),
    # 28-08-23
    path('processor_profile_api', views.processor_profile_api, name='processor_profile_api'),
    path('tier2_processor_profile_api', views.tier2_processor_profile_api, name='tier2_processor_profile_api'),
    # 08-09-23
    path('application_update_api', views.application_update_api, name='application_update_api'),
    # 25-09-23 by Rina
    # growerpaymentdetails_api 
    path('growerpaymentdetails_api/', views.growerpaymentdetails_api, name='growerpaymentdetails_api'),
    # growerbale_list_api
    path('growerbale_list_api', views.growerbale_list_api, name='growerbale_list_api'),
    # growerbale_details_api
    path('growerbale_details_api', views.growerbale_details_api, name='growerbale_details_api'),
    path('processor_outbound_shipment_list_api', views.processor_outbound_shipment_list_api, name='processor_outbound_shipment_list_api'),
    path('processor_outbound_shipment_view_api',views.processor_outbound_shipment_view_api, name='processor_outbound_shipment_view_api'),
    path('processor_outbound_shipment_list_search_api', views.processor_outbound_shipment_list_search_api, name='processor_outbound_shipment_list_search_api'),
    path('add_outbound_shipment_processor_destination_api', views.add_outbound_shipment_processor_destination_api, name='add_outbound_shipment_processor_destination_api'),
    path('add_outbound_shipment_processor_squ_list_api', views.add_outbound_shipment_processor_squ_list_api, name='add_outbound_shipment_processor_squ_list_api'),
    path('add_outbound_shipment_processor_milled_volume', views.add_outbound_shipment_processor_milled_volume, name='add_outbound_shipment_processor_milled_volume'),
    path('add_outbound_shipment_processor_api', views.add_outbound_shipment_processor_api, name='add_outbound_shipment_processor_api'),
    path('processor_management_list_api', views.processor_management_list_api, name='processor_management_list_api'),
    path('processor_management_list_search_api', views.processor_management_list_search_api, name='processor_management_list_search_api'),
    path('add_processor_user_api', views.add_processor_user_api, name='add_processor_user_api'),
    path('processor_edit_api', views.processor_edit_api, name='processor_edit_api'),
    path('processor_password_change_api', views.processor_password_change_api, name='processor_password_change_api'),
    path('processor_location_view_api', views.processor_location_view_api, name='processor_location_view_api'),
    path('processor_location_add_api', views.processor_location_add_api, name='processor_location_add_api'),
    path('processor_location_edit_api', views.processor_location_edit_api, name='processor_location_edit_api'),
    path('processor_location_delete_api', views.processor_location_delete_api, name='processor_location_delete_api'),
    path('processor_to_processor_management_api', views.processor_to_processor_management_api, name='processor_to_processor_management_api'),
    path('processor_inbound_shipment_edit_api', views.processor_inbound_shipment_edit_api, name='processor_inbound_shipment_edit_api'),
    path('receive_delivery_source_list_api', views.receive_delivery_source_list_api, name='receive_delivery_source_list_api'),
    path('processor_details_api', views.processor_details_api, name='processor_details_api'),
    path('check_update_status', views.check_update_status, name='check_update_status'),
    path('update_version', views.update_version, name='update_version'),

    path('distributor_profile_api/', views.distributor_profile_api, name='distributor_profile_api'),
    path('warehouse_manager_profile_api/', views.warehouse_manager_profile_api, name='warehouse_manager_profile_api'),
    path('customer_profile_api/', views.customer_profile_api, name='customer_profile_api'),
    path('add_distributor_user/', views.add_distributor_user, name='add_distributor_user'),
    path('edit_distributor_api/', views.edit_distributor_api, name='edit_distributor_api'),
    path('edit_warehouse_api/', views.edit_warehouse_api, name='edit_warehouse_api'),
    path('edit_customer_api/', views.edit_customer_api, name='edit_customer_api'),
    path('get_distributor_list/', views.get_distributor_list, name='get_distributor_list'),

    path('get_processor_contracts/', views.get_processor_contracts, name='get_processor_contracts'),
    path('get_destination_list/', views.get_destination_list, name='get_destination_list'),
    path('get_selected_processor/', views.get_selected_processor, name='get_selected_processor'),
    path('get_processor_contract_crops/', views.get_processor_contract_crops, name='get_processor_contract_crops'),
    path('create_processor_shipment_api/', views.create_processor_shipment_api, name='create_processor_shipment_api'),
    path('processor_shipment_list_api/', views.processor_shipment_list_api, name='processor_shipment_list_api'),
    path('processor_shipment_view_api/', views.processor_shipment_view_api, name='processor_shipment_view_api'),
    path('edit_processor_shipment_api/', views.edit_processor_shipment_api, name='edit_processor_shipment_api'),
    path('delete_processor_shipment_api/', views.delete_processor_shipment_api, name='delete_processor_shipment_api'),

    path('get_customer_contracts/', views.get_customer_contracts, name='get_customer_contracts'),
    path('get_warehouse_list/', views.get_warehouse_list, name='get_warehouse_list'),
    path('get_selected_customer/', views.get_selected_customer, name='get_selected_customer'),
    path('get_customer_contract_crops/', views.get_customer_contract_crops, name='get_customer_contract_crops'),
    path('create_warehouse_shipment_api/', views.create_warehouse_shipment_api, name='create_warehouse_shipment_api'),
    path('warehouse_shipment_list_api/', views.warehouse_shipment_list_api, name='warehouse_shipment_list_api'),
    path('warehouse_shipment_view_api/', views.warehouse_shipment_view_api, name='warehouse_shipment_view_api'),
    path('edit_warehouse_shipment_api/', views.edit_warehouse_shipment_api, name='edit_warehouse_shipment_api'),
    path('delete_warehouse_shipment_api/', views.delete_warehouse_shipment_api, name='delete_warehouse_shipment_api'),

    path('processor_shipment_invoice/', views.processor_shipment_invoice, name='processor_shipment_invoice'),
    path('warehouse_shipment_invoice/', views.warehouse_shipment_invoice, name='warehouse_shipment_invoice'),
    path('create_payment_for_shipment/', views.create_payment_for_shipment, name='create_payment_for_shipment'),
    path('checkout/<int:pk>/<str:type>/<str:checkout_session_id>/', views.checkout, name='checkout'),

]