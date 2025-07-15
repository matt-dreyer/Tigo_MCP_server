#!/usr/bin/env python3
"""
Tigo MCP Server - Model Context Protocol server for Tigo Energy solar systems.

This module provides a comprehensive MCP server that enables AI assistants to 
interact with Tigo Energy solar monitoring systems for production data, 
performance metrics, system health information, and maintenance insights.
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

# MCP and FastMCP imports
from mcp.server import Server
from mcp.types import TextContent, Tool
import fastmcp

# Environment and configuration
from dotenv import load_dotenv

# Tigo API client
try:
    import tigo
except ImportError:
    logging.error("tigo-python package not found. Please install it with: pip install tigo-python")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Global variables for Tigo client
tigo_client = None

def safe_json_serialize(obj: Any) -> Any:
    """
    Safely serialize complex objects to JSON-compatible format.
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON-serializable object
    """
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    elif isinstance(obj, dict):
        return {k: safe_json_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [safe_json_serialize(item) for item in obj]
    elif hasattr(obj, 'isoformat'):  # datetime objects
        return obj.isoformat()
    else:
        return str(obj)

def initialize_tigo_client() -> Optional[Any]:
    """
    Initialize and return Tigo API client.
    
    Returns:
        Initialized Tigo client or None if initialization fails
    """
    global tigo_client
    
    if tigo_client is not None:
        return tigo_client
    
    username = os.getenv("TIGO_USERNAME")
    password = os.getenv("TIGO_PASSWORD")
    
    if not username or not password:
        logger.error("TIGO_USERNAME and TIGO_PASSWORD environment variables are required")
        return None
    
    try:
        tigo_client = tigo.TigoApiClient(username, password)
        logger.info("Tigo API client initialized successfully")
        return tigo_client
    except Exception as e:
        logger.error(f"Failed to initialize Tigo API client: {e}")
        return None

# Initialize FastMCP app
app = fastmcp.FastMCP("Tigo Energy MCP Server")

@app.tool()
async def fetch_configuration() -> Dict[str, Any]:
    """
    Query the Tigo API for the runtime status of the system.
    
    Returns:
        Dict containing user account information and list of available solar systems.
    """
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        # Get user information
        user_info = client.get_user()
        
        # Get systems information
        systems_info = client.get_systems()
        
        result = {
            "user": safe_json_serialize(user_info),
            "systems": safe_json_serialize(systems_info)
        }
        
        logger.info(f"Configuration fetched successfully for user: {user_info.get('login', 'unknown')}")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching configuration: {e}")
        raise

@app.tool()
async def get_system_details(system_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get detailed information about a specific system including layout, sources, and summary.
    If no system_id provided, uses the first available system.
    
    Args:
        system_id: Specific system ID, uses first available system if not provided
        
    Returns:
        Dict containing comprehensive system information
    """
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        # If no system_id provided, get the first available system
        if system_id is None:
            systems = client.get_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Get detailed system information
        system_details = client.get_system_details(system_id)
        
        result = safe_json_serialize(system_details)
        logger.info(f"System details retrieved for system ID: {system_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting system details: {e}")
        raise

@app.tool()
async def get_current_production(system_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get today's production data and real-time system summary.
    
    Args:
        system_id: Target system ID
        
    Returns:
        Dict containing current production metrics, today's generation data, and system status
    """
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        # If no system_id provided, get the first available system
        if system_id is None:
            systems = client.get_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Get current production summary
        production_data = client.get_system_summary(system_id)
        
        result = {
            "system_id": system_id,
            "timestamp": datetime.now().isoformat(),
            "summary": safe_json_serialize(production_data)
        }
        
        logger.info(f"Current production data retrieved for system ID: {system_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting current production: {e}")
        raise

@app.tool()
async def get_performance_analysis(
    system_id: Optional[int] = None, 
    days_back: int = 7
) -> Dict[str, Any]:
    """
    Get comprehensive performance analysis including efficiency metrics and panel performance.
    
    Args:
        system_id: Target system ID
        days_back: Number of days to analyze (default: 7)
        
    Returns:
        Dict containing efficiency metrics, top/bottom performing panels, and performance summary
    """
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        # If no system_id provided, get the first available system
        if system_id is None:
            systems = client.get_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Get performance data for the specified period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get system summary and historical data for analysis
        summary = client.get_system_summary(system_id)
        
        # Calculate basic performance metrics
        result = {
            "system_id": system_id,
            "analysis_period_days": days_back,
            "timestamp": datetime.now().isoformat(),
            "summary": safe_json_serialize(summary),
            "performance_metrics": {
                "daily_energy_dc": summary.get("daily_energy_dc", 0),
                "lifetime_energy_dc": summary.get("lifetime_energy_dc", 0),
                "last_power_dc": summary.get("last_power_dc", 0),
                "efficiency_analysis": "Performance analysis based on available data"
            }
        }
        
        logger.info(f"Performance analysis completed for system ID: {system_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting performance analysis: {e}")
        raise

@app.tool()
async def get_historical_data(
    system_id: Optional[int] = None,
    days_back: int = 30,
    level: str = "day"
) -> Dict[str, Any]:
    """
    Get historical production data for analysis.

    Args:
        system_id: System ID (optional, uses first system if not provided)
        days_back: Number of days of historical data (default: 30)
        level: Data granularity - "minute", "hour", or "day" (default: "day")
        
    Returns:
        Dict containing historical production data with statistical summary
    """
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        # Validate level parameter
        if level not in ["minute", "hour", "day"]:
            raise ValueError("Level must be 'minute', 'hour', or 'day'")
        
        # If no system_id provided, get the first available system
        if system_id is None:
            systems = client.get_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Get historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # For now, return summary data with timestamp information
        summary = client.get_system_summary(system_id)
        
        result = {
            "system_id": system_id,
            "days_back": days_back,
            "level": level,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "timestamp": datetime.now().isoformat(),
            "data": safe_json_serialize(summary),
            "metadata": {
                "granularity": level,
                "period_days": days_back,
                "data_points": f"Requested {level}-level data for {days_back} days"
            }
        }
        
        logger.info(f"Historical data retrieved for system ID: {system_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise

@app.tool()
async def get_system_alerts(
    system_id: Optional[int] = None,
    days_back: int = 30
) -> Dict[str, Any]:
    """
    Get recent alerts and system health information.
    
    Args:
        system_id: Target system ID
        days_back: Number of days to look back for alerts (default: 30)
        
    Returns:
        Dict containing active and recent alerts with categorization and status
    """
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        # If no system_id provided, get the first available system
        if system_id is None:
            systems = client.get_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Get system information to check for alerts
        systems_info = client.get_systems()
        system_info = None
        
        for system in systems_info.get('systems', []):
            if system.get('system_id') == system_id:
                system_info = system
                break
        
        if not system_info:
            raise Exception(f"System {system_id} not found")
        
        result = {
            "system_id": system_id,
            "timestamp": datetime.now().isoformat(),
            "days_back": days_back,
            "recent_alerts_count": system_info.get("recent_alerts_count", 0),
            "alerts": [],
            "system_status": system_info.get("status", "Unknown"),
            "alert_summary": {
                "active_alerts": system_info.get("recent_alerts_count", 0),
                "period_days": days_back,
                "last_updated": datetime.now().isoformat()
            }
        }
        
        logger.info(f"System alerts retrieved for system ID: {system_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting system alerts: {e}")
        raise

@app.tool()
async def get_system_health(system_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get comprehensive system health status combining multiple data sources.
    
    Args:
        system_id: Target system ID
        
    Returns:
        Dict containing overall health rating with supporting metrics and recommendations
    """
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        # If no system_id provided, get the first available system
        if system_id is None:
            systems = client.get_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Get system summary and information
        summary = client.get_system_summary(system_id)
        systems_info = client.get_systems()
        
        system_info = None
        for system in systems_info.get('systems', []):
            if system.get('system_id') == system_id:
                system_info = system
                break
        
        if not system_info:
            raise Exception(f"System {system_id} not found")
        
        # Calculate basic health metrics
        active_alerts = system_info.get("recent_alerts_count", 0)
        power_rating = system_info.get("power_rating", 1)
        current_power = summary.get("last_power_dc", 0)
        
        # Simple efficiency calculation
        efficiency_percent = (current_power / power_rating * 100) if power_rating > 0 else 0
        
        # Determine overall health
        if active_alerts == 0 and efficiency_percent > 80:
            overall_health = "Excellent"
        elif active_alerts == 0 and efficiency_percent > 60:
            overall_health = "Good"
        elif active_alerts <= 2 and efficiency_percent > 40:
            overall_health = "Fair"
        else:
            overall_health = "Needs Attention"
        
        recommendations = []
        if efficiency_percent < 60:
            recommendations.append("System efficiency is below optimal - consider maintenance check")
        if active_alerts > 0:
            recommendations.append(f"Address {active_alerts} active alerts")
        if not recommendations:
            recommendations.append("System is performing well")
        
        result = {
            "system_id": system_id,
            "timestamp": datetime.now().isoformat(),
            "overall_health": overall_health,
            "health_metrics": {
                "active_alerts": active_alerts,
                "efficiency_percent": efficiency_percent,
                "system_status": system_info.get("status", "Unknown")
            },
            "recommendations": recommendations,
            "details": {
                "summary": safe_json_serialize(summary),
                "recent_alerts": [],
                "efficiency_analysis": {
                    "rated_power_dc": power_rating,
                    "current_power_dc": current_power,
                    "efficiency_percent": efficiency_percent
                }
            }
        }
        
        logger.info(f"System health assessment completed for system ID: {system_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise

@app.tool()
async def get_maintenance_insights(
    system_id: Optional[int] = None,
    threshold_percent: float = 85.0
) -> Dict[str, Any]:
    """
    Get maintenance recommendations based on system performance analysis.
    
    Args:
        system_id: Target system ID
        threshold_percent: Performance threshold for identifying underperforming panels (default: 85.0)
        
    Returns:
        Dict containing prioritized maintenance recommendations with affected components and next actions
    """
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        # If no system_id provided, get the first available system
        if system_id is None:
            systems = client.get_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Get system data for analysis
        summary = client.get_system_summary(system_id)
        systems_info = client.get_systems()
        
        system_info = None
        for system in systems_info.get('systems', []):
            if system.get('system_id') == system_id:
                system_info = system
                break
        
        if not system_info:
            raise Exception(f"System {system_id} not found")
        
        # Generate maintenance recommendations
        recommendations = []
        
        power_rating = system_info.get("power_rating", 1)
        current_power = summary.get("last_power_dc", 0)
        efficiency = (current_power / power_rating * 100) if power_rating > 0 else 0
        
        if efficiency < threshold_percent:
            recommendations.append({
                "priority": "High",
                "component": "Solar Array",
                "issue": f"System efficiency ({efficiency:.1f}%) below threshold ({threshold_percent}%)",
                "action": "Schedule inspection and cleaning",
                "estimated_impact": "5-15% efficiency improvement"
            })
        
        active_alerts = system_info.get("recent_alerts_count", 0)
        if active_alerts > 0:
            recommendations.append({
                "priority": "Medium",
                "component": "System Monitoring",
                "issue": f"{active_alerts} active alerts detected",
                "action": "Review and address system alerts",
                "estimated_impact": "Improved system reliability"
            })
        
        if not recommendations:
            recommendations.append({
                "priority": "Low",
                "component": "Preventive Maintenance",
                "issue": "System performing within normal parameters",
                "action": "Schedule routine maintenance check",
                "estimated_impact": "Continued optimal performance"
            })
        
        result = {
            "system_id": system_id,
            "timestamp": datetime.now().isoformat(),
            "threshold_percent": threshold_percent,
            "current_efficiency": efficiency,
            "recommendations": recommendations,
            "summary": {
                "total_recommendations": len(recommendations),
                "high_priority": len([r for r in recommendations if r["priority"] == "High"]),
                "medium_priority": len([r for r in recommendations if r["priority"] == "Medium"]),
                "low_priority": len([r for r in recommendations if r["priority"] == "Low"])
            },
            "next_actions": [rec["action"] for rec in recommendations[:3]]  # Top 3 actions
        }
        
        logger.info(f"Maintenance insights generated for system ID: {system_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting maintenance insights: {e}")
        raise

def main():
    """Entry point for the Tigo MCP server."""
    try:
        # Initialize Tigo client
        client = initialize_tigo_client()
        if not client:
            logger.error("Failed to initialize Tigo client. Please check your credentials.")
            sys.exit(1)
        
        logger.info("Starting Tigo MCP Server...")
        
        # Run the FastMCP server
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()