"""Thin launcher for the tkw-dnd (The Known World) desktop extension.

The real MCP server and the melded engine live in place at the path below --
we do NOT duplicate them into the extension bundle. This stub just runs that
in-place server with the Python the extension was told to use, so edits to the
live folder always take effect. The 1e rules corpus (adnd_1e.db) is shared
read-only with the Greyhawk install via the GREYHAWK_CORPUS env var.
"""
import runpy

runpy.run_path(
    r"C:\Users\Raymond\Documents\dndCampaign\dndTKW\server\mcp_server.py",
    run_name="__main__",
)
