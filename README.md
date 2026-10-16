# django-form-matrix

[![Build status](https://github.com/rodolvbg/django-form-matrix/actions/workflows/pytest.yml/badge.svg)](https://github.com/rodolvbg/django-form-matrix/actions/workflows/pytest.yml)
[![PyPI version](https://img.shields.io/pypi/v/django-form-matrix.svg)](https://pypi.org/project/django-form-matrix/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-form-matrix)](https://pypi.org/project/django-form-matrix/)
[![PyPI - Django Version](https://img.shields.io/pypi/djversions/django-form-matrix)](https://pypi.org/project/django-form-matrix/)
[![Downloads](https://static.pepy.tech/personalized-badge/django-form-matrix?period=month&units=international_system&left_color=black&right_color=blue&left_text=Downloads/month)](https://pepy.tech/project/django-form-matrix)

A Django form field to fill a **table**: one row per item, one column per property and, in every cell, a form field of its own — a checkbox, a number, a choice, text. Rows can be grouped in collapsible sections, and checkbox columns get shortcuts to check a row, a column or a whole section.

It works in any Django form and in the admin. A ready-made **permission matrix** (apps → models → add/view/change/delete) is included as a use case.

![A matrix with checkboxes, numbers and choices in its cells, in two sections](docs/screenshots/hero.png)

## Installation

```bash
pip install django-form-matrix
```

Add `django_form_matrix` to `INSTALLED_APPS` (it ships a template, a script and a stylesheet):

```python
INSTALLED_APPS = [
    # ...
    "django_form_matrix",
]
```

## Quick start

```python
from django import forms
from django_form_matrix import Column, MatrixField, Row


class PlanForm(forms.Form):
    features = MatrixField(
        rows=[
            Row("invoices", "Invoices", section="Billing"),
            Row("quotes", "Quotes", section="Billing"),
            Row("exports", "Exports", section="Analytics", columns=["enabled"]),
        ],
        columns=[
            Column("enabled", "Enabled"),  # a checkbox unless said otherwise
            Column(
                "limit",
                "Monthly limit",
                forms.IntegerField(min_value=0, required=False),
            ),
        ],
    )
```

Render the form as usual and add `{{ form.media }}` (the admin does it for you). The cleaned value has one entry per row with the cells that exist:

```python
form.cleaned_data["features"]
# {"invoices": {"enabled": True, "limit": 50},
#  "quotes": {"enabled": False, "limit": None},
#  "exports": {"enabled": False}}
```

That is what a `JSONField` stores, so a `ModelForm` can save it directly.

### Rows and columns

- `Column(key, label, field=BooleanField(required=False))`: the form field of the column. Its validation and its widget are Django's own, and a failing cell is reported with its row and column ("Invoices, Monthly limit: …").
- `Row(key, label, section=None, columns=None)`: `section` groups rows under a collapsible heading (rows without one go in a plain table); `columns` are the keys of the columns that have a cell in this row, the rest show a dash.
- `MatrixField(rows=…, columns=…)` is not required by default; with `required=True` at least one cell needs a value. `rows` and `columns` can be reassigned in a form's `__init__` to build the matrix dynamically.

Each cell is submitted as `<name>__<row key>__<column key>`, so it reads like any other widget.

### Shortcuts

Checkbox columns get a checkbox in their heading, every row with checkboxes gets one at its start, and each section gets an "All". They show whether their cells are all, some or none checked, and the heading of a section counts the checked ones. A section opens by itself when something in it is filled.

## Permissions

```python
from django_form_matrix.contrib.permissions import PermissionMultipleChoiceField


class RoleAdmin(admin.ModelAdmin):
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "permissions":
            kwargs["form_class"] = PermissionMultipleChoiceField
        return super().formfield_for_manytomany(db_field, request, **kwargs)
```

![The permission matrix in the admin](docs/screenshots/permissions.png)

One section per app, one row per model and a column per action; the other permissions of a model go in an "Others" column. It submits like a `CheckboxSelectMultiple`, so validation and saving do not change, and the names of the permissions are shown translated. Needs `django.contrib.auth`. [docs/examples/permissions.md](docs/examples/permissions.md) shows how to build the same matrix by hand with `MatrixField`, with rows that come from the database, for when you need more control.

## Customizing the HTML

Both templates are split in blocks, so a template of yours can extend one and change only a piece, without copying the rest:

```django
{% extends "django_form_matrix/matrix.html" %}
{% block section_summary %}<strong>{{ section.name }}</strong>{% endblock %}
{% block cell %}<div class="my-cell">{{ cell.html }}</div>{% endblock %}
```

Point a widget to it with `template_name`:

```python
class MyMatrixWidget(MatrixWidget):
    template_name = "myapp/my_matrix.html"
```

| Block | `matrix.html` | `permissions.html` | What it is |
| --- | --- | --- | --- |
| `section_summary` | ✓ | ✓ | The heading of a section (its name and count) |
| `section_toggle` | ✓ | ✓ | The "All" checkbox of a section |
| `column_heading` | ✓ | ✓ | The heading of a column |
| `others_heading` | | ✓ | The heading of the "Others" column |
| `row_heading` | ✓ | ✓ | The heading of a row |
| `cell` | ✓ | | The widget of a cell (`{{ cell.html }}`) |
| `permission` | | ✓ | The checkbox of a permission |
| `other_permission` | | ✓ | A permission of the "Others" column |
| `missing_cell` | ✓ | ✓ | A cell a row does not have |
| `empty` | ✓ | ✓ | What shows when there is nothing to fill |

`{{ block.super }}` keeps the original of a block. The classes (`.form-matrix-*`) and the `data-form-matrix-*` attributes are what the stylesheet and the script look for: keep them in your blocks and the shortcuts keep working.

Django looks for the widget templates of a form in the `templates/` of the installed apps, **not** in the `DIRS` of your project. To override `django_form_matrix/matrix.html` itself by name from the project's templates, set `FORM_RENDERER = "django.forms.renderers.TemplatesSetting"`, or put the template in an app listed before `django_form_matrix` in `INSTALLED_APPS`. Extending it with your own `template_name`, as above, needs neither.

## Styling

The stylesheet uses the colours of the Django admin when it is there. Anywhere else, set `--form-matrix-border`, `--form-matrix-heading-bg` and `--form-matrix-quiet` on `.form-matrix`.

### Unfold

[django-unfold](https://github.com/unfoldadmin/django-unfold) does not define the variables of Django's admin, so add `UnfoldMatrixMixin` to the admin: it puts the matrix on Unfold's palette, light and dark, and styles the number, text and select cells like Unfold's own inputs.

```python
from unfold.admin import ModelAdmin
from django_form_matrix.contrib.unfold import UnfoldMatrixMixin


@admin.register(Plan)
class PlanAdmin(UnfoldMatrixMixin, ModelAdmin):
    form = PlanForm
```

![The matrix in Unfold](docs/screenshots/unfold.png)

The permission matrix, the use case this library started from, in Unfold:

![The permission matrix in Unfold](docs/screenshots/unfold-permissions.png)

And in Unfold's dark mode:

![The matrix in Unfold, dark](docs/screenshots/unfold-dark.png)

## Development

```bash
uv sync && npm install
uv run pytest            # Python + end-to-end (needs `uv run playwright install chromium`)
npm test                 # JS
cd example && uv run python manage.py runserver   # demo: Plans and Roles in the admin
DJANGO_SETTINGS_MODULE=example.settings_unfold uv run python manage.py runserver   # the same, in Unfold
```
