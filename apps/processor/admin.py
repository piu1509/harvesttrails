from django.contrib import admin
from apps.processor.models import *
from apps.processor2.models import *
# Register your models here.

admin.site.register(Processor)
admin.site.register(ProcessorUser)
admin.site.register(Location)
admin.site.register(LinkGrowerToProcessor)
admin.site.register(GrowerShipment)
admin.site.register(ProductionManagement)
admin.site.register(GrowerShipmentFile)
admin.site.register(File)
admin.site.register(ShipmentManagement)
