from django.conf import settings
from django.contrib import admin

from django_form_matrix.contrib.permissions import PermissionMultipleChoiceField

from .forms import PlanForm
from .models import Plan, Role

if "unfold" in settings.INSTALLED_APPS:
    from unfold.admin import ModelAdmin

    from django_form_matrix.contrib.unfold import UnfoldMatrixMixin

    class BaseAdmin(UnfoldMatrixMixin, ModelAdmin):
        pass

else:

    class BaseAdmin(admin.ModelAdmin):  # type: ignore[no-redef]
        pass


@admin.register(Plan)
class PlanAdmin(BaseAdmin):
    form = PlanForm
    list_display = ["name"]


@admin.register(Role)
class RoleAdmin(BaseAdmin):
    list_display = ["name"]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "permissions":
            kwargs["form_class"] = PermissionMultipleChoiceField
        return super().formfield_for_manytomany(db_field, request, **kwargs)
