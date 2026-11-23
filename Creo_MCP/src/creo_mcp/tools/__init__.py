"""MCP-Werkzeuge, nach Themen getrennt. Jedes Modul hat `register(server, ctx)`."""

from . import advanced, data, drawing, features, generic, io, models, session, tree_tools

MODULES = (session, models, tree_tools, features, data, drawing, io, generic, advanced)

__all__ = ["MODULES"]
