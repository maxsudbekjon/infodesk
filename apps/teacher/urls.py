from django.urls import path
from .views import (
    TeacherToggleArchiveAPIView,
    TeacherUploadImageAPIView,
    TeacherListAPIView,
    TeacherCreateAPIView,
    TeacherDetailAPIView,
    TeacherDeleteAPIView,
    TeacherUpdateAPIView,
    TeacherGroupListAPIView,
    TeacherCourseListAPIView,
    TeacherCourseGroupsAPIView,
    TeacherMeAPIView,
)

urlpatterns = [
    path('list/', TeacherListAPIView.as_view()),
    path('create/', TeacherCreateAPIView.as_view()),
    path('detail/<int:pk>/', TeacherDetailAPIView.as_view()),
    path('<int:pk>/toggle-archive/', TeacherToggleArchiveAPIView.as_view()),
    path('<int:pk>/upload-image/', TeacherUploadImageAPIView.as_view()),
    path('my-groups/', TeacherGroupListAPIView.as_view()),
    path('my-courses/', TeacherCourseListAPIView.as_view()),
    path('my-courses/groups/', TeacherCourseGroupsAPIView.as_view()),
    path('my-courses/<int:course_id>/groups/', TeacherCourseGroupsAPIView.as_view()),
    path('me/', TeacherMeAPIView.as_view(), name='teacher-me'),

    path('delete/<int:pk>/', TeacherDeleteAPIView.as_view()),
    path('update/<int:pk>/', TeacherUpdateAPIView.as_view()),
]
