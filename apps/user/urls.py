from django.urls import path
from apps.user.views import UserLoginAPIView

urlpatterns = [
    path("login/", UserLoginAPIView.as_view(), name="user-login"),
]
