from django.db import models
from apps.grower.models import Grower
from apps.processor.models import Processor
from apps.field.models import Field
from apps.farms.models import Farm
from apps.processor.models import *
# Create your models here.
STATUS_CHOICES = (
    ("ACTIVE", "ACTIVE"),
    ("INACTIVE", "INACTIVE"),
)

class EntryFeeds(models.Model):
    grower = models.ForeignKey(Grower, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Grower')
    crop = models.CharField(max_length=200, null=True, blank=True,verbose_name='Select Item')
    contracted_payment_option = models.CharField(max_length=200, null=True, blank=True,verbose_name='Contracted Payment Option')
    contract_base_price = models.CharField(max_length=200, null=True, blank=True,verbose_name='Contract Base Price / LBS')
    sustainability_premium = models.CharField(max_length=200, null=True, blank=True,verbose_name='Sustainability Premium')
    quality_premium = models.CharField(max_length=200, null=True, blank=True,verbose_name='Quality Premium')
    status = models.CharField(max_length=200,choices=STATUS_CHOICES,default="ACTIVE")
    date_time = models.DateTimeField(auto_created=True, auto_now_add=True,verbose_name='Modified Date')
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'{self.grower.name} | {self.crop} | {self.contracted_payment_option}'

class GrowerPayments(models.Model):
    enteyfeeds = models.ForeignKey(EntryFeeds, on_delete=models.CASCADE, null=True, blank=True,verbose_name='EntryFeeds')
    processor = models.IntegerField(null=True, blank=True,verbose_name='Select Processor')
    grower = models.ForeignKey(Grower, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Grower')
    # 06-04-23
    grower_name = models.CharField(max_length=250, null=True, blank=True)
    field_name = models.CharField(max_length=250, null=True, blank=True)
    farm_name = models.CharField(max_length=250, null=True, blank=True)
    level = models.CharField(max_length=250, null=True, blank=True)

    field = models.IntegerField(null=True, blank=True,verbose_name='Select Field')
    farm = models.IntegerField(null=True, blank=True,verbose_name='Select Farm')
    crop = models.CharField(max_length=200, null=True, blank=True,verbose_name='Select Item')
    variety = models.CharField(max_length=200, null=True, blank=True,verbose_name='Select Variety')
    # bale_id
    delivery_id = models.CharField(max_length=200, null=True, blank=True,verbose_name='Delivery Id')
    # from DB
    delivery_date = models.CharField(max_length=200, null=True, blank=True,verbose_name='Delivery Date')
    # Net Weight
    delivery_lbs = models.CharField(max_length=200, null=True, blank=True,verbose_name='Delivery Lbs')
    contract_base_price = models.CharField(max_length=200, null=True, blank=True,verbose_name='Contract Base Price / LBS')
    sustainability_premium = models.CharField(max_length=200, null=True, blank=True,verbose_name='Sustainability Premium')
    quality_premium = models.CharField(max_length=200, null=True, blank=True,verbose_name='Quality Premium')
    total_price = models.CharField(max_length=200, null=True, blank=True,verbose_name='Total price')
    delivered_value = models.CharField(max_length=200, null=True, blank=True,verbose_name='Delivered Value')
    payment_due_date = models.CharField(max_length=200, null=True, blank=True,verbose_name='Payment Due Date')
    
    payment_amount = models.CharField(max_length=200, null=True, blank=True,verbose_name='Payment Amount')
    payment_date = models.CharField(max_length=200, null=True, blank=True,verbose_name='Payment Date')
    payment_type = models.CharField(max_length=200, null=True, blank=True,verbose_name='Payment Type')
    payment_confirmation = models.CharField(max_length=200, null=True, blank=True,verbose_name='Payment Confirmation')
    
    status = models.CharField(max_length=200,choices=STATUS_CHOICES,default="ACTIVE")
    date_time = models.DateTimeField(auto_created=True, auto_now_add=True,verbose_name='Modified Date')

    total_price_2 = models.CharField(max_length=200, null=True, blank=True,verbose_name='Total price Old')
    delivered_value_2 = models.CharField(max_length=200, null=True, blank=True,verbose_name='Delivered Value Old')

    def __str__(self):
        return f'{self.grower.name} | {self.crop}'


class NasdaqApiData(models.Model):
    date_api = models.DateField(null=True, blank=True)
    close_value_api = models.CharField(max_length=200, null=True, blank=True)


class GrowerPayee(models.Model):
    grower = models.ForeignKey(Grower, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Grower Payee')
    field = models.ForeignKey(Field, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Grower Field')
    grower_namee = models.CharField(max_length=200, null=True, blank=True)
    grower_idd = models.CharField(max_length=200, null=True, blank=True)
    field_namee = models.CharField(max_length=200, null=True, blank=True)
    field_idd = models.CharField(max_length=200, null=True, blank=True)
    crop = models.CharField(max_length=200, null=True, blank=True)
    payee_entity_name = models.CharField(max_length=200, null=True, blank=True)
    payee_tax_id = models.CharField(max_length=200, null=True, blank=True)
    payee_physical_address = models.TextField(null=True, blank=True)
    payee_mailing_address = models.TextField(null=True, blank=True)
    payee_phone = models.CharField(max_length=200, null=True, blank=True)
    payee_email = models.CharField(max_length=200, null=True, blank=True)
    lien_holder_status = models.CharField(max_length=200, null=True, blank=True)
    payment_split_status = models.CharField(max_length=200, null=True, blank=True)
    net_payee = models.CharField(max_length=200, null=True, blank=True)


# class LienHolder(models.Model):
#     grower_payee = models.ForeignKey(GrowerPayee, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Lien Holder ')
#     lien_entity_name = models.CharField(max_length=200, null=True, blank=True)
#     lien_tax_id = models.CharField(max_length=200, null=True, blank=True)
#     lien_physical_address = models.CharField(max_length=200, null=True, blank=True)
#     lien_mailing_address = models.CharField(max_length=200, null=True, blank=True)
#     lien_contact_person = models.CharField(max_length=200, null=True, blank=True)
#     lien_phone = models.CharField(max_length=200, null=True, blank=True)
#     lien_email = models.CharField(max_length=200, null=True, blank=True)

class PaymentSplits(models.Model):
    grower_payee = models.ForeignKey(GrowerPayee, on_delete=models.CASCADE, null=True, blank=True)
    split_payee_name = models.CharField(max_length=200, null=True, blank=True)
    split_payee_tax_id = models.CharField(max_length=200, null=True, blank=True)
    split_payee_physical_address = models.TextField(null=True, blank=True)
    split_payee_mailing_address = models.TextField(null=True, blank=True)
    split_payee_contact_person = models.CharField(max_length=200, null=True, blank=True)
    split_payee_phone = models.CharField(max_length=200, null=True, blank=True)
    split_payee_email = models.CharField(max_length=200, null=True, blank=True)
    split_payee_percent = models.CharField(max_length=200, null=True, blank=True)
    split_payee_type = models.CharField(max_length=200, null=True, blank=True,verbose_name='Lien or Split')
