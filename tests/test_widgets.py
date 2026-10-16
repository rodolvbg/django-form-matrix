from django import forms
from django.utils.datastructures import MultiValueDict

from django_form_matrix import Column, MatrixField, Row


def matrix(**kwargs):
    return MatrixField(
        rows=[
            Row("inv", "Invoices", section="Billing"),
            Row("quo", "Quotes", section="Billing"),
            Row("exp", "Exports", section="Analytics", columns=["on"]),
        ],
        columns=[
            Column("on", "On"),
            Column("limit", "Limit", forms.IntegerField(required=False)),
        ],
        **kwargs,
    )


def test_cells_are_submitted_on_their_own():
    widget = matrix().widget
    data = MultiValueDict({"m__inv__on": ["on"], "m__inv__limit": ["7"]})
    assert widget.value_from_datadict(data, {}, "m") == {
        "inv": {"on": True, "limit": "7"},
        "quo": {"on": False, "limit": None},
        "exp": {"on": False},
    }


def test_never_omitted_while_it_has_checkboxes():
    widget = matrix().widget
    assert not widget.value_omitted_from_data({}, {}, "m")
    empty = MatrixField(
        rows=[Row("a", "A")], columns=[Column("n", "N", forms.CharField())]
    )
    assert empty.widget.value_omitted_from_data({}, {}, "m")


def test_sections_group_the_rows_in_order():
    context = matrix().widget.get_context("m", {}, {"id": "id_m"})["widget"]
    assert [section.name for section in context["sections"]] == ["Billing", "Analytics"]
    billing, analytics = context["sections"]
    assert [row["label"] for row in billing.rows] == ["Invoices", "Quotes"]
    assert [row["label"] for row in analytics.rows] == ["Exports"]


def test_counts_only_checkboxes():
    value = {"inv": {"on": True, "limit": 3}, "exp": {"on": True}}
    billing, analytics = matrix().widget.get_context("m", value, {})["widget"][
        "sections"
    ]
    assert (billing.checked, billing.total) == (1, 2)
    assert (analytics.checked, analytics.total) == (1, 1)
    assert billing.is_open


def test_render():
    value = {"inv": {"on": True, "limit": 3}}
    html = matrix().widget.render("m", value, {"id": "id_m"})
    assert '<details class="form-matrix-section" open>' in html
    assert 'name="m__inv__on"' in html
    assert 'name="m__inv__limit"' in html
    assert 'value="3"' in html
    assert 'id="id_m_0_0"' in html
    assert 'aria-label="Invoices: Limit"' in html
    assert 'data-form-matrix-toggle="section"' in html
    assert 'data-form-matrix-toggle="row"' in html
    assert 'data-form-matrix-toggle="column" data-column="0"' in html
    # only the checkbox column has a shortcut
    assert 'data-form-matrix-toggle="column" data-column="1"' not in html
    assert "—" in html  # Exports has no limit cell


def test_checked_boxes_render_checked():
    html = matrix().widget.render("m", {"quo": {"on": True}})
    [quotes] = [part for part in html.split("<tr>") if "Quotes" in part]
    assert " checked" in quotes
    [invoices] = [part for part in html.split("<tr>") if "Invoices" in part]
    assert " checked" not in invoices


def test_a_matrix_without_sections():
    flat = MatrixField(rows=[Row("a", "A")], columns=[Column("on", "On")])
    html = flat.widget.render("m", {})
    assert "<details" not in html
    assert '<div class="form-matrix-section">' in html
    assert "data-form-matrix-count" not in html


def test_sections_without_checkboxes_are_open_and_have_no_shortcuts():
    text = MatrixField(
        rows=[Row("a", "A", section="S")],
        columns=[Column("n", "N", forms.CharField())],
    )
    html = text.widget.render("m", {})
    assert '<details class="form-matrix-section" open>' in html
    assert "data-form-matrix-toggle" not in html


def test_disabled_has_no_shortcuts():
    html = matrix().widget.render("m", {"inv": {"on": True}}, {"disabled": True})
    assert "data-form-matrix-toggle" not in html
    assert html.count("disabled") >= 4


def test_nothing_to_show():
    empty = MatrixField(rows=[], columns=[Column("on", "On")])
    assert empty.widget.render("m", {}).count("<table") == 0


def test_media():
    media = str(matrix().widget.media)
    assert "django_form_matrix/css/matrix.css" in media
    assert "django_form_matrix/js/matrix.js" in media


def test_rerenders_what_was_submitted():
    class MatrixForm(forms.Form):
        grid = matrix()

    form = MatrixForm(data={"grid__inv__on": "on", "grid__inv__limit": "x"})
    assert not form.is_valid()
    html = str(form["grid"])
    assert 'value="x"' in html


def test_a_section_is_open_when_any_cell_in_it_is_filled():
    billing, analytics = matrix().widget.get_context("m", {"inv": {"limit": 3}}, {})[
        "widget"
    ]["sections"]
    assert billing.is_open
    assert not analytics.is_open
    assert (billing.checked, billing.total) == (0, 2)
    closed = matrix().widget.get_context("m", {}, {})["widget"]["sections"]
    assert not any(section.is_open for section in closed)
