"""
Tigo MCP Server - Model Context Protocol server for Tigo Energy solar systems.

A comprehensive MCP server that provides AI assistants with access to Tigo Energy
solar system data and analytics, including production monitoring, performance
analysis, system health checks, and maintenance insights.

Features:
- Real-time solar production data
- Performance analysis and efficiency metrics  
- System health monitoring and alerts
- Maintenance recommendations
- Historical data analysis
- Multi-system support

Example:
    >>> from tigo_mcp_server import main
    >>> main()  # Starts the MCP server
"""

__version__ = "0.1.6"
__author__ = "Matt Dreyer"
__email__ = "matt_dreyer@hotmail.com"
__description__ = "Model Context Protocol server for Tigo Energy solar system monitoring and analytics"
__url__ = "https://github.com/matt-dreyer/Tigo_MCP_server"

# Import main components with proper error handling
try:
    # Try relative import first (when installed as package)
    from .server import main, server
except ImportError:
    try:
        # Fallback to absolute import (for development/direct execution)
        from server import main, server
    except ImportError:
        # If neither works, define placeholder functions
        import logging
        logging.warning("Could not import server module. Server functionality may not be available.")
        
        def main():
            """Placeholder main function."""
            raise ImportError("Server module not available. Please check installation.")
        
        server = None

# For backward compatibility, also expose 'app' if someone expects it
app = server

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "__description__",
    "__url__",
    "main",
    "server",
    "app",  # For backward compatibility
]