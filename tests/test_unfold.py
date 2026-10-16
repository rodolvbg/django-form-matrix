from demo.models import Plan
from django.contrib import admin
from unfold.admin import ModelAdmin

from django_form_matrix.contrib.unfold import UnfoldMatrixMixin


def test_the_mixin_adds_the_unfold_palette():
    class PlanAdmin(UnfoldMatrixMixin, ModelAdmin):
        pass

    media = str(PlanAdmin(Plan, admin.site).media)
    assert "django_form_matrix/css/unfold.css" in media
