from django.db import models
from apps.processor.models import Processor, ProcessorUser, LinkGrowerToProcessor, Location
from apps.grower.models import *
from apps.accounts.models import *


# Create your models here.
CHAT_WITH = (
    ("Grower-Consultant", "Grower-Consultant"),
    ("Grower-Processor", "Grower-Processor"),
    ("Grower-Admin", "Grower-Admin"),
)

class ProcessorMsgboard(models.Model):
    processor = models.ForeignKey(Processor, on_delete=models.CASCADE, null=True, blank=True)
    grower = models.ForeignKey(Grower, on_delete=models.CASCADE, null=True, blank=True)
    consultant = models.ForeignKey(Consultant, on_delete=models.CASCADE, null=True, blank=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    chat_with = models.CharField(max_length = 200,choices = CHAT_WITH,default = 'Grower-Processor', null=True,blank=True)
    created_date =models.DateField(auto_now_add=True)
    
    def __str__(self) :
        return f"{self.chat_with}"

READ_STATUS_CHOICE = [
        ("READ", "READ"),
        ("UNREAD", "UNREAD"),
    ]

class ProcessorMessage(models.Model):
    board = models.ForeignKey(ProcessorMsgboard, on_delete=models.CASCADE, null=True, blank=True)
    sender_is = models.CharField(max_length=250,null=True,blank=True)
    sender_id = models.CharField(max_length=250,null=True,blank=True,verbose_name='Grower or ProcessorUser ID')
    sender_name = models.CharField(max_length=250,null=True,blank=True,verbose_name='Grower or ProcessorUser Name')
    receiver_is = models.CharField(max_length=250,null=True,blank=True)
    receiver_id = models.CharField(max_length=250,null=True,blank=True,verbose_name='Grower or Processor ID')
    receiver_name = models.CharField(max_length=250,null=True,blank=True,verbose_name='Grower or Processor Name')
    msg = models.TextField(null=True,blank=True)
    msg_date = models.DateField(auto_now_add=True)
    msg_time = models.TimeField(auto_now_add=True)
    read_status = models.CharField(max_length=250,null=True,blank=True,choices=READ_STATUS_CHOICE)