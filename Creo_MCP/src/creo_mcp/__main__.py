"""Kommandozeile: `creo-mcp [serve|demo|mock|doctor]` bzw. `python -m creo_mcp ...`."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import time

from . import __version__
from .config import Settings


def _logging() -> None:
    level = os.environ.get("CREO_MCP_LOG_LEVEL", "WARNING").upper()
    logging.basicConfig(stream=sys.stderr, level=level, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def _serve(settings: Settings, transport: str, host: str, port: int) -> None:
    from .server import build_server

    server = build_server(settings)
    if transport == "stdio":
        server.run()
    else:
        server.run("streamable-http", host=host, port=port)


def _cmd_serve(args: argparse.Namespace) -> None:
    _serve(Settings.from_env(), args.transport, args.host, args.port)


def _cmd_demo(args: argparse.Namespace) -> None:
    from dataclasses import replace

    from .mock.server import start_mock_server
    from .mock.state import TEMPLATE_DIR

    handle = start_mock_server()
    print(f"[creo-mcp] Demo-Modus: simuliertes Creo/CREOSON unter {handle.url}", file=sys.stderr)
    settings = replace(Settings.from_env(), creoson_url=handle.url, template_dir=TEMPLATE_DIR)
    try:
        _serve(settings, args.transport, args.host, args.port)
    finally:
        handle.stop()


def _cmd_mock(args: argparse.Namespace) -> None:
    from .mock.server import start_mock_server

    handle = start_mock_server(host=args.host, port=args.port)
    print(f"Simulierter CREOSON-Server läuft: {handle.url} (Strg+C beendet)", file=sys.stderr)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        handle.stop()


def _cmd_doctor(args: argparse.Namespace) -> None:
    from .client import CreosonClient
    from .doctor import render_checks, run_diagnostics

    async def run() -> str:
        settings = Settings.from_env()
        client = CreosonClient(settings)
        try:
            return render_checks(await run_diagnostics(settings, client))
        finally:
            await client.aclose()

    print(asyncio.run(run()))


_SUBCOMMANDS = {"serve", "demo", "mock", "doctor"}


def normalize_argv(argv: list[str]) -> list[str]:
    """Ohne Unterbefehl gilt `serve` (auch wenn nur Optionen wie --transport angegeben sind)."""
    if not argv:
        return ["serve"]
    if argv[0] in _SUBCOMMANDS or argv[0] in ("-h", "--help"):
        return list(argv)
    return ["serve", *argv]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="creo-mcp", description=f"MCP-Server für PTC Creo Parametric (v{__version__})")
    sub = parser.add_subparsers(dest="command")

    def transport_opts(p: argparse.ArgumentParser) -> None:
        p.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio", help="MCP transport (default stdio)")
        p.add_argument("--host", default="127.0.0.1", help="Host for streamable-http")
        p.add_argument("--port", type=int, default=8765, help="Port for streamable-http")

    serve = sub.add_parser("serve", help="MCP-Server starten (Standard), verbindet sich mit CREOSON")
    transport_opts(serve)
    serve.set_defaults(func=_cmd_serve)
    demo = sub.add_parser("demo", help="MCP-Server mit simuliertem Creo starten (ohne Creo testen)")
    transport_opts(demo)
    demo.set_defaults(func=_cmd_demo)
    mock = sub.add_parser("mock", help="Nur den simulierten CREOSON-Server starten")
    mock.add_argument("--host", default="127.0.0.1")
    mock.add_argument("--port", type=int, default=9056)
    mock.set_defaults(func=_cmd_mock)
    doctor = sub.add_parser("doctor", help="Verbindungswege zu Creo prüfen und Lösungen anzeigen")
    doctor.set_defaults(func=_cmd_doctor)
    return parser


def main(argv: list[str] | None = None) -> None:
    _logging()
    parser = build_parser()
    args = parser.parse_args(normalize_argv(sys.argv[1:] if argv is None else argv))
    args.func(args)


if __name__ == "__main__":
    main()
