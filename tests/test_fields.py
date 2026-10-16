import pytest
from django import forms
from django.core.exceptions import ValidationError

from django_form_matrix import Column, MatrixField, Row


def field(**kwargs):
    return MatrixField(
        rows=[Row("a", "Alpha"), Row("b", "Beta", columns=["on"])],
        columns=[
            Column("on", "On"),
            Column("limit", "Limit", forms.IntegerField(min_value=0, required=False)),
        ],
        **kwargs,
    )


def test_cleans_every_cell_with_its_own_field():
    cleaned = field().clean(
        {"a": {"on": True, "limit": "5"}, "b": {"on": False}},
    )
    assert cleaned == {"a": {"on": True, "limit": 5}, "b": {"on": False}}


def test_rows_only_have_their_columns():
    cleaned = field().clean({"a": {"on": True, "limit": ""}, "b": {"limit": "9"}})
    assert cleaned["b"] == {"on": False}


def test_empty_value():
    assert field().clean(None) == {
        "a": {"on": False, "limit": None},
        "b": {"on": False},
    }


def test_a_failing_cell_names_its_row_and_column():
    with pytest.raises(ValidationError) as caught:
        field().clean({"a": {"on": True, "limit": "-1"}})
    [message] = caught.value.messages
    assert message.startswith("Alpha, Limit: ")
    assert "greater than or equal to 0" in message


def test_every_failing_cell_is_reported():
    with pytest.raises(ValidationError) as caught:
        field().clean({"a": {"limit": "x"}})
    assert len(caught.value.messages) == 1
    with pytest.raises(ValidationError) as caught:
        MatrixField(
            rows=[Row("a", "A")],
            columns=[
                Column("x", "X", forms.IntegerField()),
                Column("y", "Y", forms.IntegerField()),
            ],
        ).clean({})
    assert len(caught.value.messages) == 2


def test_not_required_by_default():
    assert not field().required


def test_required_asks_for_a_cell_with_a_value():
    required = field(required=True)
    with pytest.raises(ValidationError) as caught:
        required.clean({"a": {"on": False}})
    assert caught.value.code == "required"
    assert required.clean({"a": {"on": True}})["a"]["on"] is True


def test_field_validators_run_on_the_value():
    def at_most_one(value):
        if sum(cell["on"] for cell in value.values()) > 1:
            raise ValidationError("one at most")

    with pytest.raises(ValidationError, match="one at most"):
        field(validators=[at_most_one]).clean({"a": {"on": True}, "b": {"on": True}})


def test_keys_must_be_unique():
    with pytest.raises(ValueError, match="rows"):
        MatrixField(rows=[Row("a", "A"), Row("a", "B")], columns=[])
    with pytest.raises(ValueError, match="columns"):
        MatrixField(rows=[], columns=[Column("a", "A"), Column("a", "B")])


def test_rows_and_columns_can_change_after_creating_the_field():
    matrix = field()
    matrix.rows = [Row("z", "Zeta")]
    matrix.columns = [Column("on", "On")]
    assert matrix.widget.rows == matrix.rows  # type: ignore[attr-defined]
    assert matrix.widget.columns == matrix.columns  # type: ignore[attr-defined]
    assert matrix.clean({"z": {"on": True}}) == {"z": {"on": True}}


def test_has_changed_compares_cell_by_cell():
    matrix = field()
    initial = {"a": {"on": True, "limit": 5}}
    same = {"a": {"on": True, "limit": "5"}, "b": {"on": False}}
    assert not matrix.has_changed(initial, same)
    assert matrix.has_changed(initial, {"a": {"on": True, "limit": "6"}})
    assert matrix.has_changed(None, {"b": {"on": True}})
    assert not matrix.has_changed(None, None)


def test_column_knows_if_it_is_a_checkbox():
    assert Column("a", "A").is_checkbox
    assert not Column("a", "A", forms.IntegerField()).is_checkbox


def test_a_form_with_the_field():
    class MatrixForm(forms.Form):
        grid = MatrixField(rows=[Row("a", "A")], columns=[Column("on", "On")])

    form = MatrixForm(data={"grid__a__on": "on"})
    assert form.is_valid()
    assert form.cleaned_data["grid"] == {"a": {"on": True}}
    assert MatrixForm(data={}).is_valid()
    initial = {"grid": {"a": {"on": True}}}
    assert not MatrixForm(data={"grid__a__on": "on"}, initial=initial).has_changed()
    assert MatrixForm(data={}, initial=initial).has_changed()
