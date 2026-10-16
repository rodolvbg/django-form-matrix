import ast
import gettext
import re
from pathlib import Path
from typing import Any

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import translation

from django_form_matrix.contrib.permissions import (
    PermissionMultipleChoiceField,
    permission_label,
)

LOCALE_DIR = Path(__file__).parent.parent / "src/django_form_matrix/locale"
CATALOGS = sorted(LOCALE_DIR.glob("*/LC_MESSAGES/django.po"))


def po_entries(path):
    """``(msgid, [msgstr...], fuzzy)`` for every message of a .po file."""
    for block in path.read_text(encoding="utf-8").split("\n\n"):
        msgid = re.search(r'^msgid "(.*)"', block, re.M)
        if not msgid or 'msgid ""\nmsgstr ""\n"' in block:
            continue
        yield (
            msgid.group(1),
            re.findall(r'^msgstr(?:\[\d+\])? "(.*)"$', block, re.M),
            "#, fuzzy" in block,
        )


PO_LINE = re.compile(r'^(msgctxt|msgid_plural|msgid|msgstr(?:\[\d+\])?) (".*")$')


def po_messages(path):
    """``{msgid: msgstr}`` (``{(msgid, n): msgstr}`` for plurals) of a .po file."""
    messages: dict[Any, str] = {}
    for block in path.read_text(encoding="utf-8").split("\n\n"):
        fields: dict[str, str] = {}
        key = None
        for line in block.splitlines():
            match = PO_LINE.match(line)
            if match:
                key = match.group(1)
                fields[key] = ast.literal_eval(match.group(2))
            elif line.startswith('"') and key:
                fields[key] += ast.literal_eval(line)
        msgid = fields.get("msgid")
        if not msgid or "#, fuzzy" in block:
            continue
        if "msgctxt" in fields:
            msgid = f"{fields['msgctxt']}\x04{msgid}"
        if "msgid_plural" in fields:
            for name, value in fields.items():
                if name.startswith("msgstr["):
                    messages[(msgid, int(name[7:-1]))] = value
        else:
            messages[msgid] = fields["msgstr"]
    return messages


def mo_messages(path):
    """The same, from the compiled .mo (as Django will load it)."""
    with path.open("rb") as file:
        catalog = getattr(gettext.GNUTranslations(file), "_catalog")  # noqa: B009
    return {key: value for key, value in catalog.items() if key != ""}


def test_there_is_a_spanish_catalog():
    assert [c.parent.parent.name for c in CATALOGS] == ["es"]


@pytest.mark.parametrize("catalog", CATALOGS, ids=lambda c: c.parent.parent.name)
def test_every_message_is_translated(catalog):
    problems = [
        msgid
        for msgid, msgstrs, fuzzy in po_entries(catalog)
        if fuzzy or not all(s.strip() for s in msgstrs)
    ]
    assert problems == []


@pytest.mark.parametrize("catalog", CATALOGS, ids=lambda c: c.parent.parent.name)
def test_compiled_catalog_is_up_to_date(catalog):
    """The shipped .mo has exactly the .po's translations (not compared by
    date: a git checkout gives both files arbitrary modification times)."""
    compiled = catalog.with_suffix(".mo")

    assert compiled.exists()
    assert mo_messages(compiled) == po_messages(catalog)


@pytest.mark.django_db
def test_permission_names_in_spanish():
    view = Permission.objects.get(content_type__app_label="demo", codename="view_plan")
    with translation.override("es"):
        assert permission_label(view) == "Demo | Plan | Puede ver plan"


@pytest.mark.django_db
def test_the_matrix_in_spanish():
    ct = ContentType.objects.get(app_label="demo", model="plan")
    Permission.objects.create(content_type=ct, codename="export_plan", name="Export")
    field = PermissionMultipleChoiceField(
        queryset=Permission.objects.filter(content_type=ct)
    )
    with translation.override("es"):
        html = field.widget.render("p", [])

    for heading in ("Añadir", "Ver", "Modificar", "Eliminar", "Otros"):
        assert heading in html
    # The admin's own word for "All" (its catalog comes first).
    assert "> Todo</label>" in html


@pytest.mark.django_db
def test_nothing_to_choose_in_spanish():
    field = PermissionMultipleChoiceField(queryset=Permission.objects.none())
    with translation.override("es"):
        assert "No hay permisos disponibles." in field.widget.render("p", [])
