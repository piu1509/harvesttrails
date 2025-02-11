from datetime import datetime
from django.db import models
from django.urls import reverse
from django.utils import timezone
from apps.contracts.models import SignedContracts
from apps.farms.models import Farm
from apps.grower.models import Grower, Consultant
from apps.storage.models import Storage, ShapeFileDataCo as storageshapfile
from apps.growersurvey.models import SustainabilitySurvey,TypeSurvey,NameSurvey
from apps.documents.models import DocumentFile, DocumentFolder

from .choices import CHOICE
from django.contrib.postgres.fields import ArrayField, JSONField

class Field(models.Model):
    """Database model for field"""
    name = models.CharField(unique=True, max_length=200)
    farm = models.ForeignKey(
        'farms.Farm', on_delete=models.CASCADE, related_name='fields'
    )
    grower = models.ForeignKey(
        'grower.Grower', on_delete=models.CASCADE)
    batch_id = models.IntegerField(null=True, blank=True)
    acreage = models.FloatField()
    fsa_farm_number = models.CharField(
        max_length=250,help_text="Multiple values can be Comma (,) separated", null=True, blank=True,
        verbose_name='FSA Farm Number')
    fsa_tract_number = models.CharField(
        max_length=250,help_text="Multiple values can be Comma (,) separated", null=True, blank=True,
        verbose_name='FSA Tract Number')
    fsa_field_number = models.CharField(
        max_length=250,help_text="Multiple values can be Comma (,) separated", null=True, blank=True,
        verbose_name='FSA Field Number')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    crop = models.CharField(max_length=255, choices=CHOICE.CROP_CHOICES, null=True, blank=True)
    variety = models.CharField(
        max_length=255, choices=CHOICE.VARIETY_CHOICES, null=True, blank=True
    )
    yield_per_acre = models.FloatField(null=True, blank=True, verbose_name='Yield Per Acre')
    total_yield = models.FloatField(null=True, blank=True, verbose_name='Total Yield')
    crop_tech = models.CharField(max_length=200, blank=True, null=True, verbose_name='Crop Tech')
    burndown_chemical = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Burndown Chemical'
    )
    burndown_chemical_date = models.DateField(
        null=True, blank=True, verbose_name='Burndown Chemical Date'
    )
    plant_date = models.DateField(null=True, blank=True, verbose_name='Plant Date')
    preemergence_chemical = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name='Preemergence Chemical'
    )
    preemergence_chemical_date = models.DateField(
        null=True, blank=True,
        verbose_name='Preemergence Chemical Date'
    )
    stand_count = models.IntegerField(null=True, blank=True, verbose_name='Stand Count')
    emergence_date = models.DateField(
        null=True, blank=True, verbose_name='Emergence Date'
    )
    post_emergence_chemical_1 = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name='Post Emergence Chemical 1'
    )
    post_emergence_chemical_1_date = models.DateField(
        null=True, blank=True,
        verbose_name='Post Emergence Chemical 1 Date'
    )
    post_emergence_chemical_2 = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name='Post Emergence Chemical 2'
    )
    post_emergence_chemical_2_date = models.DateField(
        null=True, blank=True,
        verbose_name='Post Emergence Chemical 2 Date'
    )
    post_emergence_chemical_3 = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name='Post Emergence Chemical 3'
    )
    post_emergence_chemical_3_date = models.DateField(
        null=True, blank=True,
        verbose_name='Post Emergence Chemical 3 Date'
    )
    post_emergence_chemical_4 = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name='Post Emergence Chemical 4'
    )
    post_emergence_chemical_4_date = models.DateField(
        null=True, blank=True, verbose_name='Post Emergence Chemical 4 Date'
    )
    flood_date = models.DateField(
        null=True, blank=True, verbose_name='Flood Date'
    )
    awd_drydown_date = models.DateField(
        null=True, blank=True, verbose_name='AWD Dry Down Date'
    )
    fungicide_micronutrients = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name='Fungicide Micronutrients'
    )
    fungicide_micronutrients_date = models.DateField(
        null=True, blank=True, verbose_name='Fungicide Micronutrients Date'
    )
    insecticide_application = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name='Insecticide Application'
    )
    insecticide_application_date = models.DateField(
        null=True, blank=True,
        verbose_name='Insecticide Application Date'
    )
    drain_date = models.DateField(null=True, blank=True, verbose_name='Drain Date')
    sodium_chlorate_date = models.DateField(
        null=True, blank=True,
        verbose_name='Sodium Chlorate Date'
    )
    harvest_date = models.DateField(
        null=True, blank=True, verbose_name='Harvest Date'
    )
    soil_sample_date = models.DateField(
        null=True, blank=True, verbose_name='Soil Sample Date'
    )
    litter = models.CharField(max_length=100, blank=True, null=True)
    pre_fert_rate = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Pre Fert Rate'
    )
    pre_fert_product = models.CharField(
        max_length=255, choices=CHOICE.FERT_PRODUCT_CHOICES,
        blank=True, null=True,
        verbose_name='Pre Fert Product'
    )
    early_post_fert_rate = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Early Post Fert Rate'
    )
    early_post_fert_product = models.CharField(
        max_length=255, choices=CHOICE.FERT_PRODUCT_CHOICES,
        blank=True, null=True,
        verbose_name='Early Post Fert Product'
    )
    early_post_fert_date = models.DateField(
        null=True, blank=True,
        verbose_name='Early Post_Fert Date'
    )
    foliar_fert_app_rate = models.FloatField(
        null=True, blank=True, verbose_name='Foliar Fert App Rate'
    )
    foliar_fert_app_product = models.CharField(
        max_length=100, choices=CHOICE.FERT_PRODUCT_CHOICES,
        blank=True, null=True,
        verbose_name='Foliar Fert App Product'
    )
    foliar_fert_app_date = models.DateField(
        null=True, blank=True,
        verbose_name='Foliar Fert App Date'
    )
    pre_flood_fert_rate = models.FloatField(
        null=True, blank=True,
        verbose_name='Pre Flood Fert Rate'
    )
    pre_flood_fert_product = models.CharField(
        max_length=255, choices=CHOICE.FERT_PRODUCT_CHOICES, 
        blank=True, null=True, verbose_name='Pre Flood Fert Product'
    )
    pre_flood_fert_date = models.DateField(
        null=True, blank=True,
        verbose_name='Pre Flood Fert Date'
    )
    post_flood_midseason_fert_rate = models.FloatField(
        null=True, blank=True,
        verbose_name='Post Flood Midseason Fert Rate'
    )
    post_flood_midseason_fert_product = models.CharField(
        max_length=255, choices=CHOICE.FERT_PRODUCT_CHOICES,
        blank=True, null=True, verbose_name='Post Flood Midseason Fert Product'
    )
    post_flood_midseason_fert_date = models.DateField(
        null=True, blank=True,
        verbose_name='Post Flood Midseason Fert Date'
    )
    post_flood_midseason_fert_rate2 = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Post Flood Midseason Fert Rate 2'
    )
    post_flood_midseason_fert_product2 = models.CharField(
        max_length=255, choices=CHOICE.FERT_PRODUCT_CHOICES,
        blank=True, null=True,
        verbose_name='Post Flood Midseason Fert Product 2'
    )
    post_flood_midseason_fert_date2 = models.DateField(
        null=True, blank=True,
        verbose_name='Post Flood Midseason Fert Date 2'
    )
    post_flood_midseason_fert_rate3 = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Post Flood Midseason Fert Rate 3'
    )
    post_flood_midseason_fert_product3 = models.CharField(
        max_length=255, choices=CHOICE.FERT_PRODUCT_CHOICES,
        blank=True, null=True,
        verbose_name='Post Flood Midseason Fert Product 3'
    )
    post_flood_midseason_fert_date3 = models.DateField(
        null=True, blank=True,
        verbose_name='Post Flood Midseason Fert Date 3'
    )
    boot_fertilizer_rate = models.PositiveIntegerField(
        help_text="Enter number greater than 0",
        null=True, blank=True,
        verbose_name='Boot Fertilizer Rate'
    )
    boot_fertilizer_product = models.CharField(
        max_length=255, choices=CHOICE.FERT_PRODUCT_CHOICES,
        blank=True, null=True, verbose_name='Boot Fertilizer Product'
    )
    boot_fertilizer_date = models.DateField(
        null=True, blank=True,
        verbose_name='Boot Fertilizer Date'
    )
    total_n_applied_lbs_ac = models.PositiveIntegerField(
        help_text="Enter number between 0 and 300",
        null=True, blank=True,
        verbose_name='Total N Applied lbs ac'
    )
    flow_meter_beginning_reading = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name='Flow Meter Beginning Reading'
    )
    flow_meter_multiplier = models.IntegerField(
        null=True, blank=True,
        verbose_name='Flow Meter Multiplier'
    )
    flow_meter_end_reading = models.FloatField(
        null=True, blank=True,
        verbose_name='Flow Meter End Reading'
    )
    water_source = models.CharField(
        max_length=100, choices=CHOICE.WATER_SOURCE_CHOICES,
        blank=True, null=True, verbose_name='Water Source'
    )
    total_n_applied = models.PositiveIntegerField(
        help_text="Enter number between 0 and 300",
        null=True, blank=True,
        verbose_name='Total N Applied'
    )
    measured_water_use = models.CharField(
        max_length=200, null=True, blank=True,
        verbose_name='Measured Water Use'
    )
    field_design_and_use_of_plastic_pipe = models.CharField(
        max_length=100,
        choices=CHOICE.FIELD_DESIGN_PLASTIC_USE_SOURCE_CHOICES,
        blank=True, null=True, verbose_name='Field Design And Use Of Plastic pipe'
    )
    soil_clay_percentage = models.FloatField(
        help_text="Enter a number between 0 to 45 if clay '%'\
            is greater than 45 value should be adjusted to 45'%'",
                null=True, blank=True, verbose_name='Soil Clay Percentage'
    )
    previous_crop = models.CharField(
        max_length=100,
        blank=True, null=True, verbose_name='Previous Crop'
    )
    straw_burnt_or_residue_removed = models.CharField(
        max_length=100,
        choices=CHOICE.STRAW_BURNT_REMOVED_CHOICES, blank=True, null=True,
        verbose_name='Straw Burnt Or Residue Removed'
    )
    straw_residue_tillage_and_cover_crop_management = models.CharField(
        max_length=100,
        choices=CHOICE.RESIDUE_TILLAGE_CROP_MGMT_CHOICES, blank=True, null=True,
        verbose_name='Straw Residue Tillage And Cover Crop Management'
    )
    tillage_equipment_and_passes_or_fuel_usage_for_tillage = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name='Tillage Equipment And Passes Or Fuel Usage For Tillage'
    )
    eschlon_id = models.CharField(max_length=200, null=True, blank=True, verbose_name='Echelon Id')
    water_saving = models.IntegerField(null=True, blank=True, verbose_name='Water Saving')
    created_date = models.DateTimeField(blank=True, default=timezone.now, verbose_name='Created Date')
    modified_date = models.DateTimeField(auto_now=True, verbose_name='Modified Date')
    # 12-12-22
    gal_water_saved = models.CharField(max_length=200, null=True, blank=True)
    water_lbs_saved = models.CharField(max_length=200, null=True, blank=True)
    co2_eq_reduced = models.CharField(max_length=200, null=True, blank=True)
    increase_nitrogen = models.CharField(max_length=200, null=True, blank=True)
    ghg_reduction = models.CharField(max_length=200, null=True, blank=True)
    land_use_efficiency = models.CharField(max_length=200, null=True, blank=True)
    grower_premium_percentage = models.CharField(max_length=200, null=True, blank=True)
    grower_dollar_premium = models.CharField(max_length=200, null=True, blank=True)
    

        
        
    


    def __str__(self):
        """Returns string representation of farm"""
        #return f'{self.id}:{self.name}'
        return f'{self.name}'

    def field_center_coordinates(self):
        """method to return the latitude and longitude together as field center coordinates"""
        return f'{self.latitude} , {self.longitude}'

    def get_fields(self):
        """This method return all the field name and their value of all objects of field model."""
        return [(field.name, field.value_from_object(self)) for field in self.__class__._meta.fields]

    def get_grower(self):
        field = Field.objects.get(id=self.id)
        grower_id = field.grower_id
        grower_name = Grower.objects.get(id=grower_id)
        return grower_name.name
    
    def get_farms(self):
        field = Field.objects.get(id=self.id)
        farm_id = field.farm_id
        farm_name = Farm.objects.get(id=farm_id)
        return farm_name.name

    def get_contract(self):
        field = Field.objects.get(id=self.id)
        grower_id = field.grower
        signed_contracts = SignedContracts.objects.filter(grower_id=grower_id)
        if signed_contracts.count()!=0:
            return "Yes"
        else:
            return "No"

    def get_consultant_name(self):
        consultant_name = ''
        field = Field.objects.get(id=self.id)
        grower_id = field.grower_id
        obj = Grower.objects.get(id=grower_id)
        consultant_obj = obj.consultant.all()
        for i in consultant_obj:
            consultant_name = i.name
        return consultant_name

    def get_field_shapefile(self):
        shapeFile = ShapeFileDataCo.objects.filter(field_id=self.id)
        if shapeFile.count() != 0:
            return 'Yes'
        else:
            return 'No'
    def get_storage_shapefile(self):
        field = Field.objects.get(id=self.id)
        grower_id = field.grower_id
        storage_shap = Storage.objects.filter(grower_id=grower_id)
        
        storage_shapfile = storageshapfile.objects.filter(storage__in=storage_shap)
        if storage_shapfile.count() != 0:
            return 'Yes'
        else:
            return 'No'

    def get_survey1(self):
        field = Field.objects.get(id=self.id)
        grower_id = field.grower_id
        surveyscore = ''
        if field.crop == 'RICE':
            typesurvey = 'Entry Survey - Rice'
        elif field.crop == 'COTTON':
            typesurvey = 'Entry Survey - Cotton'
        
        else:
            typesurvey = ''
        
        if typesurvey != '':
            typenew = TypeSurvey.objects.get(name=typesurvey)
            namesurvey_id = NameSurvey.objects.get(typesurvey_id=typenew.id)
            sustainability_survey = SustainabilitySurvey.objects.filter(grower_id=grower_id).filter(namesurvey_id=namesurvey_id).filter(field_id=field.id)
            for i in sustainability_survey:
                surveyscore = i.sustainabilityscore
                if surveyscore > 100:
                    surveyscore = 100
                else:
                    surveyscore = surveyscore
                
            return surveyscore
        else:
            return 0

    def get_survey2(self):
            field = Field.objects.get(id=self.id)
            grower_id = field.grower_id
            surveyscore = ''
            if field.crop == 'RICE':
                typesurvey = 'NEW - In Season Survey - Rice'
            elif field.crop == 'COTTON':
                typesurvey = 'Cotton Survey 2 In Season'
            else:
                typesurvey = ''
            if typesurvey != '':
                typenew = TypeSurvey.objects.get(name=typesurvey)
                namesurvey_id = NameSurvey.objects.get(typesurvey_id=typenew.id)
                sustainability_survey = SustainabilitySurvey.objects.filter(grower_id=grower_id).filter(namesurvey_id=namesurvey_id).filter(field_id=field.id)
                for i in sustainability_survey:
                    surveyscore = i.sustainabilityscore
                    if surveyscore > 100:
                        surveyscore = 100
                    else:
                        surveyscore = surveyscore
                return surveyscore
            else:
                return 0

    def get_survey3(self):
            field = Field.objects.get(id=self.id)
            grower_id = field.grower_id
            surveyscore = ''
            if field.crop == 'RICE':
                typesurvey = 'Rice Survey 3 End of Season'
            elif field.crop == 'COTTON':
                typesurvey = 'Cotton Survey 3 End of Season'

            else:
                typesurvey = ''
            
            if typesurvey != '':
                typenew= TypeSurvey.objects.get(name=typesurvey)
                namesurvey_id = NameSurvey.objects.get(typesurvey_id=typenew.id)
                sustainability_survey = SustainabilitySurvey.objects.filter(grower_id=grower_id).filter(namesurvey_id=namesurvey_id).filter(field_id=field.id)
                for i in sustainability_survey:
                    surveyscore = i.sustainabilityscore
                    if surveyscore > 100:
                        surveyscore = 100
                    else:
                        surveyscore = surveyscore
                return surveyscore
            else:
                return 0

    def get_composite_score(self):
        surveyscore1 = 0
        surveyscore2 = 0
        surveyscore3 = 0
        field = Field.objects.get(id=self.id)
        grower_id = field.grower_id
        surveyscore = ''
        if field.crop == 'RICE':
            typesurvey1 = 'Entry Survey - Rice'
            typesurvey2 = 'NEW - In Season Survey - Rice'
            typesurvey3 = 'Rice Survey 3 End of Season'

        elif field.crop == 'COTTON':
            typesurvey1 = 'Entry Survey - Cotton'
            typesurvey2 = 'Cotton Survey 2 In Season'
            typesurvey3 = 'Cotton Survey 3 End of Season'
        
        else:
            typesurvey1 = ''
            typesurvey2 = ''
            typesurvey3 = ''
        
        if typesurvey1 != '' and typesurvey2 != '' and typesurvey3 != '':
            type1= TypeSurvey.objects.get(name=typesurvey1)
            type2= TypeSurvey.objects.get(name=typesurvey2)
            type3= TypeSurvey.objects.get(name=typesurvey3)

            namesurvey_id1 = NameSurvey.objects.get(typesurvey_id=type1.id)
            namesurvey_id2 = NameSurvey.objects.get(typesurvey_id=type2.id)
            namesurvey_id3 = NameSurvey.objects.get(typesurvey_id=type3.id)

            sustainability_survey1 = SustainabilitySurvey.objects.filter(grower_id=grower_id).filter(namesurvey_id=namesurvey_id1).filter(field_id=field.id)
            sustainability_survey2 = SustainabilitySurvey.objects.filter(grower_id=grower_id).filter(namesurvey_id=namesurvey_id2).filter(field_id=field.id)
            sustainability_survey3 = SustainabilitySurvey.objects.filter(grower_id=grower_id).filter(namesurvey_id=namesurvey_id3).filter(field_id=field.id)
            
            for i in sustainability_survey1:
                surveyscore1 = i.sustainabilityscore

            if surveyscore1 != None:
                if surveyscore1 > 100 :
                    surveyscore1 = 100
                else:
                    surveyscore1 = surveyscore1
            else:
                surveyscore1 = 0

            for i in sustainability_survey2:
                surveyscore2 = i.sustainabilityscore
            
            if surveyscore2 != None:
                if surveyscore2 > 100 :
                    surveyscore2 = 100
                else:
                    surveyscore2 = surveyscore2
            else:
                surveyscore2 = 0
            
            
            for i in sustainability_survey3:
                surveyscore3 = i.sustainabilityscore
            
            if surveyscore3 != None:
                if surveyscore3 > 100 :
                    surveyscore3 = 100
                else:
                    surveyscore3 = surveyscore3
            else:
                surveyscore3 = 0
            
            return round((surveyscore1*0.25)+(surveyscore2*0.50)+(surveyscore3*0.25),2)

        else:
            return 0

    def get_tissue_1(self):
        field = Field.objects.get(id=self.id)
        grower_id = field.grower_id
        doc_folder = DocumentFolder.objects.get(name='Tissue Samples 1')
        doc_file = DocumentFile.objects.filter(folder_id=doc_folder).filter(field_id=self.id).filter(grower_id=grower_id)
        return doc_file.count()

    def get_tissue_2(self):
        field = Field.objects.get(id=self.id)
        grower_id = field.grower_id
        doc_folder = DocumentFolder.objects.get(name='Tissue Samples 2')
        doc_file = DocumentFile.objects.filter(folder_id=doc_folder).filter(field_id=self.id).filter(grower_id=grower_id)
        return doc_file.count()

    
    def get_tissue_3(self):
        field = Field.objects.get(id=self.id)
        grower_id = field.grower_id
        doc_folder = DocumentFolder.objects.get(name='Tissue Samples 3')
        doc_file = DocumentFile.objects.filter(folder_id=doc_folder).filter(field_id=self.id).filter(grower_id=grower_id)
        return doc_file.count()

    def get_water(self):
        field = Field.objects.get(id=self.id)
        grower_id = field.grower_id
        doc_folder = DocumentFolder.objects.get(name='Water Samples')
        doc_file = DocumentFile.objects.filter(folder_id=doc_folder).filter(field_id=self.id).filter(grower_id=grower_id)
        return doc_file.count()

    def get_soil(self):
        field = Field.objects.get(id=self.id)
        grower_id = field.grower_id
        doc_folder = DocumentFolder.objects.get(name='Soil Samples')
        doc_file = DocumentFile.objects.filter(folder_id=doc_folder).filter(field_id=self.id).filter(grower_id=grower_id)
        return doc_file.count()

    @property
    def get_polydata_count(self):
        data_count = ShapeFileDataCo.objects.filter(field=self).count()
        return data_count


class CsvToField(models.Model):
    '''For storing CSV file
    import functionality for creating Fields'''

    csv_file = models.FileField(upload_to='CSV', null=False)

    def get_absolute_url(self):
        '''For returning url after storing file'''
        return reverse("csv-field-mapping", kwargs={"pk": self.pk})

class ShapeFileDataCo(models.Model):
    coordinates = models.JSONField(default=list)
    field = models.ForeignKey(Field, on_delete=models.CASCADE, null=True, blank=True)
    # eos_fieldId = models.BigIntegerField(null=True, blank=True)
    # lat_lon_coord = models.CharField(max_length=255, blank=True, null=True)
    # bbox_coord = models.JSONField(default=list)


# 19-06-23
crop_year = (
    ("2022", "2022"),
    ("2023", "2023"),
)
class FieldUpdated(models.Model):
    """Database model for field"""
    field = models.ForeignKey(Field,on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=200,null=True,blank=True)
    crop_year = models.CharField(max_length = 20,choices = crop_year,default = '2022',null=True,blank=True)
    # 14-11-23
    farm = models.ForeignKey(
        'farms.Farm', on_delete=models.CASCADE, null=True, blank=True
    )
    grower = models.ForeignKey(
        'grower.Grower', on_delete=models.CASCADE,null=True, blank=True)
    batch_id = models.IntegerField(null=True, blank=True)
    acreage = models.FloatField(null=True, blank=True)
    # ........
    fsa_farm_number = models.CharField(
        max_length=250,help_text="Multiple values can be Comma (,) separated", null=True, blank=True,
        verbose_name='FSA Farm Number')
    fsa_tract_number = models.CharField(
        max_length=250,help_text="Multiple values can be Comma (,) separated", null=True, blank=True,
        verbose_name='FSA Tract Number')
    fsa_field_number = models.CharField(
        max_length=250,help_text="Multiple values can be Comma (,) separated", null=True, blank=True,
        verbose_name='FSA Field Number')
    crop = models.CharField(max_length=255, choices=CHOICE.CROP_CHOICES, null=True, blank=True)
    variety = models.CharField(
        max_length=255, choices=CHOICE.VARIETY_CHOICES, null=True, blank=True
    )
    yield_per_acre = models.FloatField(null=True, blank=True, verbose_name='Yield Per Acre')
    total_yield = models.FloatField(null=True, blank=True, verbose_name='Total Yield')
    crop_tech = models.CharField(max_length=200, blank=True, null=True, verbose_name='Crop Tech')
    previous_crop = models.CharField(
        max_length=100,
        blank=True, null=True, verbose_name='Previous Crop'
    )
    stand_count = models.IntegerField(null=True, blank=True, verbose_name='Stand Count')
    plant_date = models.DateField(null=True, blank=True, verbose_name='Plant Date')
    harvest_date = models.DateField(
        null=True, blank=True, verbose_name='Harvest Date'
    )
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    # 14-11-23
    eschlon_id = models.CharField(max_length=200, null=True, blank=True, verbose_name='Echelon Id')
    water_saving = models.IntegerField(null=True, blank=True, verbose_name='Water Saving')
    gal_water_saved = models.CharField(max_length=200, null=True, blank=True)
    water_lbs_saved = models.CharField(max_length=200, null=True, blank=True)
    co2_eq_reduced = models.CharField(max_length=200, null=True, blank=True)
    increase_nitrogen = models.CharField(max_length=200, null=True, blank=True)
    ghg_reduction = models.CharField(max_length=200, null=True, blank=True)
    land_use_efficiency = models.CharField(max_length=200, null=True, blank=True)
    grower_premium_percentage = models.CharField(max_length=200, null=True, blank=True)
    grower_dollar_premium = models.CharField(max_length=200, null=True, blank=True)

class FieldActivity(models.Model):
    field_activity = models.CharField(max_length=200, null=True, blank=True)
    date_of_activity = models.DateField(null=True, blank=True)
    type_of_application = models.CharField(max_length=200, null=True, blank=True)
    mode_of_application = models.CharField(max_length=200, null=True, blank=True)
    label_name = models.CharField(max_length=200, null=True, blank=True)
    amount_per_acre = models.FloatField(null=True, blank=True)
    unit_of_acre = models.CharField(max_length=200, null=True, blank=True)
    n_nitrogen = models.FloatField(null=True, blank=True)
    p_phosporus = models.FloatField(null=True, blank=True)
    k_potassium = models.FloatField(null=True, blank=True)
    special_notes = models.TextField(null=True, blank=True)
    field = models.ForeignKey(Field, on_delete=models.CASCADE, null=True, blank=True)
    field_updated = models.ForeignKey(FieldUpdated, on_delete=models.SET_NULL, null=True, blank=True)

