from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.models import BaseUserManager
from django.utils import timezone
from django.db import connection
from django.contrib.auth.hashers import make_password

from rest_framework.authtoken.models import Token

from phonenumber_field.modelfields import PhoneNumberField

from apps.grower.models import Grower

from django.db.models.signals import post_save
from django.dispatch import receiver




class UserManager(BaseUserManager):
    """Manager for custom user"""

    def create_user(self, first_name, last_name, email, username, password=None):
        """Creates and saves a new user"""
        if not email:
            raise ValueError(_('You must provide an email address'))
        if not username:
            raise ValueError(_('You must provide an username'))

        email = self.normalize_email(email)
        user = self.model(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username
        )

        #cursor = connection.cursor()
        #cursor.execute("INSERT INTO grower_consultant(name,number,phone,email,created_date,modified_date) VALUES(%s , %s, %s , %s,%s , %s)", [first_name, 8998566565, '+12125585368', email, '2022-03-27 07:44:47.745728', '2022-03-27 07:44:47.745728'])

        #print(repr(password))
        user.set_password(password)
        
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, username, email, password):
        """Creates and saves a new superuser"""
        user = self.create_user(first_name, last_name, email, username, password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True

        if user.is_staff is not True:
            raise ValueError(
                'Superuser must be assigned to is_staff=True.')
        if user.is_superuser is not True:
            raise ValueError(
                'Superuser must be assigned to is_superuser=True.')
        user.save(using=self._db)

        return user

    def get_by_natural_key(self, username):
        case_insensitive_username_field = '{}__iexact'.format(self.model.USERNAME_FIELD)
        return self.get(**{case_insensitive_username_field: username})


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model that support using email and username"""
    email = models.EmailField(help_text='Email')
    username = models.CharField(max_length=150, unique=True, help_text='Username')
    first_name = models.CharField(max_length=150, blank=True, help_text='First Name')
    last_name = models.CharField(max_length=150, blank=True, help_text='Last Name')
    grower = models.ForeignKey('grower.Grower', on_delete=models.CASCADE, null=True, blank=True)
    role = models.ManyToManyField('Role')
    phone = PhoneNumberField(null = True, blank = True)
    is_consultant = models.BooleanField(default=False)
    is_processor = models.BooleanField(default=False)
    is_processor2 = models.BooleanField(default=False)
    is_processor3 = models.BooleanField(default=False)
    is_distributor = models.BooleanField(default=False)
    is_warehouse_manager = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    password_raw = models.CharField(max_length=128, unique=False, null=True)
    

    objects = UserManager()
    
  
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        app_label = 'accounts'

    def __str__(self):
        return f'{self.username}'


    #staticPss = "test@123456"

    def save_password(self, password):
        
        self.set_password(password)
        self.save()

    def full_name(self):
        
        return f'{self.first_name} {self.last_name}'

    def logout(self):
        Token.objects.filter(user=self).delete()

    @property
    def token(self):
        token, _ = Token.objects.get_or_create(user=self)
        return token.key

    def get_fields(self):
        return [(field.verbose_name, field.value_from_object(self)) for field in self.__class__._meta.fields]

    def get_role_perm(self):
        "returns the custom permissions asssigned to the role"
        role_perm = []
        for role in self.role.all():
            for permission in role.permissions.values_list('display'):
                role_perm.append(permission[0])
                #print(role_perm)
        return role_perm

    def get_role(self):
        user_roles_object = self.role.all()
        role_list = [role_data.role for role_data in user_roles_object]

        return role_list

    # def is_super_user(self):
    #     "returns the custom permissions assigned to the role"
    #     role_arr = []
    #     is_super = False
    #     for role in self.role.all():
    #         role_arr.append(role)
    #     role = role_arr[0]
    #     role = str(role)
    #     if(role == "SuperUser"):
    #         is_super = True
    #         #print(is_super)
    #     return is_super


class Role(models.Model):
    """Database model for role"""
    role = models.CharField(max_length=255)
    permissions = models.ManyToManyField('Permission')
    grower = models.ForeignKey(Grower, on_delete=models.CASCADE, null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.role}'


class Permission(models.Model):
    """Database model for permission"""
    name = models.CharField(max_length=255, help_text='e.g. user_management')
    display = models.CharField(max_length=255, help_text='e.g. User Management')


    def __str__(self):
        return f'{self.display}'

class SubSuperUser(models.Model):
    """Database model for Consultant"""
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=10, null=True, blank=True)
    email = models.EmailField(unique=True,
        help_text="ex: cconsultant@gmail.com"
        )
    role = models.ForeignKey('Role', on_delete=models.CASCADE, null=False, blank=False, default=False)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SubSuperUser"
        verbose_name_plural = "SubSuperUsers"

    def __str__(self):
        return f'{self.name}'

StatusChoice = (
    ("READ", "READ"),
    ("UNREAD", "UNREAD"),
)

class ShowNotification(models.Model):
    user_id_to_show = models.CharField(max_length=255, null=True, blank=True)
    notification_reason = models.CharField(max_length=255, null=True, blank=True)
    msg = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255,choices=StatusChoice, null=True, blank=True, default='UNREAD')
    redirect_url = models.TextField(null=True, blank=True)
    added_data_time = models.DateTimeField(auto_now_add=True,null=True, blank=True)

    def __str__(self):
        return f"{self.notification_reason}-{self.msg}"

# 05-04-23
LOG_TYPE_CHOICES = (
    ("User", "User"),
    ("Grower", "Grower"),
    ("Farm", "Farm"),
    ("Field", "Field"),
    ("Storage", "Storage"),
    ("FieldActivity", "FieldActivity"),
    ("GrowerShipment", "GrowerShipment"),
    ("ProcessorUser", "ProcessorUser"),
    ("ClassingReport", "ClassingReport"),
    ("ClassingListTier2", "ClassingListTier2"),
    ("ProcessorUser2", "ProcessorUser2"),
    ("LinkGrowerToProcessor", "LinkGrowerToProcessor"),
    ("ProductionManagement", "ProductionManagement"),
    ("ShipmentManagement", "ShipmentManagement"),
    ("GrowerPayee", "GrowerPayee"),
)
LOG_STATUS_CHOICES = (
    ("Added", "Added"),
    ("Edited", "Edited"),
    ("Password changed", "Password changed"),
    ("Deleted", "Deleted"),
)
LOG_DEVICE_CHOICES = (
    ("Web", "Web"),
    ("App", "App"),
)
class LogTable(models.Model):
    log_type = models.CharField(max_length=250, choices=LOG_TYPE_CHOICES, null=True, blank=True)
    log_status = models.CharField(max_length=250, choices=LOG_STATUS_CHOICES, null=True, blank=True)
    log_idd = models.CharField(max_length=250, null=True, blank=True)
    log_name = models.CharField(max_length=250, null=True, blank=True)
    log_email = models.CharField(max_length=250, null=True, blank=True)
    log_details = models.TextField(null=True, blank=True)
    log_device = models.CharField(max_length=250, choices=LOG_DEVICE_CHOICES, null=True, blank=True)

    action_by_userid = models.CharField(max_length=250, null=True, blank=True)
    action_by_username = models.CharField(max_length=250, null=True, blank=True)
    action_by_email = models.CharField(max_length=250, null=True, blank=True)
    action_by_role = models.CharField(max_length=250, null=True, blank=True)
    action_datetime = models.DateTimeField(auto_now_add=True,null=True, blank=True)


class VersionUpdate(models.Model):
    version = models.CharField(max_length=5, null=True, blank=True)
    release_date = models.DateTimeField()
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_users = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return f"Version {self.version} : {self.release_date}"
    