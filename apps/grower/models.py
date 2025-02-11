from ast import mod
from django.db import models
from django.utils import timezone
from phone_field import PhoneField
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from apps.core.validate import validate_year, validate_zipcode


class Grower(models.Model):
    """Database model for grower object"""
    name = models.CharField(help_text="ex: Fred Farmer", max_length=255)
    phone = models.CharField(max_length=10, unique=True, null=False, blank=False)
    email = models.EmailField(unique=True, help_text="ex: ffarmer@gmail.com")
    physical_address1 = models.CharField(max_length=255, blank=True, null=True)
    physical_address2 = models.CharField(max_length=255, blank=True, null=True)
    city1 = models.CharField(max_length=255, blank=True, null=True)
    state1 = models.CharField(max_length=200, null=True, blank=True)
    zip_code1 = models.BigIntegerField(blank=True, null=True, validators=[validate_zipcode])
    mailing_address1 = models.CharField(max_length=255, blank=True, null=True)
    mailing_address2 = models.CharField(max_length=255, blank=True, null=True)
    city2 = models.CharField(max_length=255, blank=True, null=True)
    state2 = models.CharField(max_length=200, null=True, blank=True)
    zip_code2 = models.BigIntegerField(blank=True, null=True, validators=[validate_zipcode])
    consultant = models.ManyToManyField('Consultant')
    notes = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Grower"
        verbose_name_plural = "Growers"

    def physical_address(self):
        """This method return the physical address of the grower object"""
        return f'{self.physical_address1},{self.city1},{self.zip_code1}'

    def mailing_address(self):
        """this method return the mailing address of the grower object"""
        return f'{self.mailing_address1},{self.city2},{self.zip_code2}'

    def __str__(self):
        """Returns string represntation of grower"""
        # return f'{self.id}: {self.name}'
        return f'{self.name}'

    def get_fields(self):
        """this method returns the field name and its value of all the objects of grower models"""
        return [(field.verbose_name, field.value_from_object(self)) for field in self.__class__._meta.fields]


    def get_Grower_Contract(self):
        grower =  GrowerChecklist.objects.filter(item_name='Grower_Contract').filter(grower_id=self.id)
        if len(grower) == 0:
            return 0
        else:
            checkstatus = [i.checkstatus for i in grower][0]
            if checkstatus == True:
                return 1
            else:
                return 0
    def get_Onboarding_Survey_1(self):
        grower =  GrowerChecklist.objects.filter(item_name='Onboarding_Survey_1').filter(grower_id=self.id)
        if len(grower) ==0:
            return 0
        else:
            checkstatus = [i.checkstatus for i in grower][0]
            if checkstatus == True:
                return 1
            else:
                return 0
        
    
    def get_FSA_ID_information(self):
        grower =  GrowerChecklist.objects.filter(item_name='FSA_ID_information').filter(grower_id=self.id)
        if len(grower) ==0:
            return 0
        else:
            checkstatus = [i.checkstatus for i in grower][0]
            if checkstatus == True:
                return 1
            else:
                return 0

    def get_Farm_fully_set_up(self):
        grower =  GrowerChecklist.objects.filter(item_name='Farm_fully_set_up').filter(grower_id=self.id)
        if len(grower) ==0:
            return 0
        else:
            checkstatus = [i.checkstatus for i in grower][0]
            if checkstatus == True:
                return 1
            else:
                return 0

    def get_Field_fully_set_up(self):
        grower =  GrowerChecklist.objects.filter(item_name='Field_fully_set_up').filter(grower_id=self.id)
        if len(grower) ==0:
            return 0
        else:
            checkstatus = [i.checkstatus for i in grower][0]
            if checkstatus == True:
                return 1
            else:
                return 0
    def get_Shapefile_upload_for_all_fields(self):
        grower =  GrowerChecklist.objects.filter(item_name='Shapefile_upload_for_all_fields').filter(grower_id=self.id)
        if len(grower) ==0:
            return 0
        else:
            checkstatus = [i.checkstatus for i in grower][0]
            if checkstatus == True:
                return 1
            else:
                return 0

class Consultant(models.Model):
    """Database model for Consultant"""
    name = models.CharField(max_length=255)
    number = models.CharField(
        max_length=255, unique=True
    )
    phone = models.CharField(max_length=10, null=True, blank=True)
    email = models.EmailField(unique=True,
                              help_text="ex: cconsultant@gmail.com"
                              )
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Consultant"
        verbose_name_plural = "Consultants"

    def __str__(self):
        return f'{self.name}'

# class GrowerNotification(models.Model):
#     text = models.TextField()
#     status = models.BooleanField(default=False)
#     grower = models.ForeignKey('Grower', on_delete=models.CASCADE, related_name='growernotifications')
#     created_date = models.DateTimeField(default=timezone.now)
#     modified_date = models.DateTimeField(auto_now=True)
#     # grower = models.ForeignKey('grower.Grower', on_delete=models.CASCADE)

#     class Meta:
#         verbose_name = "Grower Notification"
#         verbose_name_plural = "Grower Notification"


#     def __str__(self):
#         return f'{self.grower.name}'


# New Module GrowerChecklist ..............
class GrowerChecklist(models.Model):
    grower = models.ForeignKey('grower.Grower', on_delete=models.CASCADE)
    item_name = models.CharField(max_length=200, null=True, blank=True)
    checkstatus = models.BooleanField(null=True, blank=True)
    date_checked = models.DateField(auto_now_add=True)
    module = models.CharField(max_length=200)