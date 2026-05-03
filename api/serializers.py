from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode


User = get_user_model()
token_generator = PasswordResetTokenGenerator()

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'password', 'first_name', 'last_name',
            'email', 'role', 'branch', 'phone'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # 🔐 hash password
        user.save()
        return user




class UserRoleSerializer(serializers.ModelSerializer):
    # Computed properties
    is_field_officer   = serializers.ReadOnlyField()
    is_loan_officer    = serializers.ReadOnlyField()
    is_branch_manager  = serializers.ReadOnlyField()
    is_finance_officer = serializers.ReadOnlyField()
    is_md              = serializers.ReadOnlyField()
    is_sys_admin       = serializers.ReadOnlyField()
    is_auditor         = serializers.ReadOnlyField()
    is_read_only       = serializers.ReadOnlyField()
    can_approve        = serializers.ReadOnlyField()
    can_disburse       = serializers.ReadOnlyField()
    sees_all_branches  = serializers.ReadOnlyField()
    is_account_locked  = serializers.ReadOnlyField()

    role_display_badge = serializers.SerializerMethodField()
    full_name          = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "branch",
            "phone",

            # computed fields
            "is_field_officer",
            "is_loan_officer",
            "is_branch_manager",
            "is_finance_officer",
            "is_md",
            "is_sys_admin",
            "is_auditor",
            "is_read_only",
            "can_approve",
            "can_disburse",
            "sees_all_branches",
            "is_account_locked",

            "role_display_badge",
            "full_name",
        ]

    def get_role_display_badge(self, obj):
        return obj.get_role_display_badge()

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username



class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        if not User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("User with this email does not exist")
        return data


class ConfirmPasswordResetSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, data):
        try:
            uid = urlsafe_base64_decode(data['uid']).decode()
            user = User.objects.get(id=uid)
        except Exception:
            raise serializers.ValidationError("Invalid UID")

        if not token_generator.check_token(user, data['token']):
            raise serializers.ValidationError("Invalid or expired token")

        validate_password(data['new_password'])

        data['user'] = user
        return data