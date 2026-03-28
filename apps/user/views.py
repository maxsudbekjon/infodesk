from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.group.permissions import IsTeacherOrStudentUser
from apps.user.serializers import (
    UserLoginSerializer,
    UserPasswordChangeResponseSerializer,
    UserPasswordChangeSerializer,
)


@extend_schema(tags=["Auth"], summary="User login")
class UserLoginAPIView(TokenObtainPairView):
    serializer_class = UserLoginSerializer


@extend_schema(tags=["Auth"], summary="Refresh access token")
class UserTokenRefreshAPIView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer


@extend_schema(
    tags=["Auth"],
    summary="Change current user password",
    request=UserPasswordChangeSerializer,
    responses={200: UserPasswordChangeResponseSerializer},
)
class UserPasswordChangeAPIView(generics.GenericAPIView):
    serializer_class = UserPasswordChangeSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrStudentUser]
    http_method_names = ["post", "head", "options"]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Parol muvaffaqiyatli yangilandi."},
            status=status.HTTP_200_OK,
        )





