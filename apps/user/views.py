from rest_framework_simplejwt.views import TokenObtainPairView

from apps.user.serializers import UserLoginSerializer


class UserLoginAPIView(TokenObtainPairView):
    serializer_class = UserLoginSerializer
