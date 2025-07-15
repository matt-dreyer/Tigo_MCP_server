# server.py

import os
import json
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from typing import Optional, Dict, Any
from datetime import datetime
from tigo_python.client import TigoClient

#
# Load environment variables
#
load_dotenv()
USERNAME = os.getenv("TIGO_USERNAME")
PASSWORD = os.getenv("TIGO_PASSWORD")

print(f"Username loaded: {USERNAME is not None}")
print(f"Password loaded: {PASSWORD is not None}")

# Create an MCP server
mcp = FastMCP(name="Tigo")

def safe_json_response(data: Any) -> str:
    """Safely convert data to JSON string with error handling."""
    try:
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": f"JSON serialization error: {str(e)}"}, indent=2)

def get_primary_system_id(client: TigoClient) -> Optional[int]:
    """Get the primary system ID from the user's systems."""
    try:
        systems = client.list_systems()
        system_list = systems.get("systems", [])
        if system_list:
            return system_list[0]["system_id"]  # Return first system
        return None
    except Exception:
        return None

#
# Core Configuration & System Info
#
@mcp.tool("Fetch_Configuration")
async def fetch_configuration() -> str:
    """
    Query the Tigo API for the runtime status of system
    """
    try:
        with TigoClient(USERNAME, PASSWORD) as client:
            user = client.get_user()
            systems = client.list_systems()
            
            response_data = {
                "user": user,
                "systems": systems
            }
            
            return safe_json_response(response_data)
        
    except Exception as e:
        error_msg = f"Error fetching Tigo data: {str(e)}"
        print(error_msg)
        return safe_json_response({"error": error_msg})

@mcp.tool("Get_System_Details")
async def get_system_details(system_id: Optional[int] = None) -> str:
    """
    Get detailed information about a specific system including layout, sources, and summary.
    If no system_id provided, uses the first available system.
    """
    try:
        with TigoClient(USERNAME, PASSWORD) as client:
            if system_id is None:
                system_id = get_primary_system_id(client)
                if system_id is None:
                    return safe_json_response({"error": "No systems found"})
            
            system_info = client.get_system_info(system_id)
            return safe_json_response(system_info)
        
    except Exception as e:
        return safe_json_response({"error": f"Error fetching system details: {str(e)}"})

#
# Production & Performance Data
#
@mcp.tool("Get_Current_Production")
async def get_current_production(system_id: Optional[int] = None) -> str:
    """
    Get today's production data and real-time system summary.
    """
    try:
        with TigoClient(USERNAME, PASSWORD) as client:
            if system_id is None:
                system_id = get_primary_system_id(client)
                if system_id is None:
                    return safe_json_response({"error": "No systems found"})
            
            # Get today's data and current summary
            today_data = client.get_today_data(system_id)
            summary = client.get_summary(system_id)
            
            response_data = {
                "system_id": system_id,
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "today_production": {
                    "data_points": len(today_data),
                    "columns": list(today_data.columns) if not today_data.empty else [],
                    "latest_values": today_data.tail(1).to_dict('records') if not today_data.empty else [],
                    "total_production_today": today_data.iloc[:, 0].sum() if not today_data.empty else 0
                }
            }
            
            return safe_json_response(response_data)
        
    except Exception as e:
        return safe_json_response({"error": f"Error fetching current production: {str(e)}"})

@mcp.tool("Get_Performance_Analysis")
async def get_performance_analysis(system_id: Optional[int] = None, days_back: int = 7) -> str:
    """
    Get comprehensive performance analysis including efficiency metrics and panel performance.
    """
    try:
        with TigoClient(USERNAME, PASSWORD) as client:
            if system_id is None:
                system_id = get_primary_system_id(client)
                if system_id is None:
                    return safe_json_response({"error": "No systems found"})
            
            # Get performance metrics
            efficiency_metrics = client.calculate_system_efficiency(system_id, days_back)
            panel_performance = client.get_panel_performance(system_id, days_back)
            underperforming = client.find_underperforming_panels(system_id, days_back=days_back)
            
            response_data = {
                "system_id": system_id,
                "analysis_period_days": days_back,
                "timestamp": datetime.now().isoformat(),
                "efficiency_metrics": efficiency_metrics,
                "panel_performance": {
                    "total_panels": len(panel_performance),
                    "top_performers": panel_performance.head(5).to_dict('records') if not panel_performance.empty else [],
                    "bottom_performers": panel_performance.tail(5).to_dict('records') if not panel_performance.empty else []
                },
                "underperforming_panels": underperforming,
                "performance_summary": {
                    "panels_below_85_percent": len(underperforming),
                    "avg_panel_efficiency": (panel_performance['mean_power'].mean() / panel_performance['mean_power'].max() * 100) if not panel_performance.empty else 0
                }
            }
            
            return safe_json_response(response_data)
        
    except Exception as e:
        return safe_json_response({"error": f"Error fetching performance analysis: {str(e)}"})

@mcp.tool("Get_Historical_Data")
async def get_historical_data(system_id: Optional[int] = None, days_back: int = 30, level: str = "day") -> str:
    """
    Get historical production data for analysis.
    
    Args:
        system_id: System ID (optional, uses first system if not provided)
        days_back: Number of days of historical data (default: 30)
        level: Data granularity - "minute", "hour", or "day" (default: "day")
    """
    try:
        with TigoClient(USERNAME, PASSWORD) as client:
            if system_id is None:
                system_id = get_primary_system_id(client)
                if system_id is None:
                    return safe_json_response({"error": "No systems found"})
            
            # Validate level parameter
            if level not in ["minute", "hour", "day"]:
                return safe_json_response({"error": "Level must be 'minute', 'hour', or 'day'"})
            
            # Get historical data
            data = client.get_date_range_data(system_id, days_back, level)
            
            response_data = {
                "system_id": system_id,
                "days_back": days_back,
                "level": level,
                "timestamp": datetime.now().isoformat(),
                "data_summary": {
                    "total_data_points": len(data),
                    "date_range": {
                        "start": data.index.min().isoformat() if not data.empty else None,
                        "end": data.index.max().isoformat() if not data.empty else None
                    },
                    "columns": list(data.columns),
                    "total_production": data.iloc[:, 0].sum() if not data.empty else 0,
                    "average_power": data.iloc[:, 0].mean() if not data.empty else 0,
                    "peak_power": data.iloc[:, 0].max() if not data.empty else 0
                },
                "sample_data": data.head(10).to_dict('records') if not data.empty else []
            }
            
            return safe_json_response(response_data)
        
    except Exception as e:
        return safe_json_response({"error": f"Error fetching historical data: {str(e)}"})

#
# System Health & Alerts
#
@mcp.tool("Get_System_Alerts")
async def get_system_alerts(system_id: Optional[int] = None, days_back: int = 30) -> str:
    """
    Get recent alerts and system health information.
    """
    try:
        with TigoClient(USERNAME, PASSWORD) as client:
            if system_id is None:
                system_id = get_primary_system_id(client)
                if system_id is None:
                    return safe_json_response({"error": "No systems found"})
            
            # Calculate start date for alerts
            from datetime import datetime, timedelta
            start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            # Get alerts and alert types
            alerts = client.get_alerts(system_id, start_added=start_date)
            alert_types = client.get_alert_types()
            
            response_data = {
                "system_id": system_id,
                "days_back": days_back,
                "timestamp": datetime.now().isoformat(),
                "alerts": alerts,
                "alert_types": alert_types,
                "alert_summary": {
                    "total_alerts": len(alerts.get("alerts", [])),
                    "active_alerts": len([a for a in alerts.get("alerts", []) if a.get("status") == "active"]),
                    "recent_alerts": alerts.get("alerts", [])[:5]  # Most recent 5 alerts
                }
            }
            
            return safe_json_response(response_data)
        
    except Exception as e:
        return safe_json_response({"error": f"Error fetching system alerts: {str(e)}"})

@mcp.tool("Get_System_Health")
async def get_system_health(system_id: Optional[int] = None) -> str:
    """
    Get comprehensive system health status combining multiple data sources.
    """
    try:
        with TigoClient(USERNAME, PASSWORD) as client:
            if system_id is None:
                system_id = get_primary_system_id(client)
                if system_id is None:
                    return safe_json_response({"error": "No systems found"})
            
            # Get multiple health indicators
            summary = client.get_summary(system_id)
            alerts = client.get_alerts(system_id)
            efficiency = client.calculate_system_efficiency(system_id, days_back=7)
            
            # Determine overall health status
            alert_count = len(alerts.get("alerts", []))
            efficiency_percent = efficiency.get("average_efficiency_percent", 0)
            
            if alert_count == 0 and efficiency_percent > 80:
                health_status = "Excellent"
            elif alert_count <= 2 and efficiency_percent > 70:
                health_status = "Good"
            elif alert_count <= 5 and efficiency_percent > 60:
                health_status = "Fair"
            else:
                health_status = "Needs Attention"
            
            response_data = {
                "system_id": system_id,
                "timestamp": datetime.now().isoformat(),
                "overall_health": health_status,
                "health_metrics": {
                    "active_alerts": alert_count,
                    "efficiency_percent": efficiency_percent,
                    "system_status": summary.get("status", "Unknown")
                },
                "recommendations": [],
                "details": {
                    "summary": summary,
                    "recent_alerts": alerts.get("alerts", [])[:3],
                    "efficiency_analysis": efficiency
                }
            }
            
            # Add recommendations based on health status
            if alert_count > 0:
                response_data["recommendations"].append("Review and address active system alerts")
            if efficiency_percent < 70:
                response_data["recommendations"].append("System efficiency is below optimal - consider maintenance check")
            if health_status == "Excellent":
                response_data["recommendations"].append("System is performing optimally")
            
            return safe_json_response(response_data)
        
    except Exception as e:
        return safe_json_response({"error": f"Error fetching system health: {str(e)}"})

#
# Maintenance & Operations
#
@mcp.tool("Get_Maintenance_Insights")
async def get_maintenance_insights(system_id: Optional[int] = None, threshold_percent: float = 85.0) -> str:
    """
    Get maintenance recommendations based on system performance analysis.
    """
    try:
        with TigoClient(USERNAME, PASSWORD) as client:
            if system_id is None:
                system_id = get_primary_system_id(client)
                if system_id is None:
                    return safe_json_response({"error": "No systems found"})
            
            # Get performance data for analysis
            underperforming = client.find_underperforming_panels(system_id, threshold_percent=threshold_percent)
            efficiency = client.calculate_system_efficiency(system_id, days_back=30)
            alerts = client.get_alerts(system_id)
            
            maintenance_items = []
            priority_score = 0
            
            # Analyze underperforming panels
            if len(underperforming) > 0:
                maintenance_items.append({
                    "category": "Panel Performance",
                    "issue": f"{len(underperforming)} panels performing below {threshold_percent}%",
                    "priority": "High" if len(underperforming) > 3 else "Medium",
                    "recommendation": "Inspect underperforming panels for soiling, shading, or hardware issues",
                    "affected_panels": [p["panel_id"] for p in underperforming[:5]]
                })
                priority_score += len(underperforming) * 10
            
            # Analyze system efficiency
            avg_efficiency = efficiency.get("average_efficiency_percent", 100)
            if avg_efficiency < 70:
                maintenance_items.append({
                    "category": "System Efficiency", 
                    "issue": f"Overall system efficiency at {avg_efficiency:.1f}%",
                    "priority": "High",
                    "recommendation": "Schedule comprehensive system inspection and cleaning"
                })
                priority_score += 50
            elif avg_efficiency < 85:
                maintenance_items.append({
                    "category": "System Efficiency",
                    "issue": f"System efficiency below optimal at {avg_efficiency:.1f}%", 
                    "priority": "Medium",
                    "recommendation": "Consider panel cleaning and connection inspection"
                })
                priority_score += 25
            
            # Analyze alerts
            active_alerts = [a for a in alerts.get("alerts", []) if a.get("status") == "active"]
            if len(active_alerts) > 0:
                maintenance_items.append({
                    "category": "System Alerts",
                    "issue": f"{len(active_alerts)} active system alerts",
                    "priority": "High",
                    "recommendation": "Address active alerts immediately",
                    "alert_details": active_alerts[:3]
                })
                priority_score += len(active_alerts) * 15
            
            # Determine overall maintenance priority
            if priority_score > 100:
                overall_priority = "Critical"
            elif priority_score > 50:
                overall_priority = "High"
            elif priority_score > 25:
                overall_priority = "Medium"
            else:
                overall_priority = "Low"
            
            response_data = {
                "system_id": system_id,
                "timestamp": datetime.now().isoformat(),
                "overall_maintenance_priority": overall_priority,
                "priority_score": priority_score,
                "maintenance_items": maintenance_items,
                "summary": {
                    "total_issues": len(maintenance_items),
                    "critical_issues": len([item for item in maintenance_items if item["priority"] == "High"]),
                    "system_efficiency": avg_efficiency,
                    "underperforming_panels": len(underperforming)
                },
                "next_recommended_action": maintenance_items[0]["recommendation"] if maintenance_items else "System is performing well - continue regular monitoring"
            }
            
            return safe_json_response(response_data)
        
    except Exception as e:
        return safe_json_response({"error": f"Error fetching maintenance insights: {str(e)}"})

# Run the MCP server
if __name__ == "__main__":
    mcp.run(transport="stdio")