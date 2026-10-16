# Example: a permission matrix

The permission matrix is the use case this library came from. There are two ways to get it, depending on how much you need to change.

| | `contrib.permissions` | `MatrixField` by hand |
| --- | --- | --- |
| Setup | one line | a form (below) |
| Value | a `QuerySet` of `Permission`, like a `ModelMultipleChoiceField` | any dict you decide |
| Other permissions of a model (`export_invoice`) | an "Others" column | only the columns you declare |
| Names of the permissions | translated | your labels |
| Good for | groups, roles, users | the same grid over anything that is not a `Permission`, or with rules of your own |

## 1. Ready-made

```python
from django.contrib import admin
from django_form_matrix.contrib.permissions import PermissionMultipleChoiceField


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "permissions":
            kwargs["form_class"] = PermissionMultipleChoiceField
        return super().formfield_for_manytomany(db_field, request, **kwargs)
```

Outside the admin it is a normal form field. The `queryset` decides which permissions are offered, so this is also how you limit them:

```python
class RoleForm(forms.ModelForm):
    permissions = PermissionMultipleChoiceField(
        queryset=Permission.objects.filter(content_type__app_label="invoicing"),
        required=False,
    )

    class Meta:
        model = Role
        fields = ["name", "permissions"]
```

It submits like a `CheckboxSelectMultiple`, so validation and saving are Django's own.

![The permission matrix in the admin](../screenshots/permissions.png)

## 2. By hand, with `MatrixField`

The same grid built from the generic field. Everything that makes it dynamic happens in `__init__`: the rows depend on the models of the project, so they are not known when the class is defined.

The full code is in [example/demo/dynamic_permissions.py](../../example/demo/dynamic_permissions.py), with tests in [tests/test_dynamic_permissions.py](../../tests/test_dynamic_permissions.py).

### The field

Columns are fixed (the four actions); the rows start empty.

```python
ACTIONS = {"add": "Add", "view": "View", "change": "Change", "delete": "Delete"}


class RolePermissionsForm(forms.ModelForm):
    permissions = MatrixField(
        rows=[],  # one per model, in __init__
        columns=[Column(action, label) for action, label in ACTIONS.items()],
    )

    class Meta:
        model = Role
        fields = ["name"]  # "permissions" here is the matrix, not the model field
```

Each column is a checkbox, which is what `Column` makes unless you pass a field.

### The rows

One row per model, grouped in a section per app, with only the columns that model has a permission for (a model without `delete_x` shows a dash in that cell):

```python
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
                    columns=[
                        action
                        for action in ACTIONS
                        if f"{action}_{content_type.model}" in codenames
                    ],
                )
            )
        self.fields["permissions"].rows = rows
```

`rows` (and `columns`) can be reassigned on the field of a form instance; the widget follows. Nothing is shared between requests, because every form gets its own copy of its fields.

### What it shows

The value of the field is `{row key: {column key: bool}}`, so what a role already has is the same shape:

```python
        if self.instance.pk:
            self.fields["permissions"].initial = self.initial_permissions()

    def initial_permissions(self):
        initial = {}
        for permission in self.instance.permissions.all():
            action, _, _model = permission.codename.partition("_")
            if action in ACTIONS:
                initial.setdefault(str(permission.content_type_id), {})[action] = True
        return initial
```

### Saving

The matrix is not a model field, so the form saves it. `_save_m2m` runs after the role exists, both with `save()` and with `save(commit=False)` followed by `save_m2m()`:

```python
    def _save_m2m(self):
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
```

Use it in the admin like any form:

```python
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    form = RolePermissionsForm
```

### Changing the rows per request

Because the rows are plain Python, they can depend on anything: here, only the permissions the user giving them has. The form takes the user, and the `columns` of each row are filtered with it:

```python
class RolePermissionsForm(forms.ModelForm):
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        allowed = user.get_all_permissions()  # {"invoicing.view_invoice", ...}
        ...
        rows.append(
            Row(
                str(content_type.pk),
                capfirst(model._meta.verbose_name),
                section=capfirst(model._meta.app_config.verbose_name),
                columns=[
                    action
                    for action in ACTIONS
                    if f"{content_type.app_label}.{action}_{content_type.model}"
                    in allowed
                ],
            )
        )
```

In the admin, hand the user to the form from `get_form`. Return a subclass (the admin reads `base_fields` from the class it gets, so a `functools.partial` would not do):

```python
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        class UserForm(form):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, user=request.user, **kwargs)

        return UserForm
```

### Beyond permissions

Nothing above is specific to `Permission`. The same shape — rows from the database, columns from a fixed list, a value saved by the form — works for roles × modules, features per plan, notifications per channel and event... and the cells need not be checkboxes: give a `Column` a `forms.IntegerField` or a `ChoiceField` and the matrix holds limits or levels instead of yes/no.
