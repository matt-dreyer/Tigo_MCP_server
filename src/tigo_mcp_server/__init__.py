"""
Tigo MCP Server - Model Context Protocol server for Tigo solar panel monitoring and control.

"""

__version__ = "0.1.0"
__author__ = "Matt Dreyer"
__email__ = "matt_dreyer@hotmail.com"  # Replace with your actual email
__license__ = "MIT"
__description__ = "Model Context Protocol server for Tigo Energy solar panel monitoring"
__url__ = "https://github.com/matt-dreyer/Tigo_MCP_server"

# Package metadata
__all__ = [
    "FastMCP",
    "get_api_instance", 
    "format_power_value",
    "format_energy_value",
    "generate_recommendations"
]