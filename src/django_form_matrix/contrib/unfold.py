"""django-unfold integration."""

from django.forms import Media


class UnfoldMatrixMixin:
    """
    Puts the matrix on Unfold's palette (light and dark)::

        from unfold.admin import ModelAdmin

        class PlanAdmin(UnfoldMatrixMixin, ModelAdmin):
            form = PlanForm
    """

    @property
    def media(self) -> Media:
        return super().media + Media(  # type: ignore[misc]
            css={"all": ("django_form_matrix/css/unfold.css",)},
        )


__all__ = ["UnfoldMatrixMixin"]
