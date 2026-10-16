from django.contrib import admin

from django_form_matrix.contrib.permissions import PermissionMultipleChoiceField

from .forms import PlanForm
from .models import Plan, Role


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    form = PlanForm
    list_display = ["name"]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name"]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "permissions":
            kwargs["form_class"] = PermissionMultipleChoiceField
        return super().formfield_for_manytomany(db_field, request, **kwargs)
