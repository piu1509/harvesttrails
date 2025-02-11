from django.contrib import admin
from apps.growerpayments.models import *
# Register your models here.
admin.site.register(EntryFeeds)
admin.site.register(GrowerPayments)
admin.site.register(NasdaqApiData)
admin.site.register(GrowerPayee)
admin.site.register(PaymentSplits)