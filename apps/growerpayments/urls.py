from django.urls import path

from apps.growerpayments import views

urlpatterns = [
    path('entry_feeds_add/', views.entry_feeds_add, name='entry_feeds_add'),
    path('entry_feeds_list/', views.entry_feeds_list, name='entry_feeds_list'),
    path('entry_feeds_delete/<int:pk>/', views.entry_feeds_delete, name='entry_feeds_delete'),
    path('entry_feeds_edit/<int:pk>/', views.entry_feeds_edit, name='entry_feeds_edit'),
    # grower delivery details
    path('grower_payments_table/', views.grower_payments_table, name='grower_payments_table'),
    # grower payments details
    path('grower_payments_list/', views.grower_payments_list, name='grower_payments_list'),
    # 31-01-23
    path('ajax_grower_payments_list/<str:grower_id>/<str:crop_id>/', views.ajax_grower_payments_list, name='ajax_grower_payments_list'),

    path('grower_payments_add/<str:var>/<str:pk>', views.grower_payments_add, name='grower_payments_add'),
    path('grower_payments_bulk_add/', views.grower_payments_bulk_add, name='grower_payments_bulk_add'),
    path('grower_payments_edit/<str:var>/<str:pk>/', views.grower_payments_edit, name='grower_payments_edit'),
    path('nasdaq_get_data/', views.nasdaq_get_data, name='nasdaq_get_data'),
    # 26/12/22
    path('grower_payments_table_csv_download/', views.grower_payments_table_csv_download, name='grower_payments_table_csv_download'),
    path('grower_payments_list_csv_download/', views.grower_payments_list_csv_download, name='grower_payments_list_csv_download'),
    # 30/12/22
    path('grower_split_payee_add/', views.grower_split_payee_add, name='grower_split_payee_add'),
    path('grower_split_payee_list/', views.grower_split_payee_list, name='grower_split_payee_list'),
    path('grower_payment_split_list/', views.grower_payment_split_list, name='grower_payment_split_list'),
    path('grower_split_payee_edit/<int:grower_payee_iddd>', views.grower_split_payee_edit, name='grower_split_payee_edit'),
    path('grower_split_payee_delete/<int:pk>', views.grower_split_payee_delete, name='grower_split_payee_delete'),
    path('split_payee_block_delete/<int:id>', views.split_payee_block_delete, name='split_payee_block_delete'),
    path('classing_invoice_bundle_zip/<int:pk>', views.classing_invoice_bundle_zip, name='classing_invoice_bundle_zip'),
    # 06-01-23
    path('processor_grower_certificate_level_status/', views.processor_grower_certificate_level_status, name='processor_grower_certificate_level_status'),
    path('processor_grower_certificate_level_status_csv_download/<str:selectedprocessor>/<str:selectedgrower>/<str:selectedLel>/<str:selectedCre>/<str:selectedpayment>/', views.processor_grower_certificate_level_status_csv_download, name='processor_grower_certificate_level_status_csv_download'),
    # 06-04-23
    path('grower_payments_list_not_paid_csv_download/', views.grower_payments_list_not_paid_csv_download, name='grower_payments_list_not_paid_csv_download'),
    path('grower_payments_list_paid_csv_download/', views.grower_payments_list_paid_csv_download, name='grower_payments_list_paid_csv_download'),
    # 06-04-23
    # path('update_paid_payments_list/',views.update_paid_payments_list,name='update_paid_payments_list'),
    # 22-05-23
    path('nasdaq_list_data/',views.nasdaq_list_data,name='nasdaq_list_data'),
]