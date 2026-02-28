from django.contrib import admin

from apps.group.models import CourseTemplate,Day,Room,Group

# Register your models here.
admin.site.register(CourseTemplate)
admin.site.register(Day)
admin.site.register(Room)
admin.site.register(Group)