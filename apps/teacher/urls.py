from django.urls import path
from .views import (
    # TeacherListCreateAPIView,
    TeacherRetrieveUpdateDestroyAPIView,
    TeacherToggleArchiveAPIView,
    TeacherUploadImageAPIView,
    TeacherListAPIView, TeacherCreateAPIView, TeacherDetailAPIView,
)



urlpatterns = [
    # path('list/', TeacherListCreateAPIView.as_view()),
    path('list/', TeacherListAPIView.as_view()),
    path('create/', TeacherCreateAPIView.as_view()),
    path('detail/<int:pk>/', TeacherDetailAPIView.as_view()),
    path('<int:pk>/toggle-archive/', TeacherToggleArchiveAPIView.as_view()),
    path('<int:pk>/upload-image/', TeacherUploadImageAPIView.as_view()),

    path('<int:pk>/', TeacherRetrieveUpdateDestroyAPIView.as_view()),
]


