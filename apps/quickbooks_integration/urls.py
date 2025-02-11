from django.urls import path
from apps.quickbooks_integration.views import *

urlpatterns = [
    path('login/', quickbooks_login, name='quickbooks_login'),
    path('callback/', quickbooks_callback, name='quickbooks_callback'),
    path('dashboard/', quickbooks_dashboard, name='quickbooks_dashboard'),  
    
    path('quickbooks_webhook/', quickbooks_webhook_request, name='quickbooks_webhook'),

    path('customers/', customer_list, name='customers'),
    path('import_customer/', import_customer, name='import_customer'),
    path('vendors/', vendor_list, name='vendors'),
    path('import_vendor/', import_vendor, name='import_vendor'),
    path('items/', item_list, name='items'),
    path('import_item/', import_item, name='import_item'),

    
]