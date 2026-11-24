from creo_mcp.mapkeys import parse_config_mapkeys

# Aufbau wie in einer von Creo 12 gespeicherten config.pro (vgl. mapkeys_deutsch.pro des HTL-Pakets)
CONFIG = r"""
! Kommentar
pro_unit_length unit_mm
mapkey ke1 @MAPKEY_NAMEKE1 Drehen;@MAPKEY_LABELKE1;\
mapkey(continued) ~ Command `ProCmdDashBoardRevolve` ;\
mapkey(continued) ~ Select `main_dlg_cur` `PHTLeft.AssyTree` 1 `node3`;
mapkey $F3 @MAPKEY_LABELRedraw;~ Command `ProCmdViewRepaint`;
template_solidpart standard_part.prt
mapkey ke2 ~ Command `ProCmdRound` ;
mapkey ke2 ~ Command `ProCmdChamfer` ;
"""


def test_parse_config_mapkeys_joins_continued_lines_and_drops_labels():
    keys = parse_config_mapkeys(CONFIG)
    assert set(keys) == {"ke1", "$F3", "ke2"}
    assert keys["ke1"] == "~ Command `ProCmdDashBoardRevolve` ;~ Select `main_dlg_cur` `PHTLeft.AssyTree` 1 `node3`;"
    assert keys["$F3"] == "~ Command `ProCmdViewRepaint`;"


def test_parse_config_mapkeys_last_definition_wins_and_other_options_end_a_block():
    keys = parse_config_mapkeys(CONFIG)
    assert keys["ke2"] == "~ Command `ProCmdChamfer` ;"
    assert "template_solidpart" not in "".join(keys.values())
