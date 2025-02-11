from django.db import models
# from apps.field.models import Field as Fieldd
from apps.accounts.models import *
from django.db.models.fields import TextField
# Create your models here.

class Storage(models.Model):
    upload_choice = [
        ("shapefile", "Shapefile"),
        ("coordinates", "Coordinates"),
    ]
    storage_name = models.CharField(max_length=200,verbose_name='Storage Name')
    storage_uniqueid = models.CharField(max_length=200, null=True, blank=True,verbose_name='Storage ID')
    grower = models.ForeignKey('grower.Grower', on_delete=models.CASCADE,verbose_name='Grower Name')
    crop = models.CharField(max_length=200, null=True, blank=True,verbose_name='Select crop')
    upload_type = models.CharField(max_length=11,choices=upload_choice,verbose_name='Upload Type')
    shapefile_id = models.FileField(upload_to='shapefile',null=True, blank=True,verbose_name='Shapefile ID')
    latitude = models.CharField(max_length=200,null=True, blank=True,verbose_name='Latitude')
    longitude = models.CharField(max_length=200,null=True, blank=True,verbose_name='Longitude')
    eschlon_id = models.CharField(max_length=200, null=True, blank=True)
    
    def __str__(self):
        return self.storage_name
    

    def get_grower_name(self):
        return self.grower.name
    
    
class ShapeFileDataCo(models.Model):
    coordinates = models.JSONField(default=list)
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, null=True, blank=True)
    
    
status_choice = [
        ("quantity_in", "Quantity In"),
        ("quantity_edit", "Quantity Edit"),
    ]
unit_choice = [
    ("LBS","LBS"),
    ("BU","BU"),
]
class StorageFeedCsv(models.Model):
    csv_path = models.FileField(upload_to='storage_feed/',null=True, blank=True,verbose_name='Storage Feed CSV')
    upload_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Upload By')
    upload_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    def __str__(self):
        return f"{self.upload_by.username}"
    
class StorageFeed(models.Model):
    grower =  models.ForeignKey('grower.Grower', on_delete=models.CASCADE, null=True, blank=True,verbose_name='Grower Name')
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, null=True, blank=True,)
    field = models.ForeignKey('field.field', on_delete=models.CASCADE,null=True, blank=True)
    crop = models.CharField(max_length=200, null=True, blank=True,verbose_name='Select crop')
    status = models.CharField(max_length=200,choices=status_choice, null=True, blank=True,verbose_name='Quantity Status')
    quantity = models.CharField(max_length =200,null=True, blank=True,default=0,help_text ='default unit is pound')
    quantity_raw = models.CharField(max_length =200,null=True, blank=True,default=0,help_text ='if unit is pound quantity_raw and quantity is same' )
    shipment_id = models.CharField(max_length=200, null=True, blank=True,verbose_name='Shipment ID')
    unit =   models.CharField(max_length=200,choices=unit_choice, null=True, blank=True,verbose_name='Unit')
    final_quantity = models.CharField(max_length=200,null=True, blank=True,help_text ='default unit is pound')
    storage_feed_date = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    csv_file = models.ForeignKey(StorageFeedCsv, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Csv File')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Created By')
        
    def __str__(self):
        return f"{self.grower.name} - {self.storage.storage_name} " + str(self.field.name) if self.field else "---" + f"{self.quantity} LBS"
        