"""Database models for farm and farm grouping"""
from django.db import models
from django.utils import timezone
from django.urls import reverse
from apps.grower.models import Grower
# from apps.field.models import Field

from apps.field.choices import CHOICE
from apps.core.validate import validate_zipcode


class Farm(models.Model):
    """Database model for farm"""
    name = models.CharField(unique=True, max_length=200)
    grower = models.ForeignKey('grower.Grower', on_delete=models.CASCADE)
    cultivation_year = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Cultivation Year'
    )
    area = models.FloatField(blank=True, null=True)
    land_type = models.CharField(
        max_length=200, null=True, blank=True, verbose_name='Land Type'
    )
    state = models.CharField(max_length=200, null=True, blank=True)
    county = models.CharField(max_length=200, null=True, blank=True)
    village = models.CharField(max_length=200, null=True, blank=True)
    town = models.CharField(max_length=200, null=True, blank=True)
    street = models.CharField(max_length=200, null=True, blank=True)
    zipcode = models.BigIntegerField(
        validators=[validate_zipcode], null=True, blank=True, verbose_name='Zip Code'
    )
    nutrien_account_id = models.CharField(max_length=200, null=True, blank=True) 
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Farm"
        verbose_name_plural = "Farms"
    

    def address(self):
        "returns the full address of farm object"
        return f'{self.street},{self.town},{self.state},{self.zipcode}'
    
   

    def __str__(self):
        """returns string representation of farm"""
        #return f'{self.id}:{self.name} : {self.grower_id}'
        return f'{self.name}'

    

class FarmGrouping(models.Model):
    "database model for farm grouping"
    grouping_criteria = models.CharField(
        max_length=255, choices=CHOICE.FARM_GROUP_CHOICES,
        verbose_name='Farm Grouping Criteria'
    )

    class Meta:
        verbose_name = "Farm Grouping"
        verbose_name_plural = "Farm Groupings"

    def __str__(self):
        return f'{self.grouping_criteria}'


class CsvToFarm(models.Model):
    '''For storing CSV file
    import functionality for creating Farms'''
    csv_file = models.FileField(upload_to='CSV',null=False)

    def get_absolute_url(self):
        '''For returning url after storing file'''
        return reverse("csv-farm-mapping", kwargs={"pk": self.pk})

