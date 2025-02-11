from django.db import models
from apps.accounts.models import User
# Create your models here.

class AssistantApp(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE, null=True, blank=True)
    user_name = models.CharField(max_length=200, null=True, blank=True)
    user_role = models.CharField(max_length=200, null=True, blank=True)
    question = models.TextField(null=True, blank=True)
    answer = models.TextField(null=True, blank=True)
    asking_datetime = models.DateTimeField(auto_now_add=True,null=True, blank=True)