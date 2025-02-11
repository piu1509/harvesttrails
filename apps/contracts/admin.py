from django.contrib import admin

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from . import models

"""Registering  all the field application models here to be viewed in django admin panel"""

admin.site.register(models.Contracts)
admin.site.register(models.SignedContracts)
admin.site.register(models.ContractsVerifiers)
admin.site.register(models.VerifiedSignedContracts)


class AdminProcessorContractDocumentsInline(admin.TabularInline):
    model = models.AdminProcessorContractDocuments
    extra = 0


class AdminProcessorContractSignatureInline(admin.TabularInline):
    model = models.AdminProcessorContractSignature
    extra = 0


class CropDetailsInline(admin.TabularInline):
    model = models.CropDetails
    extra = 0  # Number of empty forms displayed initially
    fields = ['crop', 'crop_type', 'contract_amount', 'amount_unit', 'per_unit_rate']
    readonly_fields = ['contract']


@admin.register(models.AdminProcessorContract)
class AdminProcessorContractAdmin(admin.ModelAdmin):
    list_display = ('processor_entity_name', 'processor_type', 'contract_start_date', 'end_date', 'status', 'created_by', 'created_at')
    search_fields = ('processor_id', 'status', 'created_by__username')
    list_filter = ('status', 'processor_type')
    readonly_fields = ('created_at', 'updated_at', 'end_date')
    inlines = [AdminProcessorContractDocumentsInline, AdminProcessorContractSignatureInline, CropDetailsInline]


@admin.register(models.AdminProcessorContractSignature)
class AdminProcessorContractSignatureAdmin(admin.ModelAdmin):
    list_display = ('contract', 'user', 'signed_at')
    search_fields = ('contract__processor_id', 'user__username')
    readonly_fields = ('signed_at',)


@admin.register(models.CropDetails)
class CropDetailsAdmin(admin.ModelAdmin):
    list_display = ('contract', 'crop', 'contract_amount', 'amount_unit')
    search_fields = ('contract__secret_key', 'crop')


@admin.register(models.AdminProcessorContractDocuments)
class AdminProcessorContractDocumentsAdmin(admin.ModelAdmin):
    list_display = ('contract', 'document', 'uploaded_at')
    search_fields = ('contract__processor_id',)
    readonly_fields = ('uploaded_at',)


class AdminCustomerContractDocumentsInline(admin.TabularInline):
    model = models.AdminCustomerContractDocuments
    extra = 0


class AdminCustomerContractSignatureInline(admin.TabularInline):
    model = models.AdminCustomerContractSignature
    extra = 0

class CutomerContrcatCropDetailsInline(admin.TabularInline):
    model = models.CustomerContractCropDetails
    extra = 0  # Number of empty forms displayed initially
    fields = ['crop', 'crop_type', 'contract_amount', 'amount_unit', 'per_unit_rate']
    readonly_fields = ['contract']

@admin.register(models.AdminCustomerContract)
class AdminCustomerContractAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'total_price', 'contract_start_date', 'end_date', 'status', 'created_by', 'created_at')
    search_fields = ('customer_id', 'customer_name','status', 'created_by__username')
    list_filter = ('status','customer_name')
    readonly_fields = ('created_at', 'updated_at', 'end_date')
    inlines = [AdminCustomerContractDocumentsInline, AdminCustomerContractSignatureInline, CutomerContrcatCropDetailsInline]

@admin.register(models.CustomerContractCropDetails)
class CustomerContractCropDetailsAdmin(admin.ModelAdmin):
    list_display = ('contract', 'crop', 'contract_amount', 'amount_unit')
    search_fields = ('contract__secret_key', 'crop')


@admin.register(models.AdminCustomerContractSignature)
class AdminCustomerContractSignatureAdmin(admin.ModelAdmin):
    list_display = ('contract', 'user', 'signed_at')
    search_fields = ('contract__customer_id', 'user__username')
    readonly_fields = ('signed_at',)


@admin.register(models.AdminCustomerContractDocuments)
class AdminCustomerContractDocumentsAdmin(admin.ModelAdmin):
    list_display = ('contract', 'document', 'uploaded_at')
    search_fields = ('contract__customer_id',)
    readonly_fields = ('uploaded_at',)

admin.site.register(models.ShipmentItem)