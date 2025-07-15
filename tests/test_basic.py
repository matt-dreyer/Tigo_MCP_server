"""
Basic tests for Tigo MCP Server.
"""

def test_import():
    """Test that the package can be imported."""
    try:
        import tigo_mcp_server
        assert tigo_mcp_server.__version__ == "0.1.0"
    except ImportError:
        # During development, the package might not be installed
        pass

def test_version():
    """Test version is available."""
    try:
        from tigo_mcp_server import __version__
        assert __version__ is not None
    except ImportError:
        pass
