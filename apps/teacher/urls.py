from rest_framework.routers import DefaultRouter
from django.urls import path, include
# from .views import TeacherViewSet
#
# router = DefaultRouter()
# router.register(r'teachers', TeacherViewSet, basename='teacher')
#
# urlpatterns = [
#     path('api/', include(router.urls)),
# ]

from django.urls import path
from .views import (
    TeacherListCreateAPIView,
    TeacherRetrieveUpdateDestroyAPIView,
    TeacherToggleArchiveAPIView,
    TeacherUploadImageAPIView,
    TeacherStatsAPIView,
)

urlpatterns = [
    path('list/', TeacherListCreateAPIView.as_view()),
    path('<int:pk>/', TeacherRetrieveUpdateDestroyAPIView.as_view()),
    path('<int:pk>/toggle-archive/', TeacherToggleArchiveAPIView.as_view()),
    path('<int:pk>/upload-image/', TeacherUploadImageAPIView.as_view()),
    path('<int:pk>/stats/', TeacherStatsAPIView.as_view()),
]
