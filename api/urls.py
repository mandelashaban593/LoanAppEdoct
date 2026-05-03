from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, RequestPasswordResetView, ConfirmPasswordResetView, UserRoleDetailView, UserRoleTestView
from rest_framework_simplejwt.views import TokenObtainPairView

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),  # ✅ IMPORTANT FIX
    path('me/role/', UserRoleDetailView.as_view(), name='my-role'),
    path('test/role/', UserRoleTestView.as_view(), name='test-role'),

    path('token/', TokenObtainPairView.as_view()),

    path('password-reset/', RequestPasswordResetView.as_view()),
    path('password-reset-confirm/', ConfirmPasswordResetView.as_view()),
]
