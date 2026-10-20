from typing import Any

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import translation

from django_form_matrix.contrib.permissions import (
    PermissionMultipleChoiceField,
    permission_label,
)

pytestmark = pytest.mark.django_db


def permission(app_label, codename):
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


def context(queryset, value=()):
    widget: Any = PermissionMultipleChoiceField(queryset=queryset).widget
    return widget.get_context("permissions", list(value), {"id": "id_p"})["widget"]


class TestPermissionLabel:
    """Naming permissions."""

    def test_default_permissions_are_named_from_the_model(self):
        assert permission_label(permission("demo", "view_plan")) == (
            "Demo | Plan | Can view plan"
        )

    def test_default_permissions_are_translated(self):
        with translation.override("es"):
            label = permission_label(permission("demo", "view_plan"))
        assert label.startswith("Demo | Plan | ")

    def test_custom_permissions_keep_their_name(self):
        custom = Permission.objects.create(
            content_type=ContentType.objects.get_for_model(Permission),
            codename="audit_everything",
            name="Audit",
        )
        assert permission_label(custom).endswith("| Audit")

    def test_permissions_of_removed_models(self):
        stale = ContentType.objects.create(app_label="gone", model="thing")
        gone = Permission.objects.create(
            content_type=stale, codename="add_thing", name="Can add thing"
        )
        assert permission_label(gone) == str(gone)
        [app] = context(Permission.objects.filter(pk=gone.pk))["apps"]
        assert (app.name, list(app.rows)) == ("gone", ["thing"])
        assert app.rows["thing"].others[0]["label"] == "Can add thing"

    def test_the_form_field_uses_the_label(self):
        field = PermissionMultipleChoiceField(queryset=Permission.objects.all())
        view = permission("demo", "view_plan")
        assert field.label_from_instance(view) == permission_label(view)


class TestPermissionMultipleChoiceField:
    """The permission matrix field and its widget."""

    def test_apps_models_and_actions(self):
        demo = Permission.objects.filter(content_type__app_label="demo")
        view = permission("demo", "view_plan")

        widget = context(demo, [view.pk])

        [app] = widget["apps"]
        assert app.name == "Demo"
        assert list(app.rows) == ["Plan", "Role"]
        plan = app.rows["Plan"]
        assert [action for action, _option in plan.columns] == [
            "add",
            "view",
            "change",
            "delete",
        ]
        assert plan.cells["view"]["checked"]
        assert not plan.cells["add"]["checked"]
        assert (app.checked, app.total) == (1, demo.count())
        assert not widget["disabled"]

    def test_other_permissions_of_a_model_go_at_the_end_of_its_row(self):
        ct = ContentType.objects.get(app_label="demo", model="plan")
        export = Permission.objects.create(
            content_type=ct, codename="export_plan", name="Can export plans"
        )
        [app] = context(Permission.objects.filter(content_type=ct))["apps"]
        plan = app.rows["Plan"]
        assert [option["value"] for option in plan.others] == [export.pk]
        assert app.has_others

    def test_only_the_permissions_offered(self):
        widget = context(
            Permission.objects.filter(codename__in=["view_plan", "add_user"])
        )
        assert [app.name for app in widget["apps"]] == [
            "Authentication and Authorization",
            "Demo",
        ]
        [_auth, demo] = widget["apps"]
        assert dict(demo.rows["Plan"].columns)["add"] is None

    def test_render(self):
        view = permission("demo", "view_plan")
        field = PermissionMultipleChoiceField(
            queryset=Permission.objects.filter(pk=view.pk)
        )
        html = field.widget.render("permissions", [view.pk], {"id": "id_p"})
        assert '<details class="form-matrix-section" open>' in html
        assert f'value="{view.pk}"' in html
        assert 'data-form-matrix-toggle="row"' in html
        assert "—" in html  # actions without permission

    def test_the_others_of_an_app_have_their_own_toggle(self):
        ct = ContentType.objects.get(app_label="demo", model="plan")
        Permission.objects.create(
            content_type=ct, codename="export_plan", name="Can export plans"
        )
        widget: Any = PermissionMultipleChoiceField(
            queryset=Permission.objects.filter(
                content_type__app_label__in=["demo", "auth"]
            )
        ).widget
        html = widget.render("p", [])
        toggle = 'data-form-matrix-toggle="column" data-column="others"'
        assert html.count(toggle) == 1  # only in Demo
        # Auth keeps the room of the checkbox, so its heading lines up.
        assert html.count('class="form-matrix-placeholder"') == 1

    def test_disabled(self):
        widget: Any = PermissionMultipleChoiceField(
            queryset=Permission.objects.all()
        ).widget
        html = widget.render("p", [], {"disabled": True})
        assert "data-form-matrix-toggle" not in html
        assert "disabled" in html

    def test_nothing_to_choose(self):
        field = PermissionMultipleChoiceField(queryset=Permission.objects.none())
        assert "No permissions available." in field.widget.render("p", [])

    def test_submits_like_checkboxes(self):
        view = permission("demo", "view_plan")
        field = PermissionMultipleChoiceField(queryset=Permission.objects.all())
        data = {"permissions": [str(view.pk)]}
        assert field.widget.value_from_datadict(data, {}, "permissions") == [
            str(view.pk)
        ]
        assert list(field.clean([str(view.pk)])) == [view]
