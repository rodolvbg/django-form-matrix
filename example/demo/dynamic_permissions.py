"""
The permission matrix built by hand with ``MatrixField``, to show how any
matrix is made dynamically (see docs/examples/permissions.md): its rows come
from the models of the project and its value is saved on a many-to-many.
"""

from django import forms
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.text import capfirst

from django_form_matrix import Column, MatrixField, Row

from .models import Role

ACTIONS = {
    "add": "Add",
    "view": "View",
    "change": "Change",
    "delete": "Delete",
}


class RolePermissionsForm(forms.ModelForm):
    permissions = MatrixField(
        rows=[],  # one per model, in __init__: they depend on the database
        columns=[Column(action, label) for action, label in ACTIONS.items()],
        required=False,
    )

    class Meta:
        model = Role
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        codenames = set(Permission.objects.values_list("codename", flat=True))
        rows = []
        self.model_names = {}
        for content_type in ContentType.objects.order_by("app_label", "model"):
            model = content_type.model_class()
            if model is None:  # a model that no longer exists
                continue
            self.model_names[str(content_type.pk)] = content_type.model
            rows.append(
                Row(
                    str(content_type.pk),
                    capfirst(model._meta.verbose_name),
                    section=capfirst(model._meta.app_config.verbose_name),
                    # only the actions this model has a permission for
                    columns=[
                        action
                        for action in ACTIONS
                        if f"{action}_{content_type.model}" in codenames
                    ],
                )
            )
        self.fields["permissions"].rows = rows
        if self.instance.pk:
            self.fields["permissions"].initial = self.initial_permissions()

    def initial_permissions(self):
        initial = {}
        for permission in self.instance.permissions.all():
            action, _, _model = permission.codename.partition("_")
            if action in ACTIONS:
                initial.setdefault(str(permission.content_type_id), {})[action] = True
        return initial

    def _save_m2m(self):
        # Runs after the role is saved, also with ``save(commit=False)`` and
        # ``save_m2m()``; the field is not a model field, so it is done here.
        super()._save_m2m()
        wanted = Q(pk__in=[])
        for content_type_id, cells in self.cleaned_data["permissions"].items():
            model_name = self.model_names[content_type_id]
            for action, on in cells.items():
                if on:
                    wanted |= Q(
                        content_type_id=content_type_id,
                        codename=f"{action}_{model_name}",
                    )
        self.instance.permissions.set(Permission.objects.filter(wanted))
