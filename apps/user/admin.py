from django.contrib import admin


from apps.user.models import User,Operator
admin.site.register(Operator)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email',)