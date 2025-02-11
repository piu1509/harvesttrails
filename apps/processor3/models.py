from django.db import models

# Create your models here.

class Processor3(models.Model):
    """ Database model for processor3 """
    fein = models.CharField(max_length=250,blank=True,null=True,verbose_name ='FEIN')
    entity_name = models.CharField(max_length =250 ,blank=True,null=True,verbose_name ='Entity Name')
    billing_address = models.TextField(blank=True,null=True,verbose_name = 'Billing Address')
    shipping_address = models.TextField(blank=True,null=True,verbose_name = 'Shipping Address')
    main_number = models.CharField(max_length =250,null =True, blank=True , verbose_name = 'Main Number')
    main_fax = models.CharField(max_length =250,null=True,blank=True, verbose_name = 'Main Fax')
    website = models.TextField(null=True,blank=True,verbose_name = 'Website')
    
    def __str__(self):
        return self.entity_name
    
class ProcessorUser3(models.Model):
    """ Database model for processoruser3 """ 
    processor3 = models.ForeignKey(Processor3 , on_delete = models.CASCADE , null= True,blank= True, verbose_name ='Select Processor3') 
    contact_name= models.CharField(max_length=250,null=True,blank=True,verbose_name='Contact Name')
    contact_email= models.CharField(max_length = 250,null=True,blank=True,verbose_name ='Contact Email')
    contact_phone= models.CharField(max_length=250,null=True,blank=True,verbose_name='Contact Phone')
    contact_fax= models.CharField(max_length=250,null=True,blank=True,verbose_name ='Contact Fax')
    p_password_raw = models.CharField(max_length=250,null=True,blank=True)
    
    def __str__(self):
        return self.contact_email
    
    
    
        
      