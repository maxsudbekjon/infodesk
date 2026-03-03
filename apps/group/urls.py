from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.group.views import GroupCreateAPIView, GroupDetailAPIView, GroupListAPIView, GroupStatusUpdateAPIView, \
    GroupNoteViewSet

router = DefaultRouter()

router.register(r'group-notes', GroupNoteViewSet, basename='group-note')

urlpatterns = [
    path('list/',GroupListAPIView.as_view(),name='group-list'),
    path('update-status/<int:id>',GroupStatusUpdateAPIView.as_view(),name='group-status-update'),
    path('create/',GroupCreateAPIView.as_view(),name='group-create'),
    path('detail/<int:id>',GroupDetailAPIView.as_view(),name='group-detail'),
    path('', include(router.urls), name='group-notes'),

]
