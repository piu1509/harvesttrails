from django.contrib.auth import get_user_model
from django.utils.encoding import force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from apps.core.email import send_mail
from .services import create_password_reset_link
from apps.grower.models import Grower
from django.db import connection
from django.contrib.auth.hashers import make_password

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """Serialize username and password"""
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=255)

    def validate_username(self, username):
        if User.objects.filter(username=username).exists():
            return username
        else:
            raise serializers.ValidationError("Account with given email not exists")

    def save(self):
        validated_data = self.validated_data
        user = User.objects.get(username=validated_data['username'])
        if user.check_password(validated_data['password']):
            return user
        else:
            raise serializers.ValidationError("incorrect password")


class TokenSerializer(serializers.Serializer):
    """Serialize Token"""
    token = serializers.CharField(max_length=255)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user object"""
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'username', 'password', 'password2', 'email', 'first_name', 'last_name',
            'grower', 'is_consultant'
        )
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
        }


    def validate(self, attrs):
        """Validates password if they match and raises validation error if they don'nt"""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        """Creates a new user"""
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )

        

        user.set_password(validated_data['password'])
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for user object"""

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name'
        )

    def update(self, instance, validated_data):
        print(validated_data)
        instance.username=validated_data['username']
        instance.email=validated_data['username']
        instance.first_name=validated_data['first_name']
        instance.last_name=validated_data['last_name']
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serialize passwords"""
    old_password = serializers.CharField(max_length=128, write_only=True, required=True)
    new_password1 = serializers.CharField(max_length=128, write_only=True, required=True)
    new_password2 = serializers.CharField(max_length=128, write_only=True, required=True)

    def validate_old_password(self, value):
        """Validates old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                'Your old password was entered incorrectly. Please enter it again.')
        return value

    def validate(self, data):
        """Validates if the password match"""
        user= self.context['request'].user
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({'new_password2': "The two password fields didn't match."})
        validate_password(data['new_password1'], user)
        return data

    def save(self, **kwargs):
        """Saves the new passowrd"""
        password = self.validated_data['new_password1']
        user = self.context['request'].user
        user.set_password(password)
        user.save()
        return user


class EmailSerializer(serializers.Serializer):
    """Serialize the email"""
    email = serializers.EmailField()

    def validate_email(self, email):
        """Validate if the email exists"""
        if User.objects.filter(email=email).exists():
            return email
        else:
            raise serializers.ValidationError("Account with given email not exists")

    def save(self):
        """Sends and email to the user"""
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        context = {
            'user': user,
            'link': create_password_reset_link(user)
        }

        send_mail(
            to=email,
            subject_template="email/account/forgot_password_sub.txt",
            body_template="email/account/forgot_password.html",
            context=context
        )


class ResetPasswordSerializer(serializers.Serializer):
    """Serialize uid, token and passwords"""
    uid =serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, data):
        """Validates the passwords"""
        user= self.context['request'].user
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'new_password2': "The two password fields didn't match."})
        validate_password(data['new_password'], user)
        return data

    def validate(self, data):
        """Method to validate token"""
        id = force_str(urlsafe_base64_decode(data['uid']))
        user = User.objects.get(pk=id)
        is_valid = PasswordResetTokenGenerator().check_token(user, data['token'])
        if is_valid:
            data['user'] = user
            return data
        else:
            raise serializers.ValidationError("Invalid token")

    def save(self):
        """sets and saves the password"""
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
