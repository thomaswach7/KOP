"""KE-Typnamen von Creo vereinheitlichen (deutsche Oberfläche → englische Namen).

CREOSON liefert den KE-Typ so, wie Creo ihn in der Sprache der Oberfläche anzeigt (J-Link getFeatTypeName).
Ein deutsches Creo 12 meldet z. B. "BEZUGSEBENE", "MUSTER" oder "KOMPONENTE" statt "DATUM PLANE", "PATTERN",
"COMPONENT". Die Logik des Servers (Bezüge ausblenden, Muster/Gruppen erkennen, Komponenten aufklappen,
Typfilter) arbeitet deshalb mit dem englischen Namen; angezeigt wird weiter der Name aus Creo.

Quellen der Zuordnung: Meldungsdateien von Creo 12.4.5.0 (Common Files\\text\\german\\msgtxt*.txt, je Eintrag
englischer und deutscher Text) und echte Antworten von Creo 12.4.5.0 (deutsch) über CREOSON 3.0.2.
"""

from __future__ import annotations

from typing import Literal

_GERMAN = {
    "KOORDINATENSYSTEM": "COORDINATE SYSTEM",
    "BEZUGSEBENE": "DATUM PLANE",
    "BEZUGSACHSE": "DATUM AXIS",
    "BEZUGSPUNKT": "DATUM POINT",
    "KURVE": "CURVE",  # auch Skizzen-KEs ("Skizze 1") meldet Creo so
    "SKIZZE": "SKETCH",
    "KÖRPER": "PROTRUSION",  # Drehen/Extrudieren mit Material hinzufügen
    "MATERIALSCHNITT": "CUT",
    "BOHRUNG": "HOLE",
    "RUNDUNG": "ROUND",
    "FASE": "CHAMFER",
    "MUSTER": "PATTERN",
    "SPIEGELN": "MIRROR",
    "KOMPONENTE": "COMPONENT",
    "GRUPPENKOPF": "GROUP HEAD",
    "GRUPPE": "GROUP",
}
# Kopf-KEs heißen je nach Quelle mit oder ohne "HEAD"
_ALIASES = {"PATTERN HEAD": "PATTERN", "GROUP HEAD": "GROUP", "LOCAL GROUP": "GROUP"}

DATUM_TYPES = frozenset(
    {
        "COORDINATE SYSTEM",
        "CURVE",
        "SKETCH",
        "DATUM AXIS",
        "DATUM PLANE",
        "DATUM POINT",
        "DATUM QUILT",
        "DATUM SURFACE",
    }
)


def canonical_type(type_name: object) -> str:
    """Englischer Typname in Großbuchstaben, z. B. 'Bezugsebene' → 'DATUM PLANE', 'PATTERN HEAD' → 'PATTERN'."""
    text = " ".join(str(type_name or "").upper().replace("_", " ").split())
    text = _GERMAN.get(text, text)
    return _ALIASES.get(text, text)


def is_datum(type_name: object) -> bool:
    return canonical_type(type_name) in DATUM_TYPES


def is_component(type_name: object) -> bool:
    return canonical_type(type_name) == "COMPONENT"


def head_kind(type_name: object) -> Literal["pattern", "group"] | None:
    """'pattern' oder 'group', wenn das KE der Kopf eines Musters bzw. einer Gruppe ist."""
    t = canonical_type(type_name)
    if t == "PATTERN" or t.endswith(" PATTERN"):
        return "pattern"
    if t == "GROUP":
        return "group"
    return None


def same_type(a: object, b: object) -> bool:
    """Typvergleich unabhängig von Sprache und Schreibweise ('HOLE' == 'Bohrung')."""
    return canonical_type(a) == canonical_type(b)
