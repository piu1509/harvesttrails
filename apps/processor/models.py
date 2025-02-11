"""Database models for Processor"""
from concurrent.futures import process
from django.db import models
from django.utils import timezone
from apps.core.validate import validate_zipcode
from apps.grower.models import Grower
from apps.storage.models import Storage, StorageFeed
from apps.field.models import Field
from django.core.exceptions import ValidationError


class Processor(models.Model):
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
    gin_id = models.CharField(max_length=250, null=True, blank=True,verbose_name='Gin Id')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.entity_name

class ProcessorUser(models.Model):
    """Database model for processor User"""
    processor = models.ForeignKey(Processor, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Processor')
    contact_name = models.CharField(max_length=250, null=True, blank=True,verbose_name='Contact Name')
    contact_email = models.CharField(max_length=250, null=True, blank=True,verbose_name='Contact Email')
    contact_phone = models.CharField(max_length=250, null=True, blank=True,verbose_name='Contact Phone')
    contact_fax = models.CharField(max_length=250, null=True, blank=True,verbose_name='Contact Fax')
    p_password_raw = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return self.contact_email

class Location(models.Model):
    upload_choice = [
        ("shapefile", "Shapefile"),
        ("coordinates", "Coordinates"),
    ]
    processor = models.ForeignKey(Processor, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Processor')
    name =  models.CharField(max_length=250, null=True, blank=True,verbose_name='Location Name')
    upload_type = models.CharField(max_length=11,choices=upload_choice,verbose_name='Upload Type')
    shapefile_id = models.FileField(upload_to='processor_shapefile',null=True, blank=True,verbose_name='Shapefile ID')
    latitude = models.CharField(max_length=200,null=True, blank=True,verbose_name='Latitude')
    longitude = models.CharField(max_length=200,null=True, blank=True,verbose_name='Longitude')
    eschlon_id = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"Processor= {self.processor}, Location = {self.name}"

class LinkGrowerToProcessor(models.Model):
    processor = models.ForeignKey(Processor, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Processor')
    grower = models.ForeignKey(Grower, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Grower')

    def __str__(self):
        return f"Grower = {self.grower.name}, Processor = {self.processor.entity_name}"

STATUS_CHOICES = (
    ("APPROVED", "APPROVED"),
    ("DISAPPROVED", "DISAPPROVED"),
    ("", ""),
)
# SENDER_CHOICES = (
#     ("", ""),
#     ("Grower", "Grower"),
#     ("Processor", "Processor"),
# )

class GrowerShipmentFile(models.Model):
    # file = models.FileField(upload_to='uploads_grower_shipment/')
    file = models.FileField(upload_to='grower_shipment_file',null=True, blank=True,verbose_name='Shipmentfile ID')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.file.name
    
LBS_TO_BU_CONVERSION = 56

class GrowerShipment(models.Model):
    processor = models.ForeignKey(Processor, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Processor')
    grower = models.ForeignKey(Grower, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Grower')
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Storage')
    field = models.ForeignKey(Field, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Field')
    crop = models.CharField(max_length=200, null=True, blank=True,verbose_name='Select Item')
    variety = models.CharField(max_length=200, null=True, blank=True,verbose_name='Select Variety')
    amount = models.CharField(max_length=200, null=True, blank=True,verbose_name='Amount')
    amount2 = models.CharField(max_length=200, null=True, blank=True,verbose_name='Amount2')
    sustainability_score = models.CharField(max_length=200, null=True, blank=True,verbose_name='Sustainability Score')
    echelon_id = models.CharField(max_length=200, null=True, blank=True,verbose_name='Echelon Id')
    date_time = models.DateTimeField(auto_created=True, auto_now_add=True,verbose_name='Shipment Date')
    shipment_id = models.CharField(max_length=200, null=True, blank=True,verbose_name='Shipment Id')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Location')
    date_time_location = models.DateTimeField(auto_created=True, auto_now_add=True,verbose_name='Location Date')
    process_amount = models.CharField(max_length=200, null=True, blank=True,verbose_name='Processed Amount')
    process_date = models.DateField(auto_created=True, auto_now_add=True,verbose_name='Processed Date')
    process_time = models.TimeField(auto_created=True, auto_now_add=True,verbose_name='Processed Time')
    sku = models.CharField(max_length=200, null=True, blank=True,verbose_name='SKU ID')
    module_number = models.CharField(max_length=200, null=True, blank=True,verbose_name='Module Tag #')
    unit_type = models.CharField(max_length=200, null=True, blank=True,verbose_name='Unit Type')
    unit_type2 = models.CharField(max_length=200, null=True, blank=True,verbose_name='Unit Type2')
    total_amount = models.CharField(max_length=200, null=True, blank=True,verbose_name='Total Amount')
    received_amount = models.CharField(max_length=200, null=True, blank=True,verbose_name='Received Amount')
    token_id = models.CharField(max_length=200, null=True, blank=True,verbose_name='Token Id')
    approval_date = models.DateField(verbose_name='Approval Date', null=True, blank=True)
    status = models.CharField(max_length=200,choices=STATUS_CHOICES,default="")
    #30-02-23
    reason_for_disapproval = models.CharField(max_length=200, null=True, blank=True,verbose_name='Reason For Disapproval')
    moisture_level = models.CharField(max_length=200, null=True, blank=True,verbose_name='Moisture Level')
    fancy_count = models.CharField(max_length=200, null=True, blank=True,verbose_name='Fancy Count')
    head_count = models.CharField(max_length=200, null=True, blank=True,verbose_name='Head Count')
    bin_location_processor = models.CharField(max_length=200, null=True, blank=True,verbose_name='Bin Location at Processor')
    files = models.ManyToManyField(GrowerShipmentFile, related_name='growershipments', blank=True)
    processor2_idd = models.CharField(max_length=200, null=True, blank=True)
    processor2_name = models.CharField(max_length=250, null=True, blank=True)
    qr_code = models.FileField(upload_to='qr_code/',null=True, blank=True)
    # lot_number = models.CharField(max_length=200, null=True, blank=True)
    # volume_shipped = models.CharField(max_length=200, null=True, blank=True)
    # sender = models.CharField(max_length=200,choices=SENDER_CHOICES,default="")
    
    class Meta:
        ordering = ('-date_time',)

    def __str__(self):
        return f"Shipment Id = {self.shipment_id}, Grower = {self.grower.name}, Processor = {self.processor.entity_name}"
    
    def save(self, *args, **kwargs):
        """
        Override the save method to validate the total_amount and update the final_quantity in StorageFeed.
        """
        if self.storage:
            total_amount_lbs = float(self.total_amount)
            try:
                storage_feed = StorageFeed.objects.filter(storage=self.storage).last()
                if storage_feed:
                    if storage_feed.unit == "BU":
                        total_amount_in_bu = total_amount_lbs / LBS_TO_BU_CONVERSION
                        if total_amount_in_bu > float(storage_feed.final_quantity):
                            raise ValidationError(
                                f"The total amount ({total_amount_in_bu} BU) exceeds the available final quantity ({storage_feed.final_quantity} BU) in the storage feed."
                            )
                        # Deduct the amount from storage
                        new_final_quantity = float(storage_feed.final_quantity) - total_amount_in_bu
                    else:
                        if total_amount_lbs > float(storage_feed.final_quantity):
                            raise ValidationError(
                                f"The total amount ({total_amount_lbs} LBS) exceeds the available final quantity ({storage_feed.final_quantity} LBS) in the storage feed."
                            )
                        # Deduct the amount from storage
                        new_final_quantity = float(storage_feed.final_quantity) - total_amount_lbs

                    storage_feed.final_quantity = new_final_quantity
                    storage_feed.save()
                else:
                    pass
            except StorageFeed.DoesNotExist:
                raise ValidationError(f"StorageFeed does not exist for the selected storage: {self.storage}")

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Override the delete method to add the total_amount back to the final_quantity in StorageFeed.
        """
        if self.storage:
            total_amount_lbs = float(self.total_amount)
            try:
                storage_feed = StorageFeed.objects.filter(storage=self.storage).last()

                if storage_feed.unit == "BU":
                    total_amount_in_bu = total_amount_lbs / LBS_TO_BU_CONVERSION
                    # Add the amount back to storage
                    storage_feed.final_quantity = float(storage_feed.final_quantity) + total_amount_in_bu
                else:
                    # Add the amount back to storage
                    storage_feed.final_quantity = float(storage_feed.final_quantity) + total_amount_lbs

                storage_feed.save()

            except StorageFeed.DoesNotExist:
                raise ValidationError(f"StorageFeed does not exist for the selected storage: {self.storage}")

        super().delete(*args, **kwargs)

class ClassingReport(models.Model):
    processor = models.ForeignKey(Processor, on_delete=models.CASCADE, null=True, blank=True)
    grower = models.ForeignKey(Grower, on_delete=models.CASCADE, null=True, blank=True)
    csv_path = models.FileField(upload_to='processor_reports',null=True, blank=True,verbose_name='Classing Report CSV')
    executed = models.CharField(max_length=200, null=True, blank=True,default='No')
    csv_type = models.CharField(max_length=200, null=True, blank=True)
    upload_date = models.DateField(null=True, blank=True)

class ProductionReport(models.Model):
    uploaded_date = models.DateField(null=True, blank=True)
    processor = models.ForeignKey(Processor, on_delete=models.CASCADE, null=True, blank=True,verbose_name='Select Processor')
    csv_path = models.FileField(upload_to='processor_reports',null=True, blank=True,verbose_name='Classing Report CSV')
    executed = models.CharField(max_length=200, null=True, blank=True,default='No')
    
    class Meta:
        ordering = ('-uploaded_date',)


class BaleReportFarmField(models.Model):
    classing = models.ForeignKey(ClassingReport, on_delete=models.CASCADE,null=True, blank=True)
    prod_id = models.CharField(max_length=200, null=True, blank=True)
    bale_id = models.CharField(max_length=200, null=True, blank=True)
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
    ob2 = models.CharField(max_length=200, null=True, blank=True, verbose_name='grower id')
    ob3 = models.CharField(max_length=200, null=True, blank=True, verbose_name='grower name')
    ob4 = models.CharField(max_length=200, null=True, blank=True, verbose_name='field id')
    ob5 = models.CharField(max_length=200, null=True, blank=True, verbose_name='certificate')
    value = models.CharField(max_length=200, null=True, blank=True)
    level = models.CharField(max_length=200, null=True, blank=True)
    crop_variety = models.CharField(max_length=200, null=True, blank=True)
    upload_date = models.DateField(null=True, blank=True)
    # def getPaymentTablejson(self):
    #     bale = BaleReportFarmField.objects.get(id=self.id)
    #     certificate = bale.certificate()
    #     level = bale.get_check()
    #     return {
    #         "id":self.id,
    #         "prod_id":self.prod_id,
    #         "farm_name":self.farm_name,
    #         "grower_name":self.classing.grower.name,
    #         "bale_id":self.bale_id,
    #         "warehouse_wt":self.warehouse_wt,
    #         "dt_class":self.dt_class,
    #         "net_wt":self.net_wt,
    #         "field_name":self.field_name,
    #         "certificate":certificate,
    #         "level":level,
    #         "value":self.value,
    #         "csv_type":self.classing.csv_type,
    #     }

    def certificate(self):
        grower_name = self.classing.grower.name
        grower = Grower.objects.filter(name=grower_name)
        if grower.count() > 0:
            grower_id = [i.id for i in grower]
        else:
            grower_id = ''
        field = Field.objects.filter(name=self.field_name).filter(grower_id__in=grower_id)
        if field.count() > 0:
            survey1 = [i.get_survey1() for i in field][0]
            survey2 = [i.get_survey2() for i in field][0]
            survey3 = [i.get_survey3() for i in field][0]
            # print(survey1,survey2,survey3)
            if survey1 != '':
                var1 = survey1
            else:
                var1 = 0
            if survey2 != '':
                var2= survey2
            else:
                var2 = 0
            if survey3 != '':
                var3= survey3
            else:
                var3 = 0

            composite_score = (float(var1) * 0.25) + (float(var2) * 0.50) + (float(var3) * 0.25)
            
            if composite_score >= 75:
                certificate = "Pass"
            elif composite_score < 75 :
                certificate = "Fail"
        else:
            certificate = 'N/A'

        return certificate

    #checking 
    def get_check(self):
        check_lst = []
        bale = BaleReportFarmField.objects.get(id=self.id)
        # Color — CGR
        clr = bale.cgr
        if clr != 'nan':
            # clr = int(float(bale.cgr[:2]))
            clr_var = clr.split('-')
            clr1 = int(float(clr_var[0]))
            #if clr1 >= 11 and clr1 <= 21 :
            if clr1 == 11 or clr1 == 21 :
                check_lst.append('gold')
            elif clr1 == 31 :
                check_lst.append('silver')
            elif clr1 == 41 :
                check_lst.append('bronze')
            else:
                check_lst.append('0')
        else:
            clr = 'nan'
        # clr = bale.cgr
        # if clr != 'nan':
        #     clr = int(float(bale.cgr[:2]))
        #     if clr <= 21 :
        #         check_lst.append('gold')
        #     elif clr <= 31 and clr >21 :
        #         check_lst.append('silver')
        #     elif clr <= 41 and clr >31 :
        #         check_lst.append('bronze')
        #     else:
        #         check_lst.append('0')
        # else:
        #     clr = 'nan'

        # Leaf — LF
        llf = bale.lf
        if llf != 'nan':
            llf = int(bale.lf[0])
            if llf <= 2 :
                check_lst.append('gold')
            elif llf <= 3 and llf > 2 :
                check_lst.append('silver')
            elif llf <= 4 and llf > 3 :
                check_lst.append('bronze')
            else:
                check_lst.append('0')
        else:
            llf = 'nan'

        # Staple — MIC
        stap = bale.st
        if stap != 'nan':
            stap = float(bale.st)
            if stap >= 43 :
                check_lst.append('Llano Super')
            elif stap >= 38 and stap < 43 :
                check_lst.append('gold')
            elif stap >= 37 and stap < 38 :
                check_lst.append('silver')
            elif stap >= 36 and stap < 37 :
                check_lst.append('bronze')
            else:
                check_lst.append('0')
        else:
            stap = 'nan'

        # Strength — STR
        streng = bale.str_no
        if streng != 'nan':
            streng = float(bale.str_no)
            if streng >= 33 :
                check_lst.append('gold')
            elif streng >= 31 and streng < 33 :
                check_lst.append('silver')
            elif streng >= 29 and streng < 31 :
                check_lst.append('bronze')
            else:
                check_lst.append('0')
        else:
            streng = 'nan'

        # Mic — TR
        trmic = bale.mic
        if trmic !='nan':
            trmic = float(bale.mic)
            if trmic >= 3.7 and trmic <4.3 :
                check_lst.append('gold')
            else:
                check_lst.append('0')
        else:
            trmic = 'nan'

        # Uniformity  — UNIF
        uniformi = bale.unif
        if uniformi != 'nan':
            uniformi = float(bale.unif)
            if uniformi >= 82 :
                check_lst.append('gold')
            elif uniformi >= 81 and uniformi < 82 :
                check_lst.append('silver')
            elif uniformi >= 80 and uniformi < 81 :
                check_lst.append('bronze')
            else:
                check_lst.append('0')
        else:
            uniformi = 'nan'

        lls = check_lst.count('Llano Super')
        gg = check_lst.count('gold')
        ss = check_lst.count('silver')
        bb = check_lst.count('bronze')
        zz = check_lst.count('0')
        data = ["Llano Super :",lls,"gold :",gg,"silver :",ss,"bronze :",bb,"zero :",zz]
        if bale.rm != 'nan'  and bale.rm != '  ' and  bale.rm != None :
            level="None"

        elif bale.ex != 'nan'  and bale.ex != '  ' and  bale.ex != None :
            level="None"

        else:
            if gg>=3 and lls==1 :
                level="Llano Super"
            elif gg>=4 :
                level="Gold"
            elif lls+gg+ss>=4:
                level="Silver"
            elif lls+gg+ss+bb>=4:
                level="Bronze"
            else:
                level="None"
            
        # var = [check_lst,data,level]   
        return level

class CertificateCalc(models.Model):
    grower_id = models.CharField(max_length=200, null=True, blank=True)
    field_id = models.CharField(max_length=200, null=True, blank=True)
    certificate = models.CharField(max_length=200, null=True, blank=True)
    

class BaleReportProducer(models.Model):
    classing = models.ForeignKey(ClassingReport, on_delete=models.CASCADE,null=True, blank=True)
    prod_id = models.CharField(max_length=200, null=True, blank=True)
    farm_name = models.CharField(max_length=200, null=True, blank=True)
    sale_status = models.CharField(max_length=200, null=True, blank=True)
    wh_id = models.CharField(max_length=200, null=True, blank=True)
    bale_id = models.CharField(max_length=200, null=True, blank=True)
    gin_date = models.DateField(null=True, blank=True)
    net_wt = models.CharField(max_length=200, null=True, blank=True)
    farm_id = models.CharField(max_length=200, null=True, blank=True)
    load_id = models.CharField(max_length=200, null=True, blank=True)
    field_name = models.CharField(max_length=200, null=True, blank=True)
    pk_num = models.CharField(max_length=200, null=True, blank=True)
    gr = models.CharField(max_length=200, null=True, blank=True)
    lf = models.CharField(max_length=200, null=True, blank=True)
    st = models.CharField(max_length=200, null=True, blank=True)
    mic = models.CharField(max_length=200, null=True, blank=True)
    ex = models.CharField(max_length=200, null=True, blank=True)
    rm = models.CharField(max_length=200, null=True, blank=True)
    str_no = models.CharField(max_length=200, null=True, blank=True)
    cgr = models.CharField(max_length=200, null=True, blank=True)
    rd = models.CharField(max_length=200, null=True, blank=True)
    ob1 = models.CharField(max_length=200, null=True, blank=True)
    tr = models.CharField(max_length=200, null=True, blank=True)
    unif = models.CharField(max_length=200, null=True, blank=True)
    len_num = models.CharField(max_length=200, null=True, blank=True)
    elong = models.CharField(max_length=200, null=True, blank=True)
    ob2 = models.CharField(max_length=200, null=True, blank=True)
    ob3 = models.CharField(max_length=200, null=True, blank=True)
    ob4 = models.CharField(max_length=200, null=True, blank=True)
    ob5 = models.CharField(max_length=200, null=True, blank=True)
    value = models.CharField(max_length=200, null=True, blank=True)

    #checking 
    def get_check(self):
        check_lst = []
        bale = BaleReportProducer.objects.get(id=self.id)
        # Color — CGR
        clr = bale.cgr
        if clr !='nan':
            clr = bale.cgr.split("-")
            clr = int(float(clr[0]))
            # clr = int(float(bale.cgr[:2]))
            if clr <= 21 :
                check_lst.append('gold')
            elif clr <= 31 and clr >21 :
                check_lst.append('silver')
            elif clr <= 41 and clr >31 :
                check_lst.append('bronze')
            else:
                check_lst.append('0')
        else:
            clr = 'nan'

        # Leaf — LF
        llf = bale.lf
        if llf !='nan':
            llf = int(bale.lf[0])
            if llf <= 2 :
                check_lst.append('gold')
            elif llf <= 3 and llf > 2 :
                check_lst.append('silver')
            elif llf <= 4 and llf > 3 :
                check_lst.append('bronze')
            else:
                check_lst.append('0')
        else:
            llf = 'nan'

        # Staple — MIC
        stap = bale.st
        if stap !='nan':
            stap = float(bale.st)
            if stap >= 43 :
                check_lst.append('Llano Super')
            elif stap >= 38 and stap < 43 :
                check_lst.append('gold')
            elif stap >= 37 and stap < 38 :
                check_lst.append('silver')
            elif stap >= 36 and stap < 37 :
                check_lst.append('bronze')
            else:
                check_lst.append('0')
        else:
            stap = 'nan'

        # Strength — STR
        streng = bale.str_no
        if streng !='nan':
            streng = float(bale.str_no)
            if streng >= 33 :
                check_lst.append('gold')
            elif streng >= 31 and streng < 33 :
                check_lst.append('silver')
            elif streng >= 29 and streng < 31 :
                check_lst.append('bronze')
            else:
                check_lst.append('0')
        else:
            streng = 'nan'

        # Mic — TR
        trmic = bale.mic
        if trmic !='nan':
            trmic = float(bale.mic)
            if trmic >= 3.7 and trmic <4.3 :
                check_lst.append('gold')
            else:
                check_lst.append('0')
        else:
            trmic = 'nan'

        # Uniformity  — UNIF
        uniformi = bale.unif
        if uniformi !='nan':
            uniformi = float(bale.unif)
            if uniformi >= 82 :
                check_lst.append('gold')
            elif uniformi >= 81 and uniformi < 82 :
                check_lst.append('silver')
            elif uniformi >= 80 and uniformi < 81 :
                check_lst.append('bronze')
            else:
                check_lst.append('0')
        else:
            uniformi = 'nan'

        lls = check_lst.count('Llano Super')
        gg = check_lst.count('gold')
        ss = check_lst.count('silver')
        bb = check_lst.count('bronze')
        zz = check_lst.count('0')
        data = ["Llano Super :",lls,"gold :",gg,"silver :",ss,"bronze :",bb,"zero :",zz]
        if gg>=3 and lls==1 :
            level="Llano Super"
        elif gg>=4 :
            level="Gold"
        elif gg+ss>=4:
            level="Silver"
        elif gg+ss+bb>=4:
            level="Bronze"
        else:
            level="None"
            
        # var = [check_lst,data,level]   
        return level



class GinReportbyday(models.Model):
    production = models.ForeignKey(ProductionReport, on_delete=models.CASCADE,null=True, blank=True)
    date = models.CharField(max_length=200, null=True, blank=True)
    load_id = models.CharField(max_length=200, null=True, blank=True)
    prod_id = models.CharField(max_length=200, null=True, blank=True)
    farm_id = models.CharField(max_length=200, null=True, blank=True)
    field_name = models.CharField(max_length=200, null=True, blank=True)
    pk_num = models.CharField(max_length=200, null=True, blank=True)
    variety = models.CharField(max_length=200, null=True, blank=True)
    tm = models.CharField(max_length=200, null=True, blank=True)
    module_amount = models.CharField(max_length=200, null=True, blank=True)
    truck_id = models.CharField(max_length=200, null=True, blank=True)
    made_date = models.CharField(max_length=200, null=True, blank=True)
    delivery_date = models.CharField(max_length=200, null=True, blank=True)
    gin_date = models.CharField(max_length=200, null=True, blank=True)
    bc = models.CharField(max_length=200, null=True, blank=True)
    cotton_seed = models.CharField(max_length=200, null=True, blank=True)
    lint = models.CharField(max_length=200, null=True, blank=True)
    seed = models.CharField(max_length=200, null=True, blank=True)
    turnout = models.CharField(max_length=200, null=True, blank=True)
    bale_tot = models.CharField(max_length=200, null=True, blank=True)


class GinLoadBalebydate(models.Model):
    gin_date = models.CharField(max_length=200, null=True, blank=True)
    load_id = models.CharField(max_length=200, null=True, blank=True)
    bale_id = models.CharField(max_length=200, null=True, blank=True)
    net_wt = models.CharField(max_length=200, null=True, blank=True)


class ProductionManagement(models.Model):
    processor = models.ForeignKey(Processor, on_delete=models.CASCADE, null=True, blank=True)
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



EquipmentType = (
    ("Truck", "Truck"),
    ("Hopper Car", "Hopper Car"),
    ("Rail Car", "Rail Car"),
)
unit_choice = [
    ("LBS","LBS"),
    ("BU","BU"),
]



class File(models.Model):
    # file = models.FileField(upload_to='uploads_shipment/')
    file = models.FileField(upload_to='processor_shipment_files', null=True, blank=True, verbose_name="ProcessorShipment Id")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.file.name

