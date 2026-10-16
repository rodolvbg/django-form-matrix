import re

import pytest
from demo.dynamic_permissions import RolePermissionsForm
from demo.models import Role
from django.contrib.auth.models import Permission

pytestmark = pytest.mark.django_db


def cell(model, action):
    permission = Permission.objects.get(
        content_type__app_label="demo", codename=f"{action}_{model}"
    )
    return f"permissions__{permission.content_type_id}__{action}"


def test_rows_come_from_the_models_with_their_actions():
    form = RolePermissionsForm()
    rows = {row.label: row for row in form.fields["permissions"].rows}
    assert rows["Plan"].section == "Demo"
    assert set(rows["Plan"].columns) == {"add", "view", "change", "delete"}


def test_saves_the_chosen_permissions():
    form = RolePermissionsForm(
        data={
            "name": "Reader",
            cell("plan", "view"): "on",
            cell("plan", "change"): "on",
            cell("role", "view"): "on",
        }
    )
    assert form.is_valid(), form.errors
    role = form.save()
    assert set(role.permissions.values_list("codename", flat=True)) == {
        "view_plan",
        "change_plan",
        "view_role",
    }


def test_shows_and_changes_the_permissions_of_a_role():
    role = Role.objects.create(name="Reader")
    role.permissions.set(Permission.objects.filter(codename="view_plan"))

    form = RolePermissionsForm(instance=role)
    [plan_id] = [
        key
        for key, cells in form.fields["permissions"].initial.items()
        if "view" in cells
    ]
    assert form.fields["permissions"].initial == {plan_id: {"view": True}}
    html = str(form["permissions"])
    assert re.search(rf'name="permissions__{plan_id}__view"[^>]*checked', html)
    assert not re.search(rf'name="permissions__{plan_id}__add"[^>]*checked', html)

    change = RolePermissionsForm(
        data={"name": "Reader", cell("role", "add"): "on"}, instance=role
    )
    assert change.is_valid()
    change.save()
    assert list(role.permissions.values_list("codename", flat=True)) == ["add_role"]


def test_with_commit_false_the_permissions_wait_for_save_m2m():
    form = RolePermissionsForm(data={"name": "Later", cell("plan", "add"): "on"})
    assert form.is_valid()
    role = form.save(commit=False)
    role.save()
    assert not role.permissions.exists()
    form.save_m2m()
    assert list(role.permissions.values_list("codename", flat=True)) == ["add_plan"]


def test_the_admin_can_hand_the_user_to_the_form():
    # The pattern of docs/examples/permissions.md: a subclass, not a partial,
    # so the admin finds ``base_fields`` in the class it gets.
    from django.contrib import admin
    from django.contrib.auth.models import User
    from django.test import RequestFactory

    class UserRolePermissionsForm(RolePermissionsForm):
        def __init__(self, *args, user, **kwargs):
            super().__init__(*args, **kwargs)
            self.user = user

    class RoleAdmin(admin.ModelAdmin):
        form = UserRolePermissionsForm

        def get_form(self, request, obj=None, **kwargs):
            form = super().get_form(request, obj, **kwargs)

            class UserForm(form):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, user=request.user, **kwargs)

            return UserForm

    request = RequestFactory().get("/")
    request.user = User.objects.create_superuser("root", "r@example.com", "x")
    model_admin = RoleAdmin(Role, admin.site)

    [(_, options)] = model_admin.get_fieldsets(request)
    assert options["fields"] == ["name", "permissions"]  # the matrix is declared
    assert model_admin.get_form(request)().user == request.user
