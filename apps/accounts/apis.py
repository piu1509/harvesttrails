from django.contrib.auth import get_user_model

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status

from .serializers import (LoginSerializer, TokenSerializer, UserSerializer,
                          ChangePasswordSerializer, EmailSerializer,
                          ResetPasswordSerializer, UserUpdateSerializer)


User = get_user_model()


class AuthViewSet(viewsets.ViewSet):
    queryset = User.objects.none()
    authentication_classes = (TokenAuthentication,)

    @action(methods=["post"], detail=False)
    def login(self, request, *args, **kwarsg):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(TokenSerializer(instance=user).data)

    @action(
        methods=["post"],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def logout(self, request, *args, **kwargs):
        user = request.user
        user.logout()
        return Response({'message': "User logged out successfully."})

    @action(methods=["post"], detail=False)
    def register(self, request, *args, **kwarsg):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            data = {
                'data': serializer.data,
                'statuscode' : status.HTTP_201_CREATED,
                'message' : "User Created Successfully",
            }
            return Response(data)
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['patch', "get"],
        detail=False, permission_classes=(IsAuthenticated,)
    )
    def me(self, request, *args, **kwargs):
        if request.method == "GET":
            return Response(UserSerializer(instance=request.user).data)
        elif request.method == "PATCH":
            _serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
            if _serializer.is_valid(raise_exception=True):
                _serializer.save()
                data = {
                    'data': _serializer.data,
                    'statuscode' : status.HTTP_201_CREATED,
                    'message' : "User Details Updated Successfully",
                }
                return Response(data)
            else:
                return Response(_serializer._errors, status=status.HTTP_400_BAD_REQUEST)


    @action(
        methods=["post"], detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def change_password(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': "Password changed successfully."})

    @action(methods=["post"], detail=False)
    def forgot_password(self, request, *args, **kwargs):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': "Password reset link sent successfully."})

    @action(methods=["post"], detail=False)
    def reset_password(self, request, *args, **kwargs):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': "Password changed successfully."})
