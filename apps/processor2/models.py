from django.db import models
from apps.processor.models import *
from apps.field.models import Crop, CropVariety
# from apps.processor.models import BaleReportFarmField

# Create your models here.
TYPE_CHOICES = (
    ("T1","T1"),
    ("T2","T2"),
    ("T3","T3"),
    ("T4","T4"),
)
class ProcessorType(models.Model):
    type_name = models.CharField(choices=TYPE_CHOICES, max_length=5, null=True, blank=True)

    def __str__(self):
        return self.type_name


class Processor2(models.Model):
    """Database model for processor"""
    quickbooks_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    fein = models.CharField(max_length=250, null=True, blank=True,verbose_name='FEIN')
    entity_name = models.CharField(max_length=250, null=True, blank=True,verbose_name='Entity Name')
    billing_address = models.TextField(null=True, blank=True,verbose_name='Billing Address')
    shipping_address = models.TextField(null=True, blank=True,verbose_name='Shipping Address')
    main_number = models.CharField(max_length=250, null=True, blank=True,verbose_name='Main Number')
    main_fax = models.CharField(max_length=250, null=True, blank=True,verbose_name='Main Fax')
    main_email = models.CharField(max_length=255, null=True, blank=True, verbose_name='Main Email')
    website = models.TextField(null=True, blank=True,verbose_name='Website')
    account_number = models.CharField(max_length=255, null=True, blank=True)
    processor_type = models.ManyToManyField(ProcessorType, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.entity_name

class ProcessorUser2(models.Model):
    """Database model for processor User"""
    processor2 = models.ForeignKey(Processor2, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Processor2')
    contact_name = models.CharField(max_length=250, null=True, blank=True,verbose_name='Contact Name')
    contact_email = models.CharField(max_length=250, null=True, blank=True,verbose_name='Contact Email')
    contact_phone = models.CharField(max_length=250, null=True, blank=True,verbose_name='Contact Phone')
    contact_fax = models.CharField(max_length=250, null=True, blank=True,verbose_name='Contact Fax')
    p_password_raw = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return self.contact_email


class Processor2Location(models.Model):
    upload_choice = [
        ("shapefile", "Shapefile"),
        ("coordinates", "Coordinates"),
    ]
    processor = models.ForeignKey(Processor2, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Processor2')
    name =  models.CharField(max_length=250, null=True, blank=True,verbose_name='Location2 Name')
    upload_type = models.CharField(max_length=11,choices=upload_choice,verbose_name='Upload2 Type')
    shapefile_id = models.FileField(upload_to='processor2_shapefile',null=True, blank=True,verbose_name='Shapefile ID2')
    latitude = models.CharField(max_length=200,null=True, blank=True,verbose_name='Latitude2')
    longitude = models.CharField(max_length=200,null=True, blank=True,verbose_name='Longitude2')
    eschlon_id = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"Processor = {self.processor}, Location = {self.name}"
    

class AssignedBaleProcessor2(models.Model):
    processor2 = models.ForeignKey(Processor2, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Processor2')
    bale = models.ForeignKey(BaleReportFarmField, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Bale')
    assigned_bale = models.CharField(max_length=250, null=True, blank=True,verbose_name='Bale ID')
    prod_id = models.CharField(max_length=200, null=True, blank=True)
    wt = models.CharField(max_length=200, null=True, blank=True)
    net_wt = models.CharField(max_length=200, null=True, blank=True)
    load_id = models.CharField(max_length=200, null=True, blank=True)
    dt_class = models.CharField(max_length=200, null=True, blank=True)
    gr = models.CharField(max_length=200, null=True, blank=True)
    lf = models.CharField(max_length=200, null=True, blank=True)
    st = models.CharField(max_length=200, null=True, blank=True)
    mic = models.CharField(max_length=200, null=True, blank=True)
    ex = models.CharField(max_length=200, null=True, blank=True)
    rm = models.CharField(max_length=200, null=True, blank=True)
    str_no = models.CharField(max_length=200, null=True, blank=True)
    cgr = models.CharField(max_length=200, null=True, blank=True)
    rd = models.CharField(max_length=200, null=True, blank=True)
    tr = models.CharField(max_length=200, null=True, blank=True)
    unif = models.CharField(max_length=200, null=True, blank=True)
    len_num = models.CharField(max_length=200, null=True, blank=True)
    elong = models.CharField(max_length=200, null=True, blank=True)
    cents_lb = models.CharField(max_length=200, null=True, blank=True)
    loan_value = models.CharField(max_length=200, null=True, blank=True)
    warehouse_wt = models.CharField(max_length=200, null=True, blank=True)
    warehouse_bale_id = models.CharField(max_length=200, null=True, blank=True)
    warehouse_wh_id = models.CharField(max_length=200, null=True, blank=True)

    farm_name = models.CharField(max_length=200, null=True, blank=True)
    sale_status = models.CharField(max_length=200, null=True, blank=True)
    wh_id = models.CharField(max_length=200, null=True, blank=True)
    ob1 = models.CharField(max_length=200, null=True, blank=True)
    gin_date = models.DateField(null=True, blank=True)
    farm_id = models.CharField(max_length=200, null=True, blank=True)
    field_name = models.CharField(max_length=200, null=True, blank=True)
    pk_num = models.CharField(max_length=200, null=True, blank=True)
    grower_idd = models.CharField(max_length=200, null=True, blank=True, verbose_name='grower id')
    grower_name = models.CharField(max_length=200, null=True, blank=True, verbose_name='grower name')
    field_idd = models.CharField(max_length=200, null=True, blank=True, verbose_name='field id')
    certificate = models.CharField(max_length=200, null=True, blank=True, verbose_name='certificate')
    value = models.CharField(max_length=200, null=True, blank=True)
    level = models.CharField(max_length=200, null=True, blank=True)
    crop_variety = models.CharField(max_length=200, null=True, blank=True)
    mark_id = models.CharField(max_length=200, null=True, blank=True)
    gin_id = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"Processor = {self.processor2}, Bale = {self.bale}"

class LinkProcessorToProcessor(models.Model):
    processor = models.ForeignKey(Processor2, on_delete=models.CASCADE, null=True, blank=True, related_name="processor")
    linked_processor = models.ForeignKey(Processor2, on_delete=models.CASCADE, null=True, blank=True, related_name="linked_procesor")

    def __str__(self):
        return f"Processor = {self.processor}, Linked processor = {self.linked_processor}"

class ProductionManagementProcessor2(models.Model):
    processor = models.ForeignKey(Processor2, on_delete=models.CASCADE, null=True, blank=True)
    processor_e_name = models.CharField(max_length=200, null=True, blank=True)
    total_volume = models.CharField(max_length=200, null=True, blank=True)
    inbound = models.CharField(max_length=200, null=True, blank=True)
    date_pulled = models.DateField(null=True, blank=True)
    bin_location = models.CharField(max_length=200, null=True, blank=True)
    volume_pulled = models.CharField(max_length=200, null=True, blank=True)
    milled_volume = models.CharField(max_length=200, null=True, blank=True)
    volume_left = models.CharField(max_length=200, null=True, blank=True)
    milled_storage_bin = models.CharField(max_length=200, null=True, blank=True)
    editable_obj = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f"Processor = {self.processor}"

STATUS_CHOICES = (
    ("APPROVED", "APPROVED"),
    ("DISAPPROVED", "DISAPPROVED"),
    ("", ""),
)

Processor_Type =(
    ("T1","T1"),
    ("T2","T2"),
    ("T3","T3"),
    ("T4","T4"),
    ("Buyer","Buyer"),
)

class ShipmentManagement(models.Model):
    @staticmethod
    def crop_choices():
        crops = Crop.objects.all()
        return [(crop.code, crop.name) for crop in crops]
    @staticmethod
    def variety_choices():
        varieties = CropVariety.objects.all()
        return [(variety.variety_code, variety.variety_name) for variety in varieties] 
    
    shipment_id = models.CharField(max_length=200, null=True, blank=True)
    processor_idd = models.CharField(max_length=200, null=True, blank=True)
    processor_e_name = models.CharField(max_length=200, null=True, blank=True)
    sender_processor_type = models.CharField(max_length=5, choices=Processor_Type, null=True, blank=True)
    crop = models.CharField(max_length=255, choices=[], default="RICE")
    variety = models.CharField(max_length=255, choices=[], default="DG-263L")
    production_management = models.ForeignKey(ProductionManagement,on_delete=models.CASCADE, null=True, blank=True)
    prod_mgmt_processor2 = models.ForeignKey(ProductionManagementProcessor2, on_delete=models.CASCADE, null=True, blank=True)
    bin_location = models.CharField(max_length=200, null=True, blank=True, verbose_name='MILLED STORAGE BIN')
    date_pulled = models.DateTimeField(auto_now_add=True)
    milled_volume = models.CharField(max_length=200, null=True, blank=True)
    equipment_type = models.CharField(max_length=200,choices=EquipmentType, null=True, blank=True)
    equipment_id = models.CharField(max_length=200, null=True, blank=True)
    purchase_order_number = models.CharField(max_length=200, null=True, blank=True)
    lot_number = models.CharField(max_length=200, null=True, blank=True)
    volume_shipped = models.CharField(max_length=200, null=True, blank=True)
    volume_left = models.CharField(max_length=200, null=True, blank=True)
    editable_obj = models.BooleanField(null=True, blank=True)
    storage_bin_send = models.CharField(max_length=200, null=True, blank=True,verbose_name='Storage Bin ID(SKU ID)(storage_bin_send)')
    storage_bin_recive = models.CharField(max_length=200, null=True, blank=True,verbose_name='Storage Bin ID(SKU ID)(storage_bin_recive)')
    weight_of_product = models.CharField(max_length =200,null=True, blank=True,default=0,help_text ='default unit is pound')
    weight_of_product_raw = models.CharField(max_length =200,null=True, blank=True,default=0,help_text ='if unit is pound, then weight_of_product_raw and weight_of_product is same' )
    weight_of_product_unit =   models.CharField(max_length=200,choices=unit_choice, null=True, blank=True,verbose_name='Unit')
    excepted_yield = models.CharField(max_length =200,null=True, blank=True,default=0,help_text ='default unit is pound')
    excepted_yield_raw = models.CharField(max_length =200,null=True, blank=True,default=0,help_text ='if unit is pound, then excepted_yield_raw and excepted_yield is same' )
    excepted_yield_unit =   models.CharField(max_length=200,choices=unit_choice, null=True, blank=True,verbose_name='Unit')
    moisture_percent = models.CharField(max_length=200, null=True, blank=True)
    files = models.ManyToManyField(File, related_name='shipments', blank=True)
    receiver_processor_type = models.CharField(max_length=200, choices=Processor_Type, null=True, blank=True)
    processor2_idd = models.CharField(max_length=200, null=True, blank=True)
    processor2_name = models.CharField(max_length=250, null=True, blank=True)
    recive_delivery_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)
    received_weight = models.CharField(max_length=10, null=True, blank=True)
    ticket_number = models.CharField(max_length=20, null=True, blank=True)
    qr_code_processor = models.FileField(upload_to='qr_code_processor/',null=True, blank=True)
    reason_for_disapproval = models.CharField(max_length=200, null=True, blank=True,verbose_name='Reason For Disapproval')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)    
        self._meta.get_field('crop').choices = self.crop_choices()
        self._meta.get_field('variety').choices = self.variety_choices()

    def __str__(self):
        return f"Shipment Id = {self.shipment_id}, Sender Processor = {self.processor_e_name}, Receiver processor = {self.processor2_name}"

class LinkProcessor1ToProcessor(models.Model):
    processor1 = models.ForeignKey(Processor, on_delete=models.CASCADE, null=True,blank=True)
    processor2 = models.ForeignKey(Processor2, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Processor = {self.processor1}, Linked processor = {self.processor2}"

Processor_Type2 = (
    ("T1", "T1"),
    ("T2", "T2"),
    ("T3", "T3"),
    ("T4", "T4"),
)

class Processor_sku(models.Model):
    processor_type = models.CharField(max_length=5, choices=Processor_Type2)
    processor1 = models.ForeignKey(Processor, on_delete=models.CASCADE, null=True, blank=True)
    processor2 = models.ForeignKey(Processor2, on_delete=models.CASCADE, null=True, blank=True)
    sku_id = models.CharField(max_length=100)


    def _str_(self):
        p_type = self.processor_type
        if p_type == "T1":
            return f"{p_type} || {self.processor1_id.entity_name} || SKU ID:-{self.sku_id}"
        else:
            return f"{p_type} || {self.processor2_id.entity_name} || SKU ID:-{self.sku_id}"

        