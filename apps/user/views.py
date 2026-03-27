from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.user.serializers import UserLoginSerializer


@extend_schema(tags=["Auth"], summary="User login")
class UserLoginAPIView(TokenObtainPairView):
    serializer_class = UserLoginSerializer


@extend_schema(tags=["Auth"], summary="Refresh access token")
class UserTokenRefreshAPIView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer






