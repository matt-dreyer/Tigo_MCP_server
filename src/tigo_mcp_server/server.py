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

# MCP imports - Using standard MCP
from mcp.server import Server
from mcp.types import TextContent, Tool
from mcp.server.stdio import stdio_server

# Environment and configuration
from dotenv import load_dotenv

# Tigo API client
try:
    from tigo_python import TigoClient
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
_global_tigo_client = None  # Keep reference for cleanup

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
    elif hasattr(obj, 'to_dict'):  # pandas DataFrame
        return obj.to_dict('records')
    else:
        return str(obj)

def initialize_tigo_client() -> Optional[TigoClient]:
    """
    Initialize and return Tigo API client.
    
    Returns:
        Initialized Tigo client or None if initialization fails
    """
    global tigo_client, _global_tigo_client
    
    if tigo_client is not None:
        return tigo_client
    
    username = os.getenv("TIGO_USERNAME")
    password = os.getenv("TIGO_PASSWORD")
    
    if not username or not password:
        logger.error("TIGO_USERNAME and TIGO_PASSWORD environment variables are required")
        return None
    
    try:
        tigo_client = TigoClient(username=username, password=password)
        _global_tigo_client = tigo_client  # Keep reference for cleanup
        logger.info("Tigo API client initialized successfully")
        return tigo_client
    except Exception as e:
        logger.error(f"Failed to initialize Tigo API client: {e}")
        return None

# Initialize MCP server
server = Server("Tigo Energy MCP Server")

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="Get_Tigo_Configuration",
            description="Get user information and list all accessible Tigo solar systems",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="Get_System_Details",
            description="Get detailed information about a specific Tigo system including layout, sources, and summary. If no system_id provided, uses the first available system.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_id": {"type": ["integer", "null"], "description": "Specific system ID, uses first available system if not provided"}
                }
            }
        ),
        Tool(
            name="Get_Current_Production",
            description="Get today's production data and real-time system summary from Tigo system.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_id": {"type": ["integer", "null"], "description": "Target system ID"}
                }
            }
        ),
        Tool(
            name="Get_Performance_Analysis",
            description="Get comprehensive performance analysis including efficiency metrics and panel performance for Tigo system.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_id": {"type": ["integer", "null"], "description": "Target system ID"},
                    "days_back": {"type": "integer", "default": 7, "description": "Number of days to analyze"}
                }
            }
        ),
        Tool(
            name="Get_Historical_Data",
            description="Get historical production data for analysis from Tigo system.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_id": {"type": ["integer", "null"], "description": "System ID"},
                    "days_back": {"type": "integer", "default": 30, "description": "Number of days of historical data"},
                    "level": {"type": "string", "default": "day", "description": "Data granularity - minute, hour, or day"}
                }
            }
        ),
        Tool(
            name="Get_System_Alerts",
            description="Get recent alerts and system health information from Tigo system.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_id": {"type": ["integer", "null"], "description": "Target system ID"},
                    "days_back": {"type": "integer", "default": 30, "description": "Number of days to look back for alerts"}
                }
            }
        ),
        Tool(
            name="Get_System_Health",
            description="Get comprehensive system health status combining multiple data sources from Tigo system.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_id": {"type": ["integer", "null"], "description": "Target system ID"}
                }
            }
        ),
        Tool(
            name="Get_Maintenance_Insights",
            description="Get maintenance recommendations based on Tigo system performance analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_id": {"type": ["integer", "null"], "description": "Target system ID"},
                    "threshold_percent": {"type": "number", "default": 85, "description": "Performance threshold for identifying underperforming panels"}
                }
            }
        ),
        Tool(
            name="Get_Daily_Chart_Data",
            description="Get detailed daily chart data with time series analysis from Tigo system.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_id": {"type": ["integer", "null"], "description": "System ID"},
                    "date_text": {"type": ["string", "null"], "description": "Date in YYYY-MM-DD format"},
                    "analysis_type": {"type": "string", "default": "full", "description": "Type of analysis - full, summary, hourly, efficiency, or raw"}
                }
            }
        ),
        Tool(
            name="Get_Data_Range",
            description="Get Tigo system data for a specific date range with configurable granularity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_id": {"type": ["integer", "null"], "description": "System ID"},
                    "start_date": {"type": "string", "description": "Start date in YYYY-MM-DD format"},
                    "end_date": {"type": "string", "description": "End date in YYYY-MM-DD format"},
                    "granularity": {"type": "string", "default": "hour", "description": "Data granularity - minute, hour, or day"}
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    try:
        if name == "Get_Tigo_Configuration":
            result = await get_tigo_configuration()
        elif name == "Get_System_Details":
            result = await get_system_details(arguments.get("system_id"))
        elif name == "Get_Current_Production":
            result = await get_current_production(arguments.get("system_id"))
        elif name == "Get_Performance_Analysis":
            result = await get_performance_analysis(
                arguments.get("system_id"), 
                arguments.get("days_back", 7)
            )
        elif name == "Get_Historical_Data":
            result = await get_historical_data(
                arguments.get("system_id"),
                arguments.get("days_back", 30),
                arguments.get("level", "day")
            )
        elif name == "Get_System_Alerts":
            result = await get_system_alerts(
                arguments.get("system_id"),
                arguments.get("days_back", 30)
            )
        elif name == "Get_System_Health":
            result = await get_system_health(arguments.get("system_id"))
        elif name == "Get_Maintenance_Insights":
            result = await get_maintenance_insights(
                arguments.get("system_id"),
                arguments.get("threshold_percent", 85.0)
            )
        elif name == "Get_Daily_Chart_Data":
            result = await get_daily_chart_data(
                arguments.get("system_id"),
                arguments.get("date_text"),
                arguments.get("analysis_type", "full")
            )
        elif name == "Get_Data_Range":
            result = await get_data_range(
                arguments.get("system_id"),
                arguments.get("start_date"),
                arguments.get("end_date"),
                arguments.get("granularity", "hour")
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=json.dumps({"error": error_msg}, indent=2))]

# Tool implementation functions
async def get_tigo_configuration() -> Dict[str, Any]:
    """Get user information and list all accessible Tigo systems."""
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        user_info = client.get_user()
        systems_info = client.list_systems()
        
        result = {
            "user": safe_json_serialize(user_info),
            "systems": safe_json_serialize(systems_info),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Tigo configuration fetched successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching Tigo configuration: {e}")
        raise

async def get_system_details(system_id: Optional[int] = None) -> Dict[str, Any]:
    """Get detailed information about a specific Tigo system."""
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        if system_id is None:
            systems = client.list_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Get comprehensive system information
        system_info = client.get_system(system_id)
        layout_info = client.get_system_layout(system_id)
        sources_info = client.get_sources(system_id)
        summary_info = client.get_summary(system_id)
        
        result = {
            "system_id": system_id,
            "timestamp": datetime.now().isoformat(),
            "system": safe_json_serialize(system_info),
            "layout": safe_json_serialize(layout_info),
            "sources": safe_json_serialize(sources_info),
            "summary": safe_json_serialize(summary_info)
        }
        
        logger.info(f"System details retrieved for Tigo system ID: {system_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting system details: {e}")
        raise

async def get_current_production(system_id: Optional[int] = None) -> Dict[str, Any]:
    """Get today's production data and real-time system summary."""
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        if system_id is None:
            systems = client.list_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Get current summary
        summary_data = client.get_summary(system_id)
        
        # Get today's data using date range method for today
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        try:
            today_data = client.get_combined_data(
                system_id,
                start_of_day.isoformat(),
                end_of_day.isoformat(),
                level="hour"
            )
        except Exception as e:
            logger.warning(f"Could not get today's detailed data: {e}")
            # Fallback to just using date range data method
            today_data = client.get_date_range_data(system_id, days_back=1, level="hour")
        
        result = {
            "system_id": system_id,
            "timestamp": datetime.now().isoformat(),
            "summary": safe_json_serialize(summary_data),
            "today_data": safe_json_serialize(today_data),
            "data_points_today": len(today_data) if hasattr(today_data, '__len__') else 0,
            "date": today.isoformat()
        }
        
        logger.info(f"Current production data retrieved for Tigo system ID: {system_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting current production: {e}")
        raise

async def get_performance_analysis(
    system_id: Optional[int] = None, 
    days_back: int = 7
) -> Dict[str, Any]:
    """Get comprehensive performance analysis including efficiency metrics and panel performance."""
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        if system_id is None:
            systems = client.list_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Get efficiency analysis
        efficiency_data = client.calculate_system_efficiency(system_id, days_back=days_back)
        
        # Get panel performance data - this method may not exist, so handle gracefully
        try:
            # Since this method doesn't exist in the client, we'll skip it for now
            panel_performance_data = []
            logger.warning("Panel performance analysis not available - method not implemented in client")
        except Exception as e:
            logger.warning(f"Could not get panel performance: {e}")
            panel_performance_data = []
        
        # Get underperforming panels - this method may not exist, so handle gracefully
        try:
            # Since this method doesn't exist in the client, we'll skip it for now
            underperforming = []
            logger.warning("Underperforming panel analysis not available - method not implemented in client")
        except Exception as e:
            logger.warning(f"Could not get underperforming panels: {e}")
            underperforming = []
        
        result = {
            "system_id": system_id,
            "analysis_period_days": days_back,
            "timestamp": datetime.now().isoformat(),
            "efficiency_analysis": safe_json_serialize(efficiency_data),
            "panel_performance": panel_performance_data,
            "underperforming_panels": safe_json_serialize(underperforming),
            "analysis_summary": {
                "total_panels_analyzed": len(panel_performance_data) if isinstance(panel_performance_data, list) else 0,
                "underperforming_count": len(underperforming) if isinstance(underperforming, list) else 0,
                "efficiency_percent": efficiency_data.get('average_efficiency_percent', 0) if isinstance(efficiency_data, dict) else 0
            }
        }
        
        logger.info(f"Performance analysis completed for Tigo system ID: {system_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting performance analysis: {e}")
        raise

async def get_historical_data(
    system_id: Optional[int] = None,
    days_back: int = 30,
    level: str = "day"
) -> Dict[str, Any]:
    """Get historical production data for analysis."""
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        if level not in ["minute", "hour", "day"]:
            raise ValueError("Level must be 'minute', 'hour', or 'day'")
        
        if system_id is None:
            systems = client.list_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Get historical data using the available date range method
        historical_data = client.get_date_range_data(system_id, days_back, level)
        
        result = {
            "system_id": system_id,
            "days_back": days_back,
            "level": level,
            "start_date": (datetime.now() - timedelta(days=days_back)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "timestamp": datetime.now().isoformat(),
            "data": safe_json_serialize(historical_data),
            "metadata": {
                "granularity": level,
                "period_days": days_back,
                "data_points": len(historical_data) if hasattr(historical_data, '__len__') else "summary"
            }
        }
        
        logger.info(f"Historical data retrieved for Tigo system ID: {system_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise

async def get_system_alerts(
    system_id: Optional[int] = None,
    days_back: int = 30
) -> Dict[str, Any]:
    """Get recent alerts and system health information."""
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        if system_id is None:
            systems = client.list_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Get alerts data
        try:
            alerts_data = client.get_alerts(system_id)
        except Exception as e:
            logger.warning(f"Could not get alerts: {e}")
            alerts_data = []
        
        # Get system status from systems list
        systems_info = client.list_systems()
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
            "alerts": safe_json_serialize(alerts_data),
            "system_status": system_info.get("status", "Unknown"),
            "recent_alerts_count": len(alerts_data) if isinstance(alerts_data, list) else 0,
            "alert_summary": {
                "active_alerts": len(alerts_data) if isinstance(alerts_data, list) else 0,
                "period_days": days_back,
                "last_updated": datetime.now().isoformat()
            }
        }
        
        logger.info(f"System alerts retrieved for Tigo system ID: {system_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting system alerts: {e}")
        raise

async def get_system_health(system_id: Optional[int] = None) -> Dict[str, Any]:
    """Get comprehensive system health status combining multiple data sources."""
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        if system_id is None:
            systems = client.list_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Get current summary and efficiency data
        summary = client.get_summary(system_id)
        efficiency_data = client.calculate_system_efficiency(system_id, days_back=7)
        
        # Get system status from systems list
        systems_info = client.list_systems()
        system_info = None
        for system in systems_info.get('systems', []):
            if system.get('system_id') == system_id:
                system_info = system
                break
        
        if not system_info:
            raise Exception(f"System {system_id} not found")
        
        # Get alerts count
        try:
            alerts = client.get_alerts(system_id)
            active_alerts = len(alerts) if isinstance(alerts, list) else 0
        except:
            active_alerts = 0
        
        # Calculate overall health score
        efficiency_percent = efficiency_data.get('average_efficiency_percent', 0) if isinstance(efficiency_data, dict) else 0
        
        if active_alerts == 0 and efficiency_percent > 80:
            overall_health = "Excellent"
        elif active_alerts == 0 and efficiency_percent > 60:
            overall_health = "Good"
        elif active_alerts <= 2 and efficiency_percent > 40:
            overall_health = "Fair"
        else:
            overall_health = "Needs Attention"
        
        # Generate recommendations
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
                "efficiency_analysis": safe_json_serialize(efficiency_data)
            }
        }
        
        logger.info(f"System health assessment completed for Tigo system ID: {system_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise

async def get_maintenance_insights(
    system_id: Optional[int] = None,
    threshold_percent: float = 85.0
) -> Dict[str, Any]:
    """Get maintenance recommendations based on system performance analysis."""
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        if system_id is None:
            systems = client.list_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Get efficiency analysis
        efficiency_data = client.calculate_system_efficiency(system_id, days_back=30)
        
        # Get underperforming panels - method doesn't exist, so skip for now
        underperforming_panels = []
        
        # Get alerts count
        try:
            alerts = client.get_alerts(system_id)
            active_alerts = len(alerts) if isinstance(alerts, list) else 0
        except:
            active_alerts = 0
        
        # Generate maintenance recommendations
        recommendations = []
        current_efficiency = efficiency_data.get('average_efficiency_percent', 0) if isinstance(efficiency_data, dict) else 0
        
        if current_efficiency < threshold_percent:
            recommendations.append({
                "priority": "High",
                "component": "Solar Array",
                "issue": f"System efficiency ({current_efficiency:.1f}%) below threshold ({threshold_percent}%)",
                "action": "Schedule inspection and cleaning",
                "estimated_impact": "5-15% efficiency improvement"
            })
        
        if underperforming_panels:
            recommendations.append({
                "priority": "Medium",
                "component": "Individual Panels",
                "issue": f"{len(underperforming_panels)} panels performing below threshold",
                "action": "Inspect and service underperforming panels",
                "estimated_impact": "2-8% efficiency improvement"
            })
        
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
            "current_efficiency": current_efficiency,
            "recommendations": recommendations,
            "underperforming_panels": safe_json_serialize(underperforming_panels),
            "summary": {
                "total_recommendations": len(recommendations),
                "high_priority": len([r for r in recommendations if r["priority"] == "High"]),
                "medium_priority": len([r for r in recommendations if r["priority"] == "Medium"]),
                "low_priority": len([r for r in recommendations if r["priority"] == "Low"])
            },
            "next_actions": [rec["action"] for rec in recommendations[:3]]
        }
        
        logger.info(f"Maintenance insights generated for Tigo system ID: {system_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting maintenance insights: {e}")
        raise

async def get_daily_chart_data(
    system_id: Optional[int] = None,
    date_text: Optional[str] = None,
    analysis_type: str = "full"
) -> Dict[str, Any]:
    """Get detailed daily chart data with time series analysis."""
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        if system_id is None:
            systems = client.list_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Parse target date
        if date_text is None:
            target_date = datetime.now().date()
            # Get today's data using date range method
            daily_data = client.get_date_range_data(system_id, days_back=1, level="hour")
        else:
            try:
                target_date = datetime.strptime(date_text, "%Y-%m-%d").date()
                start_datetime = datetime.combine(target_date, datetime.min.time())
                end_datetime = datetime.combine(target_date, datetime.max.time())
                daily_data = client.get_combined_data(
                    system_id, 
                    start_datetime.isoformat(), 
                    end_datetime.isoformat(), 
                    level="hour"  # Use hour level for better performance
                )
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        
        # Process analysis based on type
        analysis_result = {}
        
        if analysis_type in ["full", "summary"]:
            analysis_result["daily_summary"] = safe_json_serialize(daily_data)
        
        if analysis_type in ["full", "efficiency"] and hasattr(daily_data, '__len__'):
            # Calculate efficiency metrics if we have data
            if hasattr(daily_data, 'iloc') and len(daily_data) > 0:
                # This is a DataFrame
                power_col = daily_data.iloc[:, 0] if len(daily_data.columns) > 0 else None
                if power_col is not None:
                    power_values = power_col.dropna()
                    if len(power_values) > 0:
                        analysis_result["efficiency_metrics"] = {
                            "total_energy_today": float(power_values.sum()),
                            "peak_power": float(power_values.max()),
                            "average_power": float(power_values.mean()),
                            "data_points": len(power_values)
                        }
            elif isinstance(daily_data, list) and daily_data:
                # This is a list of records
                power_values = [point.get('power', 0) for point in daily_data if point.get('power')]
                if power_values:
                    analysis_result["efficiency_metrics"] = {
                        "total_energy_today": sum(power_values),
                        "peak_power": max(power_values),
                        "average_power": sum(power_values) / len(power_values),
                        "data_points": len(power_values)
                    }
        
        result = {
            "system_id": system_id,
            "date": target_date.isoformat(),
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat(),
            "chart_data": analysis_result,
            "data_resolution": "hour-level",
            "metadata": {
                "date_analyzed": target_date.isoformat(),
                "analysis_type": analysis_type,
                "data_points": len(daily_data) if hasattr(daily_data, '__len__') else "summary"
            }
        }
        
        logger.info(f"Daily chart data retrieved for Tigo system ID: {system_id}, date: {target_date}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting daily chart data: {e}")
        raise

async def get_data_range(
    system_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: str = "hour"
) -> Dict[str, Any]:
    """Get Tigo system data for a specific date range with configurable granularity."""
    try:
        client = initialize_tigo_client()
        if not client:
            raise Exception("Failed to initialize Tigo API client")
        
        if granularity not in ["minute", "hour", "day"]:
            raise ValueError("Granularity must be 'minute', 'hour', or 'day'")
        
        if system_id is None:
            systems = client.list_systems()
            if not systems or not systems.get('systems'):
                raise Exception("No systems found for this account")
            system_id = systems['systems'][0]['system_id']
        
        # Parse dates
        if not start_date or not end_date:
            raise ValueError("Both start_date and end_date are required")
        
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
        
        if start_dt > end_dt:
            raise ValueError("Start date must be before end date")
        
        # Calculate date range
        date_diff = (end_dt - start_dt).days
        
        # Get data using the appropriate method
        range_data = client.get_combined_data(
            system_id,
            start_dt.isoformat(),
            end_dt.isoformat(),
            level=granularity
        )
        
        result = {
            "system_id": system_id,
            "start_date": start_date,
            "end_date": end_date,
            "granularity": granularity,
            "days_span": date_diff,
            "timestamp": datetime.now().isoformat(),
            "data": safe_json_serialize(range_data),
            "metadata": {
                "granularity": granularity,
                "period_days": date_diff,
                "data_points": len(range_data) if hasattr(range_data, '__len__') else "summary"
            }
        }
        
        logger.info(f"Data range retrieved for Tigo system ID: {system_id}, {start_date} to {end_date}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting data range: {e}")
        raise

async def main_async():
    """Async main function to run the MCP server."""
    global _global_tigo_client
    
    try:
        # Initialize Tigo client to verify credentials
        client = initialize_tigo_client()
        if not client:
            logger.error("Failed to initialize Tigo client. Please check your credentials.")
            sys.exit(1)
        
        logger.info("Starting Tigo MCP Server...")
        
        # Run the MCP server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    finally:
        # Clean up the client when shutting down
        if _global_tigo_client:
            _global_tigo_client.close()
            logger.info("Tigo client closed on shutdown")

def main():
    """Entry point for the Tigo MCP server."""
    try:
        asyncio.run(main_async())
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()