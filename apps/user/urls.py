from django.urls import path
from apps.user.views import UserLoginAPIView, UserPasswordChangeAPIView

urlpatterns = [
    path("login/", UserLoginAPIView.as_view(), name="user-login"),
    path("change-password/", UserPasswordChangeAPIView.as_view(), name="user-change-password"),
]
