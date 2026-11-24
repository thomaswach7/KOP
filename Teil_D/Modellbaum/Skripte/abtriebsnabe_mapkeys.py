"""Abtriebsnabe (Pos. 2) über aufgezeichnete Mapkeys in Creo 12 bauen – mit Volumenprüfung nach jedem KE.

Ablauf (Aufnahme der Mapkeys: Teil_D/Modellbaum/Mapkeys_Abtriebsnabe.md):
1. creo_new_model: neues Teil aus der HTL-Vorlage standard_part (RECHTS/OBEN/VORNE, A_X, BASIS, mm)
2. Mapkeys ke1 … ke8 aus der config.pro nacheinander über creo_run_mapkey abspielen
3. nach jedem KE: Ist ein neues KE im Modellbaum? Stimmt das Volumen mit der Tabelle der Anleitung?

Alles läuft über die Werkzeuge des Creo-MCP (wie bei Claude Desktop). Voraussetzung: CREOSON und Creo laufen
(C:\\Creoson_<Benutzer>\\creoson_run.bat und nitro_proe_remote.bat), `python -m creo_mcp doctor` ist grün.

Aufruf mit dem Python des Creo-MCP:
    Creo_MCP\\.venv\\Scripts\\python.exe Teil_D\\Modellbaum\\Skripte\\abtriebsnabe_mapkeys.py
Optionen:
    --config PFAD   config.pro mit den Mapkeys (Standard: Dokumente\\Creo\\config.pro)
    --name DATEI    neues Teil (Standard: pos02_abtriebsnabe.prt)
    --ab N          ab KE N weitermachen; das Teil ist schon offen und hat KE 1 … N-1
    --toleranz P    erlaubte Abweichung des Volumens in Prozent (Standard 0,1)
    --warten S      so lange auf das neue KE warten (Standard 120 s)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

from mcp import Client

from creo_mcp.client import CreosonClient
from creo_mcp.config import Settings
from creo_mcp.mapkeys import parse_config_mapkeys
from creo_mcp.server import build_server

HTL_VORLAGEN = r"C:\PTC\admCreo12HTL\bibliothek\Vorlagen"
# (KE, Mapkey, Inhalt, Volumen danach in mm³) – aus Anleitung_Abtriebsnabe.md
SCHRITTE = [
    (1, "ke1", "Drehen – Grundkörper mit Freistichen", 356_379),
    (2, "ke2", "Rundung R10 Nabe/Flansch", 360_051),
    (3, "ke3", "Rundung 2 × R5 bei 55", 363_355),
    (4, "ke4", "Rundung 2 × R2", 362_766),
    (5, "ke5", "Kantenfase 1,5 × 45°", 362_289),
    (6, "ke6", "Profil – Passfedernut", 360_786),
    (7, "ke7", "Bohrung Ø9 mit Stirnsenkung", 359_050),
    (8, "ke8", "Muster 6 × 60° um A_X", 350_370),
]


class Abbruch(Exception):
    pass


async def werkzeug(client: Client, name: str, args: dict) -> str:
    res = await client.call_tool(name, args)
    text = "\n".join(getattr(c, "text", "") for c in res.content)
    if res.is_error:
        raise Abbruch(f"{name}: {text}")
    return text


async def ke_liste(client: Client, datei: str) -> list[dict]:
    text = await werkzeug(client, "creo_list_features", {"file": datei, "limit": 1000, "response_format": "json"})
    return json.loads(text)["items"]


async def volumen(client: Client, datei: str) -> float:
    text = await werkzeug(client, "creo_mass_properties", {"file": datei, "response_format": "json"})
    return float(json.loads(text).get("volume") or 0.0)


async def bauen(args: argparse.Namespace) -> int:
    mapkeys = parse_config_mapkeys(Path(args.config).read_text(encoding="utf-8", errors="replace"))
    schritte = [s for s in SCHRITTE if s[0] >= args.ab]
    fehlend = [s[1] for s in schritte if s[1] not in mapkeys]
    if fehlend:
        print(f"In {args.config} fehlen die Mapkeys: {', '.join(fehlend)}. Gefunden: {', '.join(sorted(mapkeys)) or 'keine'}.")
        return 2

    os.environ.setdefault("CREO_VERSION", "12")
    settings = Settings.from_env()
    async with Client(build_server(settings, CreosonClient(settings))) as client:
        try:
            return await ablauf(client, args, mapkeys, schritte)
        except Abbruch as exc:  # hier fangen – außerhalb des Clients käme er als ExceptionGroup an
            print(f"Abbruch: {exc}")
            return 1


async def ablauf(client: Client, args: argparse.Namespace, mapkeys: dict[str, str], schritte: list) -> int:
    if args.ab == 1:
        print(await werkzeug(client, "creo_new_model", {"name": args.name, "model_type": "part", "template": "standard_part", "template_dir": HTL_VORLAGEN}))
    else:
        print(await werkzeug(client, "creo_open_model", {"file": args.name, "display": True, "activate": True}))

    ergebnis = []
    for nr, taste, inhalt, soll in schritte:
        vorher = len(await ke_liste(client, args.name))
        await werkzeug(client, "creo_run_mapkey", {"script": mapkeys[taste]})
        ende = time.monotonic() + args.warten
        while True:
            kes = await ke_liste(client, args.name)
            if len(kes) > vorher:
                break
            if time.monotonic() > ende:
                raise Abbruch(f"KE {nr} ({taste}): nach {args.warten:g} s kein neues KE im Modellbaum. Ist in Creo ein Dialog offen?")
            await asyncio.sleep(1.0)
        await asyncio.sleep(1.0)  # Creo regeneriert noch
        ist = await volumen(client, args.name)
        abweichung = (ist - soll) / soll * 100
        ok = abs(abweichung) <= args.toleranz
        neu = ", ".join(str(k.get("type")) for k in kes[vorher:])
        ergebnis.append((nr, inhalt, neu, soll, ist, abweichung, ok))
        print(f"KE {nr} {inhalt}: neu {neu} – Volumen {ist:,.0f} mm³ (Soll {soll:,} mm³, {abweichung:+.3f} %) {'✅' if ok else '❌'}".replace(",", "."))
        if not ok:
            print(f"Abbruch nach KE {nr}: Volumen weicht mehr als {args.toleranz} % ab. Mapkey {taste} prüfen, dann mit --ab {nr} weiter.")
            return 1
    print(f"\nFertig: {args.name} mit {len(ergebnis)} KEs, Endvolumen {ergebnis[-1][4]:,.0f} mm³.".replace(",", "."))
    print("Nicht gespeichert – in Creo prüfen und mit Strg+S speichern (oder creo_save_model).")
    return 0


def main() -> int:
    logging.basicConfig(level=logging.WARNING)
    for name in ("httpx", "mcp"):  # keine Protokollzeilen pro Anfrage
        logging.getLogger(name).setLevel(logging.ERROR)
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--config", default=str(Path.home() / "Documents" / "Creo" / "config.pro"))
    p.add_argument("--name", default="pos02_abtriebsnabe.prt")
    p.add_argument("--ab", type=int, default=1, choices=range(1, 9))
    p.add_argument("--toleranz", type=float, default=0.1)
    p.add_argument("--warten", type=float, default=120.0)
    args = p.parse_args()
    return asyncio.run(bauen(args))


if __name__ == "__main__":
    sys.exit(main())
