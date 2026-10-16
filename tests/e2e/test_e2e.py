"""
Real end-to-end tests: an actual Chromium against a real Django server, to see
the shortcuts of the matrix and the saving of its cells working together.
"""

import pytest
from demo.models import Plan, Role
from django.contrib.auth.models import User
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def admin_page(live_server, page: Page) -> Page:
    User.objects.create_superuser("admin", "admin@example.com", "password")
    page.goto(f"{live_server.url}/admin/login/")
    page.fill("#id_username", "admin")
    page.fill("#id_password", "password")
    page.click("input[type=submit]")
    expect(page.locator("#site-name")).to_be_visible()
    return page


def test_plan_matrix_is_filled_and_saved(live_server, admin_page: Page):
    page = admin_page
    page.goto(f"{live_server.url}/admin/demo/plan/add/")
    page.fill("#id_name", "Pro")

    billing = page.locator("details.form-matrix-section", has_text="Billing")
    billing.locator("summary").click()
    billing.locator("[data-form-matrix-toggle=column][data-column='0']").check()
    expect(billing.locator("[data-form-matrix-count]")).to_have_text("2/2")
    page.fill("input[name=features__invoices__limit]", "50")
    page.select_option("select[name=features__invoices__support]", "email")
    page.click("[name=_save]")

    plan = Plan.objects.get(name="Pro")
    assert plan.features["invoices"] == {
        "enabled": True,
        "limit": 50,
        "support": "email",
    }
    assert plan.features["quotes"]["enabled"] is True
    assert plan.features["reports"]["enabled"] is False
    assert plan.features["exports"] == {"enabled": False}


def test_plan_matrix_reports_the_cell_that_fails(live_server, admin_page: Page):
    page = admin_page
    page.goto(f"{live_server.url}/admin/demo/plan/add/")
    page.fill("#id_name", "Bad")
    page.locator("details.form-matrix-section", has_text="Billing").locator(
        "summary"
    ).click()
    page.fill("input[name=features__invoices__limit]", "-3")
    page.click("[name=_save]")

    expect(page.locator(".errorlist")).to_contain_text("Invoices, Monthly limit")
    assert not Plan.objects.exists()


def test_permission_shortcuts(live_server, admin_page: Page):
    page = admin_page
    page.goto(f"{live_server.url}/admin/demo/role/add/")
    page.fill("#id_name", "Reader")

    demo = page.locator("details.form-matrix-section", has_text="Demo")
    demo.locator("summary").click()
    demo.locator("[data-form-matrix-toggle=column][data-column=view]").check()
    expect(demo.locator("[data-form-matrix-count]")).to_have_text("2/8")
    demo.locator("tr", has_text="Plan").locator("[data-form-matrix-toggle=row]").check()
    expect(demo.locator("[data-form-matrix-count]")).to_have_text("5/8")
    page.click("[name=_save]")

    codenames = set(
        Role.objects.get(name="Reader").permissions.values_list("codename", flat=True)
    )
    assert codenames == {
        "add_plan",
        "view_plan",
        "change_plan",
        "delete_plan",
        "view_role",
    }
