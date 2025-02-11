from django.contrib import admin
from apps.storage.models import *
# Register your models here.
admin.site.register(StorageFeed)
admin.site.register(Storage)
admin.site.register(StorageFeedCsv)