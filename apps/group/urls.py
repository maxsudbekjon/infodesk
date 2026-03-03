from django.urls import path

from apps.group.views import (
    GroupCreateAPIView,
    GroupDetailAPIView,
    GroupListAPIView,
    GroupStatusUpdateAPIView,
)

urlpatterns = [
    path('list/',GroupListAPIView.as_view(),name='group-list'),
    path('update-status&branch/<int:id>',GroupStatusUpdateAPIView.as_view(),name='group-status-update'),
    path('create/',GroupCreateAPIView.as_view(),name='group-create'),
    path('detail/<int:id>',GroupDetailAPIView.as_view(),name='group-detail'),
]
