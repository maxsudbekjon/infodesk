from django import forms
from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from apps.dashboard.admin_utils import AdminUiResponseMixin, FriendlyAdminMixin
from apps.user.models import Operator, User


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Parol")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Parolni tasdiqlang")

    class Meta:
        model = User
        fields = ("phone_number", "full_name", "first_name", "last_name", "email", "role")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Parollar mos emas")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label="Parol")

    class Meta:
        model = User
        fields = (
            "phone_number",
            "full_name",
            "email",
            "password",
            "role",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )

    def clean_password(self):
        return self.initial["password"]


@admin.register(Operator)
class OperatorAdmin(FriendlyAdminMixin):
    admin_page_title = "Operatorlar"
    admin_page_subtitle = "Murojaatlar bilan ishlovchi operatorlar va KPI ko'rsatkichlari."
    list_display = (
        "id",
        "display_name",
        "phone_number",
        "center",
        "monthly_salary",
        "penalty_point",
        "bonus_point",
        "is_archived",
    )
    list_filter = ("is_archived", "center", "created_at")
    search_fields = ("user__phone_number", "user__full_name", "center__name")
    search_help_text = "Operator ni ism, telefon yoki organization bo'yicha qidiring."
    autocomplete_fields = ("user", "center")
    list_select_related = ("user", "center")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": ("user", "center", "image", "is_archived"),
        }),
        ("Ish ko'rsatkichlari", {
            "fields": ("monthly_salary", "kpi", "penalty_point", "bonus_point"),
        }),
        ("Texnik ma'lumotlar", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    @admin.display(description="Operator")
    def display_name(self, obj):
        if obj.user:
            return obj.user.display_name
        return f"Operator #{obj.pk}"

    @admin.display(description="Telefon")
    def phone_number(self, obj):
        if obj.user:
            return obj.user.phone_number
        return None


@admin.register(User)
class UserAdmin(AdminUiResponseMixin, BaseUserAdmin):
    admin_page_title = "Foydalanuvchilar"
    admin_page_subtitle = "Login va ruxsatlarni boshqarish sahifasi."
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ("id", "phone_number", "display_name", "email", "role", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "is_superuser", "role", "gender")
    search_fields = ("phone_number", "phone_number2", "full_name", "first_name", "last_name", "email")
    search_help_text = "User ni telefon, ism yoki email bo'yicha qidiring."
    ordering = ("id",)
    list_per_page = 25
    save_on_top = True
    empty_value_display = "-"
    date_hierarchy = "date_joined"
    fieldsets = (
        ("Login ma'lumotlari", {"fields": ("phone_number", "phone_number2", "password")}),
        ("Shaxsiy ma'lumotlar", {
            "fields": ("full_name", "first_name", "last_name", "email", "role", "gender", "birthday"),
        }),
        ("Ruxsatlar", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Muhim sanalar", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone_number", "full_name", "first_name", "last_name", "email", "role", "password1", "password2"),
        }),
    )

    @admin.display(description="F.I.Sh.", ordering="full_name")
    def display_name(self, obj):
        return obj.get_full_name() or "-"


def _register_all_models():
    app_config = django_apps.get_app_config("user")
    for model in app_config.get_models():
        try:
            admin.site.register(model)
        except AlreadyRegistered:
            pass


_register_all_models()
