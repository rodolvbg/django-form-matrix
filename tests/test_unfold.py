import pytest
from demo.models import Plan
from django.contrib import admin

# The tox environments without django-unfold skip it (see "-unfold" ones).
pytest.importorskip("unfold")

from unfold.admin import ModelAdmin  # noqa: E402

from django_form_matrix.contrib.unfold import UnfoldMatrixMixin  # noqa: E402


class TestUnfoldMatrixMixin:
    """The django-unfold admin mixin."""

    def test_the_mixin_adds_the_unfold_palette(self):
        class PlanAdmin(UnfoldMatrixMixin, ModelAdmin):
            pass

        media = str(PlanAdmin(Plan, admin.site).media)
        assert "django_form_matrix/css/unfold.css" in media
