from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from .serializers import (
    UserSerializer,
    RequestPasswordResetSerializer,
    ConfirmPasswordResetSerializer,
    UserRoleSerializer
)

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


class UserRoleDetailView(APIView):


    def get(self, request):
        user = request.user
        serializer = UserRoleSerializer(user)
        return Response(serializer.data)


class UserRoleTestView(APIView):
    """
    For testing via POST (Postman)
    """
    def post(self, request):
        user_id = request.data.get("user_id")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        serializer = UserRoleSerializer(user)
        return Response(serializer.data)

# 👤 User CRUD

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserRoleSerializer

# 🔑 Request Password Reset
class RequestPasswordResetView(APIView):
    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        uid = urlsafe_base64_encode(force_bytes(user.id))
        token = token_generator.make_token(user)

        # Normally send email — for Postman testing we return it
        return Response({
            "uid": uid,
            "token": token,
            "message": "Use these to reset password"
        })


# 🔄 Confirm Password Reset
class ConfirmPasswordResetView(APIView):
    def post(self, request):
        serializer = ConfirmPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({"message": "Password reset successful"})