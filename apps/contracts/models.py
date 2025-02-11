import secrets
import string
from datetime import datetime, timedelta
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
from apps.accounts.models import User
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.core.exceptions import ImproperlyConfigured
from django.contrib import messages
from django.shortcuts import HttpResponse
from dateutil.relativedelta import relativedelta


class Contracts(models.Model):
    """Database model for field"""
    name = models.CharField(unique=True, max_length=200)
    envelope_id = models.CharField(max_length=200, null=True)
    is_signed = models.BooleanField(default=False)
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='Created Date')
    modified_date = models.DateTimeField(auto_now=True, verbose_name='Modified Date')
    contract_doc = models.FileField(upload_to='demo_documents/', verbose_name='Contract Document', blank=True)

    def __str__(self):
        """Returns string representation of farm"""
        # return f'{self.id}:{self.name}'
        return f'{self.name}'

    def get_fields(self):
        """This method return all the field name and their value of all objects of field model."""
        return [(contract.name, contract.value_from_object(self)) for contract in self.__class__._meta.contracts]


class GrowerContracts(models.Model):
    """Database model for field"""
    contract = models.ForeignKey('contracts.Contracts', on_delete=models.CASCADE, null=False, blank=False)
    contract_url = models.TextField()
    grower = models.ForeignKey('grower.Grower', on_delete=models.CASCADE, null=False, blank=False)
    is_signed = models.BooleanField(default=False)
    envelope_id = models.CharField(max_length=200, null=True)
    envelope_uri = models.URLField(null=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='Created Date')
    modified_date = models.DateTimeField(auto_now=True, verbose_name='Modified Date')

    def __str__(self):
        """Returns string representation of farm"""
        # return f'{self.id}:{self.name}'
        return f'contract : {self.contract}, grower : {self.grower}, contract_url: {self.contract_url}'


class SignedContracts(models.Model):
    """Database model for field"""
    signature = models.TextField()
    contract = models.ForeignKey('contracts.Contracts', on_delete=models.CASCADE, null=False, blank=False)
    grower = models.ForeignKey('grower.Grower', on_delete=models.CASCADE, null=False, blank=False)
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='Created Date')

    def __str__(self):
        """Returns string representation of farm"""
        # return f'{self.id}:{self.name}'
        return f'{self.id}'


class ContractsVerifiers(models.Model):
    """Database model for field"""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    contract = models.ForeignKey(
        'contracts.Contracts',
        on_delete=models.CASCADE,
        related_name="contract_verifiers",
        null=False,
        blank=False
    )
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='Created Date')

    def __str__(self):
        """Returns string representation of farm"""
        # return f'{self.id}:{self.name}'
        return f'{self.name}'


class VerifiedSignedContracts(models.Model):
    """Database model for field"""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    signature = models.TextField(
        null=True,
        blank=True
    )
    signed_contracts = models.ForeignKey(
        'contracts.SignedContracts',
        on_delete=models.CASCADE,
        related_name="signedcontracts",
        null=False,
        blank=False
    )
    is_verified = models.BooleanField(default=False)
    verified_date = models.DateTimeField(auto_now=True)
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='Created Date')

    def __str__(self):
        """Returns string representation of farm"""
        # return f'{self.id}:{self.name}'
        return f'{self.name}'


unit_choice = (
    ("LBS","LBS"),
    ("MT","MT"),
)
processor_type = (
    ("T1","T1"),
    ("T2","T2"),
    ("T3","T3"),
    ("T4","T4"),
)
contract_period_choices = (
    ("Days","Days"),
    ("Months","Months"),
    ("Year","Year"),
)
contract_status = (
    ('Contract Initiated', 'Contract Initiated'),
    ('Under Review', 'Under Review'),
    ('Active With Documentation Processing','Active With Documentation Processing'),
    ('Active With Documentation Completed','Active With Documentation Completed'),
    ('Completed', 'Completed'),
    ('Terminated', 'Terminated'),
)
contract_type = (
    ('Single Crop','Single Crop'),
    ('Multiple Crop', 'Multiple Crop'),
) 

def generate_secret_key( length=32):
    """Generate a unique secret key with the format HT+date+random_number."""
    
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
    date_part = datetime.now().strftime("%Y%m%d")
    random_number = secrets.randbelow(900) + 100  
    secret_key = f"HT{date_part}{random_number}"
    return secret_key
 
       
class AdminProcessorContract(models.Model):
    secret_key = models.CharField(max_length=255, unique=True)
    processor_id = models.CharField(max_length=255)
    processor_type = models.CharField(max_length=5, choices=processor_type)
    processor_entity_name = models.CharField(max_length=255, null=True, blank=True)  
    contract_type = models.CharField(max_length=25, choices=contract_type, default='Single Crop')  
    total_price = models.DecimalField( max_digits=20,decimal_places=2,validators=[MinValueValidator(Decimal('0.01'))],null=True, blank=True)
    contract_start_date = models.DateTimeField()
    contract_period = models.PositiveIntegerField(help_text="Warranty period")
    contract_period_choice = models.CharField(max_length=10, choices=contract_period_choices, default="Days" )
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=255, choices=contract_status)
    reason_for_rejection = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contractingUser')  
    is_signed = models.BooleanField(default=False)
    

    def save(self, *args, **kwargs):
        if not self.secret_key:  # Generate a new key only if it does not already exist
            while True:
                self.secret_key = generate_secret_key()
                if not AdminProcessorContract.objects.filter(secret_key=self.secret_key).exists():
                    break

        if isinstance(self.contract_period, str):
            self.contract_period = int(self.contract_period)

        if isinstance(self.contract_start_date, str):
            self.contract_start_date = datetime.strptime(self.contract_start_date, "%Y-%m-%d")

        # Make contract_start_date timezone-aware
        if timezone.is_naive(self.contract_start_date):
            self.contract_start_date = timezone.make_aware(self.contract_start_date, timezone.get_current_timezone())

        # Calculate end_date based on the period choice
        if self.contract_period:
            if self.contract_period_choice == "Days":
                self.end_date = self.contract_start_date + timedelta(days=self.contract_period)
            elif self.contract_period_choice == "Months":
                self.end_date = self.contract_start_date + timedelta(days=self.contract_period * 30)  # Approximate to 30 days per month
            elif self.contract_period_choice == "Year":
                self.end_date = self.contract_start_date + timedelta(days=self.contract_period * 365)  # Approximate to 365 days per year

        # Make end_date timezone-aware
        if timezone.is_naive(self.end_date):
            self.end_date = timezone.make_aware(self.end_date, timezone.get_current_timezone())

        super().save(*args, **kwargs)

    def get_active_months(self):
        """
        Returns a list of months (as strings) during which the contract is active.
        """
        if not self.contract_start_date or not self.end_date:
            return []

        active_months = []
        current_date = self.contract_start_date.replace(day=1)  # Start at the beginning of the month
        end_date = self.end_date.replace(day=1)  # Ensure we only compare months, not specific days or times

        while current_date <= end_date:
            active_months.append(current_date.strftime('%B %Y'))  # Add the current month to the list
            current_date += relativedelta(months=1)  # Move to the next month

        return active_months
    
    def __str__(self):
        return f'Contract ID - {self.secret_key} || {self.processor_entity_name} || {self.processor_type}'


class CropDetails(models.Model):
    @staticmethod
    def crop_choices():
        from apps.field.models import Crop
        crops = Crop.objects.all()
        return [(crop.code, crop.name) for crop in crops] 
    
    contract = models.ForeignKey(AdminProcessorContract, on_delete=models.CASCADE, related_name='contractCrop')
    crop = models.CharField(max_length=255, choices=[], null=True, blank=True)
    crop_type = models.CharField(max_length=255, null=True, blank=True)
    contract_amount = models.FloatField()
    amount_unit = models.CharField(max_length=10, choices=unit_choice)
    per_unit_rate = models.DecimalField(max_digits=10, decimal_places=3) 
    left_amount = models.FloatField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)    
        self._meta.get_field('crop').choices = self.crop_choices() 

    def save(self, *args, **kwargs):
        if self._state.adding and self.left_amount is None:
            self.left_amount = self.contract_amount
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f'Contract ID - {self.contract.secret_key} || Crop -  {self.crop} || Amount - {self.contract_amount} {self.amount_unit}'


class AdminProcessorContractSignature(models.Model):
    contract = models.ForeignKey(AdminProcessorContract, related_name='contractSignatures', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signingUser')
    signed_at = models.DateTimeField(auto_now_add=True)
    signature = models.TextField(help_text="A textual or digital representation of the signature")

    def __str__(self):
        return f'Signature of Contract id - {self.contract.id}'

    
class AdminProcessorContractDocuments(models.Model):
    contract = models.ForeignKey(AdminProcessorContract, on_delete=models.CASCADE, related_name='contractDocuments')
    name = models.CharField(max_length=255, null=True, blank=True)
    document = models.FileField(upload_to='contracts/documents/', null=True, blank=True)
    document_status = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Documents for {self.contract.id}'


class AdminCustomerContract(models.Model):
    secret_key = models.CharField(max_length=255, unique=True)
    customer_id = models.CharField(max_length=255) 
    customer_name = models.CharField(max_length=255)   
    contract_type = models.CharField(max_length=25, choices=contract_type, default='Single Crop') 
    total_price = models.DecimalField( max_digits=20,decimal_places=2,validators=[MinValueValidator(Decimal('0.01'))],null=True, blank=True)
    contract_start_date = models.DateTimeField()
    contract_period = models.PositiveIntegerField(help_text="Warranty period")
    contract_period_choice = models.CharField(max_length=10, choices=contract_period_choices, default="Days" )
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=255, choices=contract_status)
    reason_for_rejection = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contractUSer')  
    is_signed = models.BooleanField(default=False)
    

    def save(self, *args, **kwargs):
        if not self.secret_key:  # Generate a new key only if it does not already exist
            while True:
                self.secret_key = generate_secret_key()
                if not AdminCustomerContract.objects.filter(secret_key=self.secret_key).exists():
                    break

        if isinstance(self.contract_period, str):
            self.contract_period = int(self.contract_period)

        if isinstance(self.contract_start_date, str):
            self.contract_start_date = datetime.strptime(self.contract_start_date, "%Y-%m-%d").date()
        
        if self.contract_period:
            if self.contract_period_choice == "Days":
                self.end_date = self.contract_start_date + timedelta(days=self.contract_period)
            elif self.contract_period_choice == "Months":
                self.end_date = self.contract_start_date + timedelta(days=self.contract_period * 30)  # Approximate to 30 days per month
            elif self.contract_period_choice == "Year":
                self.end_date = self.contract_start_date + timedelta(days=self.contract_period * 365)  # Approximate to 365 days per year
        super().save(*args, **kwargs)   

    def get_active_months(self):
        """
        Returns a list of months (as strings) during which the contract is active.
        """
        if not self.contract_start_date or not self.end_date:
            return []

        active_months = []
        current_date = self.contract_start_date.replace(day=1)  # Start at the beginning of the month
        end_date = self.end_date.replace(day=1)  # Ensure we only compare months, not specific days or times

        while current_date <= end_date:
            active_months.append(current_date.strftime('%B %Y'))  # Add the current month to the list
            current_date += relativedelta(months=1)  # Move to the next month

        return active_months
    
    def __str__(self):
        return f'Contract ID - {self.secret_key} || {self.customer_name}'


class CustomerContractCropDetails(models.Model):
    @staticmethod
    def crop_choices():
        from apps.field.models import Crop
        crops = Crop.objects.all()
        return [(crop.code, crop.name) for crop in crops] 
    
    contract = models.ForeignKey(AdminCustomerContract, on_delete=models.CASCADE, related_name='customerContractCrop')
    crop = models.CharField(max_length=255, choices=[], null=True, blank=True)
    crop_type = models.CharField(max_length=255, null=True, blank=True)
    contract_amount = models.FloatField()
    amount_unit = models.CharField(max_length=10, choices=unit_choice)
    per_unit_rate = models.DecimalField(max_digits=10, decimal_places=3) 
    left_amount = models.FloatField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)    
        self._meta.get_field('crop').choices = self.crop_choices() 

    def save(self, *args, **kwargs):
        if self._state.adding and self.left_amount is None:
            self.left_amount = self.contract_amount
        super().save(*args, **kwargs)     

    def __str__(self):
        return f'Contract ID - {self.contract.secret_key} || Crop -  {self.crop} || Amount - {self.contract_amount} {self.amount_unit}'


class AdminCustomerContractSignature(models.Model):
    contract = models.ForeignKey(AdminCustomerContract, related_name='customerContractSignatures', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customerContractingUser')
    signed_at = models.DateTimeField(auto_now_add=True)
    signature = models.TextField(help_text="A textual or digital representation of the signature")

    def __str__(self):
        return f'Signature of Contract id - {self.contract.id}'

    
class AdminCustomerContractDocuments(models.Model):
    contract = models.ForeignKey(AdminCustomerContract, on_delete=models.CASCADE, related_name='customerContractDocuments')
    name = models.CharField(max_length=255, null=True, blank=True)
    document = models.FileField(upload_to='contracts/documents/', null=True, blank=True)
    document_status = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Documents for {self.contract.id}'
    
type_choices = (
    ("Service", "Service"),
    ("Inventory", "Inventory"),
    ("NonInventory", "NonInventory"),
)   
class ShipmentItem(models.Model):
    item = models.CharField(max_length=255, null=True, blank=True)
    item_name = models.CharField(max_length=255)
    item_type = models.CharField(max_length=255)
    quickbooks_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    per_unit_price = models.DecimalField(max_digits=10, decimal_places=2) 
    description = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=255, choices=type_choices, default="Inventory")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    purchase_description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.item_name}"
    
   


