from django.db import models
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now


# Create your models here.
class QuickBooksToken(models.Model):
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    realm_id = models.CharField(max_length=255)
    state = models.CharField(max_length=255, null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Token for Realm ID: {self.realm_id} with State: {self.state}"
    
    def is_token_expired(self):
        """
        Check if the access token is expired based on the expires_at field.
        """
        return now() >= self.expires_at

    def save(self, *args, **kwargs):
        """
        Automatically set the `expires_at` field based on the token's expiration information.
        If no expiration is provided, use a fallback value.
        """        
        if not self.expires_at:            
            expires_in_seconds = getattr(settings, 'DEFAULT_TOKEN_EXPIRY', 3600)
            self.expires_at = now() + timedelta(seconds=expires_in_seconds)
        super().save(*args, **kwargs)

    def update_expiry(self, expires_in):
        """
        Update the `expires_at` field based on the provided `expires_in` duration (in seconds).
        This should be called after refreshing the token.
        """
        self.expires_at = now() + timedelta(seconds=expires_in)
        self.save()
