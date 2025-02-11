from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Warehouse)
admin.site.register(WarehouseUser)
admin.site.register(ProcessorWarehouseShipment)
admin.site.register(ProcessorShipmentCrops)
admin.site.register(Distributor)
admin.site.register(DistributorUser)
admin.site.register(Customer)
admin.site.register(CustomerDocuments)
admin.site.register(CustomerUser)
admin.site.register(ProcessorWarehouseShipmentDocuments)
admin.site.register(CarrierDetails)
admin.site.register(ProcessorShipmentLog)

admin.site.register(WarehouseCustomerShipment)
admin.site.register(WarehouseCustomerShipmentDocuments)
admin.site.register(WarehouseShipmentLog)
admin.site.register(WarehouseShipmentCrops)
admin.site.register(CarrierDetails2)

admin.site.register(PaymentForShipment)
admin.site.register(Invoice)
admin.site.register(Purchase)
admin.site.register(ProcessorShipmentLotNumberTracking)
admin.site.register(WarehouseShipmentLotNumberTracking)

# class ProcessorShipmentCropsInline(admin.TabularInline):  # You can also use StackedInline
#     model = ProcessorShipmentCrops
#     extra = 1  # Number of empty forms displayed for adding new crops
#     fields = ('crop_id', 'crop', 'crop_type', 'ship_quantity', 'ship_weight', 'gross_weight', 'net_weight', 'weight_unit', 'contract_weight_left', 'payment_amount')
#     readonly_fields = ('payment_amount',)  # Make fields read-only if necessary

# @admin.register(ProcessorWarehouseShipment)
# class ProcessorWarehouseShipmentAdmin(admin.ModelAdmin):
#     list_display = ('shipment_id', 'invoice_id', 'processor_entity_name', 'status', 'date_pulled', 'total_payment', 'is_paid')
#     list_filter = ('status', 'is_paid', 'carrier_type', 'outbound_type')
#     search_fields = ('shipment_id', 'invoice_id', 'processor_entity_name', 'customer_name', 'warehouse_name')
#     inlines = [ProcessorShipmentCropsInline]
