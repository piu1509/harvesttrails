from django.contrib import admin
from apps.processor2.models import *

# Register your models here.
admin.site.register(Processor2)
admin.site.register(ProcessorUser2)
admin.site.register(Processor2Location)
admin.site.register(ProcessorType)
admin.site.register(LinkProcessor1ToProcessor)
admin.site.register(ProductionManagementProcessor2)
admin.site.register(LinkProcessorToProcessor)
admin.site.register(AssignedBaleProcessor2)



class ProcessorSkuAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = ('processor_type', 'get_processor_entity_name', 'sku_id')
    
    # Enable searching on these fields
    search_fields = ('processor1_processor_entity_name', 'processor2_processor_entity_name')

    # Enable filtering based on processor type
    list_filter = ('processor_type',)

    def get_processor_entity_name(self, obj):
        if obj.processor_type == "T1":
            return obj.processor1.entity_name
        else:
            return obj.processor2.entity_name
    get_processor_entity_name.short_description = 'Entity Name'

admin.site.register(Processor_sku, ProcessorSkuAdmin)