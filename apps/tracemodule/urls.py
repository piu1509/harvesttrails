from django.urls import path
from django.contrib.auth.decorators import login_required
from apps.tracemodule import views

urlpatterns = [
    path('traceability_report_list/', views.traceability_report, name='traceability_report_list'),
    path('showsustainability_metrics/<str:get_search_by>/<int:field_id>/', views.showsustainability_metrics, name='showsustainability_metrics'),
    path('showquality_metrics/<str:get_search_by>/<str:delivery_idd>/', views.showquality_metrics, name='showquality_metrics'),
    
    path('traceability_report_Origin_csv_download/<str:select_crop>/<str:get_search_by>/<str:search_text>/<str:from_date>/<str:to_date>/', views.traceability_report_Origin_csv_download, name='traceability_report_Origin_csv_download'),
    path('traceability_report_WIP1_csv_download/<str:select_crop>/<str:get_search_by>/<str:search_text>/<str:from_date>/<str:to_date>/', views.traceability_report_WIP1_csv_download, name='traceability_report_WIP1_csv_download'),
    path('traceability_report_T1_Processor_csv_download/<str:select_crop>/<str:get_search_by>/<str:search_text>/<str:from_date>/<str:to_date>/', views.traceability_report_T1_Processor_csv_download, name='traceability_report_T1_Processor_csv_download'),
    path('traceability_report_WIP2_csv_download/<str:select_crop>/<str:get_search_by>/<str:search_text>/<str:from_date>/<str:to_date>/', views.traceability_report_WIP2_csv_download, name='traceability_report_WIP2_csv_download'),
    path('traceability_report_T2_Processor_csv_download/<str:select_crop>/<str:get_search_by>/<str:search_text>/<str:from_date>/<str:to_date>/', views.traceability_report_T2_Processor_csv_download, name='traceability_report_T2_Processor_csv_download'),
    path("traceability_report_WIP3_csv_download/<str:select_crop>/<str:get_search_by>/<str:search_text>/<str:from_date>/<str:to_date>/", views.traceability_report_WIP3_csv_download, name="traceability_report_WIP3_csv_download"),
    path("traceability_report_T3_Processor_csv_download/<str:select_crop>/<str:get_search_by>/<str:search_text>/<str:from_date>/<str:to_date>/", views.traceability_report_T3_Processor_csv_download, name="traceability_report_T3_Processor_csv_download"),
    path("traceability_report_WIP4_csv_download/<str:select_crop>/<str:get_search_by>/<str:search_text>/<str:from_date>/<str:to_date>/", views.traceability_report_WIP4_csv_download, name="traceability_report_WIP4_csv_download"),
    path("traceability_report_T4_Processor_csv_download/<str:select_crop>/<str:get_search_by>/<str:search_text>/<str:from_date>/<str:to_date>/", views.traceability_report_T4_Processor_csv_download, name="traceability_report_T4_Processor_csv_download"),
    # all csv download
    path('traceability_report_all_csv_download/<str:select_crop>/<str:get_search_by>/<str:search_text>/<str:from_date>/<str:to_date>/', views.traceability_report_all_csv_download, name='traceability_report_all_csv_download'),
    path('traceability_report_all_csv_download_for_shipment_id/<str:search_text>/<str:from_date>/<str:to_date>/',views.export_all_csv_for_shipmentID, name="export_all_csv_for_shipmentID"),
    path('generate_csv_for_multiple_shipments/<str:search_text>//<str:get_search_by>/<str:from_date>/<str:to_date>/', views.generate_csv_for_multiple_shipments, name='generate_csv_for_multiple_shipments'),
    path('generate_csv_for_recent_shipments/<str:from_date>/<str:to_date>/', views.generate_csv_for_recent_shipments, name='generate_csv_for_recent_shipments'),
    # autocomplete suggestions 03-04-23    
    path('autocomplete_suggestions/<str:select_search>/', views.autocomplete_suggestions, name='autocomplete_suggestions'),
    path('view_trace/<str:search_text>/<str:from_date>/<str:to_date>/', views.trace_shipment, name="view_trace"),
    path('trace_shipment/<str:search_text>/<str:from_date>/<str:to_date>/', views.view_traceability, name="trace_shipment"),
    path('test/', views.transport_list, name="transport_list"),
]