import sys

from mcp import Client, StdioServerParameters


async def test_demo_server_over_stdio_returns_model_tree():
    params = StdioServerParameters(command=sys.executable, args=["-m", "creo_mcp", "demo"])
    async with Client(params) as client:
        names = {t.name for t in (await client.list_tools()).tools}
        assert "creo_get_model_tree" in names
        await client.call_tool("creo_open_model", {"file": "fliehkraftkupplung.asm"})
        res = await client.call_tool("creo_get_model_tree", {"include_datums": False})
        text = "\n".join(c.text for c in res.content)
        assert not res.is_error
        assert "abtriebsnabe.prt" in text and "Muster_Bohrungen" in text


async def test_cli_help_runs():
    import subprocess

    out = subprocess.run([sys.executable, "-m", "creo_mcp", "--help"], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0
    assert "demo" in out.stdout and "doctor" in out.stdout
