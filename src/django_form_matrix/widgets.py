from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from django import forms

if TYPE_CHECKING:
    from django_form_matrix.fields import Column, Row


@dataclass
class Section:
    """The rows under one heading; the ones without section go together."""

    name: Any
    rows: list[dict[str, Any]] = field(default_factory=list)

    @property
    def checkboxes(self) -> list[dict[str, Any]]:
        return [
            cell
            for row in self.rows
            for cell in row["cells"]
            if cell["checkbox"] and cell["html"]
        ]

    @property
    def has_checkboxes(self) -> bool:
        return bool(self.checkboxes)

    @property
    def checked(self) -> int:
        return sum(cell["checked"] for cell in self.checkboxes)

    @property
    def total(self) -> int:
        return len(self.checkboxes)

    @property
    def is_open(self) -> bool:
        # Open when something in it is filled (also when it fails), and when
        # it has no checkboxes to count.
        return not self.total or any(
            cell["filled"] for row in self.rows for cell in row["cells"]
        )


class MatrixWidget(forms.Widget):
    """
    A table with the widget of each column in every cell. Every cell is
    submitted on its own, as ``<name>__<row key>__<column key>``, so it reads
    like any other widget; the value is ``{row key: {column key: raw value}}``.
    """

    template_name = "django_form_matrix/matrix.html"

    class Media:
        css = {"all": ("django_form_matrix/css/matrix.css",)}
        js = ("django_form_matrix/js/matrix.js",)

    def __init__(
        self,
        attrs: dict[str, Any] | None = None,
        rows: tuple[Row, ...] = (),
        columns: tuple[Column, ...] = (),
    ) -> None:
        super().__init__(attrs)
        self.rows = rows
        self.columns = columns

    @staticmethod
    def cell_name(name: str, row: Row, column: Column) -> str:
        return f"{name}__{row.key}__{column.key}"

    def value_from_datadict(
        self, data: Any, files: Any, name: str
    ) -> dict[str, dict[str, Any]]:
        return {
            row.key: {
                column.key: column.field.widget.value_from_datadict(
                    data, files, self.cell_name(name, row, column)
                )
                for column in self.columns
                if row.has(column.key)
            }
            for row in self.rows
        }

    def value_omitted_from_data(self, data: Any, files: Any, name: str) -> bool:
        return all(
            column.field.widget.value_omitted_from_data(
                data, files, self.cell_name(name, row, column)
            )
            for row in self.rows
            for column in self.columns
            if row.has(column.key)
        )

    def format_value(self, value: Any) -> Any:
        return value

    def get_context(self, name: str, value: Any, attrs: Any) -> dict[str, Any]:
        context = super().get_context(name, value, attrs)
        widget = context["widget"]
        value = value or {}
        base_id = widget["attrs"].get("id") or f"id_{name}"
        disabled = bool(widget["attrs"].get("disabled"))
        sections: dict[Any, Section] = {}
        for i, row in enumerate(self.rows):
            cells = []
            for j, column in enumerate(self.columns):
                cell: dict[str, Any] = {
                    "column": column,
                    "html": None,
                    "checkbox": column.is_checkbox,
                    "checked": False,
                    "filled": False,
                }
                if row.has(column.key):
                    cell_value = value.get(row.key, {}).get(column.key)
                    cell_attrs: dict[str, Any] = {
                        "id": f"{base_id}_{i}_{j}",
                        "aria-label": f"{row.label}: {column.label}",
                    }
                    if disabled:
                        cell_attrs["disabled"] = True
                    cell["html"] = column.field.widget.render(
                        self.cell_name(name, row, column),
                        column.field.prepare_value(cell_value),
                        cell_attrs,
                    )
                    cell["filled"] = bool(cell_value)
                    cell["checked"] = column.is_checkbox and cell["filled"]
                cells.append(cell)
            sections.setdefault(row.section, Section(row.section)).rows.append(
                {
                    "label": row.label,
                    "cells": cells,
                    "has_checkboxes": any(c["checkbox"] and c["html"] for c in cells),
                }
            )
        widget.update(
            sections=list(sections.values()),
            columns=self.columns,
            disabled=disabled,
        )
        return context
