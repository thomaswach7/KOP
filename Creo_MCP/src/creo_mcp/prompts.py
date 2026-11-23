"""MCP-Prompts: wiederverwendbare Arbeitsabläufe."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer


def register(server: MCPServer) -> None:
    @server.prompt(name="pdf_zu_creo_modell", title="PDF-Zeichnung → Creo-Modell + Zeichnung")
    def pdf_zu_creo_modell(pdf: str, teilname: str) -> str:
        """Ablauf: Bauteil aus einer PDF-Zeichnung in Creo aufbauen und danach eine Zeichnung erstellen."""
        return f"""Baue das Bauteil aus der Zeichnung "{pdf}" in Creo Parametric als "{teilname}" auf.

1. Lies die PDF vollständig: Ansichten, alle Maße mit Toleranzen, Werkstoff, Maßstab, Schriftfeld, Stückliste.
   Schreibe eine KE-Liste (Reihenfolge, Skizzierebene, Maße) und berechne das Sollvolumen, bevor du in Creo etwas änderst.
2. creo_status → läuft CREOSON/Creo? Sonst creo_connect(start_creo=true) oder creo_doctor.
3. creo_new_model(name="{teilname}") legt das Teil aus der mmns-Vorlage an (RIGHT/TOP/FRONT/PRT_CSYS_DEF).
4. KEs erzeugen: Die kostenlose Creo-API kann keine Skizzen-KEs direkt anlegen. Wege:
   a) Mapkeys (creo_run_mapkey) mit in Creo aufgezeichneten Befehlsfolgen – danach immer creo_get_model_tree prüfen;
   b) Ausweichweg: Geometrie als STEP erzeugen und mit creo_import_geometry importieren (kein KE-Verlauf).
   Benenne jedes KE sinnvoll (creo_rename_feature), z. B. "Grundkörper", "Passfedernut".
5. Maße feinjustieren: creo_list_dimensions → creo_set_dimension. Parameter: creo_set_parameter (BENENNUNG, WERKSTOFF, POSITION),
   Material: creo_set_material.
6. Prüfen: creo_mass_properties (Volumen gegen Sollvolumen, Abweichung < 0,5 %), creo_get_model_tree (KE-Reihenfolge/Namen).
7. Zeichnung: creo_create_drawing (Vorlage/Format der Schule, Maßstab wie in der PDF), creo_add_drawing_view
   (Vorderansicht + Projektionen), creo_edit_drawing, dann creo_export(format="PDF") und creo_save_model.
8. Fasse am Ende zusammen: was automatisch ging, was der Nutzer in Creo noch von Hand machen muss.
"""

    @server.prompt(name="modellbaum_pruefen", title="Modellbaum gegen Anleitung prüfen")
    def modellbaum_pruefen(datei: str, anleitung: str = "") -> str:
        """Ablauf: Modellbaum eines Modells lesen und mit einer Anleitung/Vorgabe vergleichen."""
        extra = f'\nVergleichsgrundlage (Anleitung/Vorgabe):\n"""\n{anleitung}\n"""\n' if anleitung else ""
        return f"""Prüfe das Creo-Modell "{datei}".

1. creo_get_model_tree(file="{datei}") – Reihenfolge, Namen, Typen, Status (⊘ = unterdrückt).
2. creo_mass_properties – Volumen; creo_list_parameters – BENENNUNG/WERKSTOFF; creo_list_dimensions – Hauptmaße.
3. Vergleiche mit der Vorgabe und liste Abweichungen als Tabelle: Soll | Ist | Bewertung | Korrekturvorschlag.
4. Schlage konkrete Korrekturen vor (z. B. creo_rename_feature, creo_set_dimension) – ändere nichts ohne Rückfrage.
{extra}"""
