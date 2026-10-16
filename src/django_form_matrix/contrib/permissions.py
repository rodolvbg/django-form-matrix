"""
Permissions in a matrix: one collapsible section per app, one row per model and
a column per basic action (add, view, change, delete), with the other
permissions of the model at the end of its row. Django stores the name of each
permission ("Can add invoice") in English when creating it; here they are shown
translated.

It needs ``django.contrib.auth``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from django import forms
from django.utils.text import capfirst
from django.utils.translation import gettext, pgettext_lazy
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django.contrib.auth.models import Permission
    from django.db.models import QuerySet

ACTIONS = {
    "add": _("Can add %(model)s"),
    "change": _("Can change %(model)s"),
    "delete": _("Can delete %(model)s"),
    "view": _("Can view %(model)s"),
}
# Columns of the matrix, in the order they are shown.
ACTION_COLUMNS = (
    ("add", pgettext_lazy("permission", "Add")),
    ("view", pgettext_lazy("permission", "View")),
    ("change", pgettext_lazy("permission", "Change")),
    ("delete", pgettext_lazy("permission", "Delete")),
)


@dataclass(frozen=True)
class PermissionParts:
    """Where a permission belongs and what it allows, translated."""

    app: str
    model: str
    action: str | None  # "add", "change"... for the basic ones
    name: str


def permission_parts(permission: Permission) -> PermissionParts:
    content_type = permission.content_type
    model = content_type.model_class()
    if model is None:  # permission of a removed model
        return PermissionParts(
            content_type.app_label, content_type.model, None, permission.name
        )
    opts = model._meta
    action, _separator, model_name = permission.codename.partition("_")
    if action in ACTIONS and model_name == opts.model_name:
        return PermissionParts(
            str(capfirst(opts.app_config.verbose_name)),
            str(capfirst(opts.verbose_name)),
            action,
            ACTIONS[action] % {"model": opts.verbose_name},
        )
    return PermissionParts(
        str(capfirst(opts.app_config.verbose_name)),
        str(capfirst(opts.verbose_name)),
        None,
        gettext(permission.name),
    )


def permission_label(permission: Permission) -> str:
    """ "App | Model | Can add model", translated like the rest of the admin."""
    if permission.content_type.model_class() is None:
        return str(permission)
    parts = permission_parts(permission)
    return f"{parts.app} | {parts.model} | {parts.name}"


@dataclass
class PermissionRow:
    model: str
    cells: dict[str, dict[str, Any]] = field(default_factory=dict)
    others: list[dict[str, Any]] = field(default_factory=list)

    @property
    def columns(self) -> list[tuple[str, dict[str, Any] | None]]:
        return [(action, self.cells.get(action)) for action, _label in ACTION_COLUMNS]


@dataclass
class PermissionApp:
    name: str
    rows: dict[str, PermissionRow] = field(default_factory=dict)

    @property
    def options(self) -> list[dict[str, Any]]:
        return [
            option
            for row in self.rows.values()
            for option in [*row.cells.values(), *row.others]
        ]

    @property
    def has_others(self) -> bool:
        return any(row.others for row in self.rows.values())

    @property
    def checked(self) -> int:
        return sum(option["checked"] for option in self.options)

    @property
    def total(self) -> int:
        return len(self.options)


class PermissionMatrixWidget(forms.CheckboxSelectMultiple):
    """
    Permissions as a matrix (see the module docstring). It submits like a
    CheckboxSelectMultiple, so validation and saving do not change; only the
    permissions of the queryset of the field are shown.
    """

    template_name = "django_form_matrix/permissions.html"

    class Media:
        css = {"all": ("django_form_matrix/css/matrix.css",)}
        js = ("django_form_matrix/js/matrix.js",)

    def get_context(self, name: str, value: Any, attrs: Any) -> dict[str, Any]:
        context = super().get_context(name, value, attrs)
        selected = {str(item) for item in value or []}
        apps: dict[str, PermissionApp] = {}
        # Choices of a ModelMultipleChoiceField: no empty one, and each value
        # carries its permission.
        for choice, _label in self.choices:
            permission = choice.instance  # type: ignore[union-attr]
            parts = permission_parts(permission)
            row = apps.setdefault(parts.app, PermissionApp(parts.app)).rows.setdefault(
                parts.model, PermissionRow(parts.model)
            )
            option = {
                "value": permission.pk,
                "id": f"{context['widget']['attrs'].get('id', name)}_{permission.pk}",
                "label": parts.name,
                "checked": str(permission.pk) in selected,
            }
            if parts.action:
                row.cells[parts.action] = option
            else:
                row.others.append(option)
        context["widget"].update(
            {
                "apps": [
                    PermissionApp(app.name, dict(sorted(app.rows.items())))
                    for app in sorted(apps.values(), key=lambda app: app.name)
                ],
                "columns": ACTION_COLUMNS,
                "disabled": bool(context["widget"]["attrs"].get("disabled")),
            }
        )
        return context


class PermissionMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Permissions labelled with their translated names, chosen in a matrix."""

    widget = PermissionMatrixWidget

    def __init__(self, queryset: QuerySet[Permission], **kwargs: Any) -> None:
        kwargs["widget"] = PermissionMatrixWidget
        super().__init__(queryset.select_related("content_type"), **kwargs)

    def label_from_instance(self, obj: Any) -> str:
        return permission_label(obj)
