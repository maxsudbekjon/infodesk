from django.contrib import admin

from apps.teacher.models import Specialty, Teacher


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    search_fields = ('title',)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'monthly_salary', 'kpi', 'monthly_per_lesson', 'monthly_per_student', 'is_archived')
    search_fields = ('user__phone_number',)
    list_filter = ('is_archived',)