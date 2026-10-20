import re

import pytest
from django.contrib.auth.models import Permission

from django_form_matrix import Column, MatrixField, MatrixWidget, Row
from django_form_matrix.contrib.permissions import (
    PermissionMatrixWidget,
    PermissionMultipleChoiceField,
)


class CustomMatrixWidget(MatrixWidget):
    template_name = "demo/custom_matrix.html"


class CustomPermissionWidget(PermissionMatrixWidget):
    template_name = "demo/custom_permissions.html"


def matrix(rows):
    field = MatrixField(rows=rows, columns=[Column("on", "On")])
    field.widget = CustomMatrixWidget(rows=field.rows, columns=field.columns)
    return field.widget


class TestMatrixWidgetBlocks:
    """Overriding blocks of the matrix template."""

    def test_a_template_can_change_one_block_and_keep_the_rest(self):
        html = matrix([Row("a", "Alpha", section="S")]).render("m", {"a": {"on": True}})
        assert '<strong class="demo-title">S</strong>' in html
        assert '<span class="demo-cell"><input' in html
        # what it did not change is the library's
        assert 'data-form-matrix-toggle="row"' in html
        assert 'class="form-matrix-section"' in html
        assert 'class="form-matrix-section-name"' not in html

    def test_the_empty_block(self):
        assert 'class="demo-empty"' in matrix([]).render("m", {})


class TestPermissionWidgetBlocks:
    """Overriding blocks of the permissions template."""

    @pytest.mark.django_db
    def test_the_permission_template_has_blocks_too(self):
        field = PermissionMultipleChoiceField(
            queryset=Permission.objects.filter(codename="view_plan")
        )
        widget = CustomPermissionWidget()
        widget.choices = field.widget.choices
        html = widget.render("p", [])
        assert '<strong class="demo-title">Demo</strong>' in html
        assert 'data-form-matrix-toggle="row"' in html

        nothing = CustomPermissionWidget()
        nothing.choices = PermissionMultipleChoiceField(
            queryset=Permission.objects.none()
        ).widget.choices
        assert 'class="demo-empty"' in nothing.render("p", [])

    @pytest.mark.django_db
    def test_block_super_keeps_the_original_of_the_block(self):
        from django.contrib.contenttypes.models import ContentType

        plan = ContentType.objects.get(app_label="demo", model="plan")
        Permission.objects.create(
            content_type=plan, codename="export_plan", name="Can export plans"
        )
        field = PermissionMultipleChoiceField(
            queryset=Permission.objects.filter(content_type=plan)
        )
        widget = CustomPermissionWidget()
        widget.choices = field.widget.choices
        html = widget.render("p", [])
        assert re.search(r'<span class="demo-other">\s*<label><input', html)
        assert "Can export plans" in html
