from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator


def create_password_reset_link(user):
    base64_encoded_id = urlsafe_base64_encode(force_bytes(user.id))
    token = PasswordResetTokenGenerator().make_token(user)
    url = f"reset_password/{base64_encoded_id}/{token}"
    return url
