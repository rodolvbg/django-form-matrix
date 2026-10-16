"""
A form field to fill a table: one row per item, one column per property and,
in every cell, a form field of its own (a checkbox, a number, a choice...).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django_form_matrix.widgets import MatrixWidget

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Mapping


def _boolean() -> forms.Field:
    return forms.BooleanField(required=False)


@dataclass(frozen=True)
class Column:
    """
    A column and the form field that is in each of its cells (a checkbox
    unless said otherwise). Checkbox columns get a shortcut to check them all.
    """

    key: str
    label: Any
    field: forms.Field = field(default_factory=_boolean)

    @property
    def is_checkbox(self) -> bool:
        return isinstance(self.field.widget, forms.CheckboxInput)


@dataclass(frozen=True)
class Row:
    """
    A row, optionally inside a collapsible ``section``. ``columns`` are the keys
    of the columns that have a cell in this row (all of them if it is None).
    """

    key: str
    label: Any
    section: Any = None
    columns: Collection[str] | None = None

    def __post_init__(self) -> None:
        if self.columns is not None:
            object.__setattr__(self, "columns", frozenset(self.columns))

    def has(self, column: str) -> bool:
        return self.columns is None or column in self.columns


class MatrixField(forms.Field):
    """
    Its value is ``{row key: {column key: cleaned value of the cell}}``, with
    only the cells that exist. Each cell is cleaned by the field of its column,
    so its validation and its widget are the ones of Django; a cell that fails
    reports its row and column. It is not required by default; when it is, at
    least one cell must have a value.
    """

    widget = MatrixWidget
    default_error_messages = {
        "cell": _("%(row)s, %(column)s: %(error)s"),
    }

    def __init__(
        self,
        *,
        rows: Iterable[Row],
        columns: Iterable[Column],
        required: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(required=required, **kwargs)
        self.rows = rows
        self.columns = columns

    @property
    def rows(self) -> tuple[Row, ...]:
        return self._rows

    @rows.setter
    def rows(self, rows: Iterable[Row]) -> None:
        rows = tuple(rows)
        self._check_unique("row", [row.key for row in rows])
        self._rows = rows
        self.widget.rows = rows

    @property
    def columns(self) -> tuple[Column, ...]:
        return self._columns

    @columns.setter
    def columns(self, columns: Iterable[Column]) -> None:
        columns = tuple(columns)
        self._check_unique("column", [column.key for column in columns])
        self._columns = columns
        self.widget.columns = columns

    @staticmethod
    def _check_unique(kind: str, keys: list[str]) -> None:
        if len(set(keys)) != len(keys):
            raise ValueError(f"The keys of the {kind}s of a matrix must be unique.")

    def clean(self, value: Mapping[str, Mapping[str, Any]] | None) -> dict[str, Any]:
        value = value or {}
        cleaned: dict[str, dict[str, Any]] = {}
        errors: list[ValidationError] = []
        for row in self.rows:
            cells = cleaned[row.key] = {}
            for column in self.columns:
                if not row.has(column.key):
                    continue
                raw = value.get(row.key, {}).get(column.key)
                try:
                    cells[column.key] = column.field.clean(raw)
                except ValidationError as error:
                    errors.extend(
                        ValidationError(
                            self.error_messages["cell"],
                            code="cell",
                            params={
                                "row": row.label,
                                "column": column.label,
                                "error": message,
                            },
                        )
                        for message in error.messages
                    )
        if errors:
            raise ValidationError(errors)
        if self.required and not any(
            cell for cells in cleaned.values() for cell in cells.values()
        ):
            raise ValidationError(self.error_messages["required"], code="required")
        self.run_validators(cleaned)
        return cleaned

    def has_changed(self, initial: Any, data: Any) -> bool:
        initial = initial or {}
        data = data or {}
        return any(
            column.field.has_changed(
                initial.get(row.key, {}).get(column.key),
                data.get(row.key, {}).get(column.key),
            )
            for row in self.rows
            for column in self.columns
            if row.has(column.key)
        )
