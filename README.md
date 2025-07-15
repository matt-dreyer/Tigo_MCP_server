# Tigo Energy MCP Server

A Model Context Protocol (MCP) server that provides comprehensive access to Tigo Energy solar system data and analytics. This server enables AI assistants to interact with your Tigo solar monitoring system to retrieve production data, performance metrics, system health information, and maintenance insights.

## Features

### Core Functionality
- **System Configuration**: Access user account and system information
- **Real-time Production**: Get current solar production data and system summary
- **Performance Analysis**: Comprehensive efficiency metrics and panel performance evaluation
- **Historical Data**: Retrieve production data with configurable time ranges and granularity
- **System Health**: Monitor alerts and overall system status
- **Maintenance Insights**: AI-powered recommendations based on performance analysis

### Key Capabilities
- Monitor multiple solar systems (automatically uses primary system if not specified)
- Identify underperforming panels with customizable thresholds
- Calculate system efficiency metrics over configurable time periods
- Track and analyze system alerts and their types
- Generate maintenance recommendations with priority scoring
- Support for minute, hour, and day-level historical data analysis

## Installation

### Prerequisites
- Python 3.8 or higher
- A Tigo Energy account with API access
- Required Python packages (install via pip):

```bash
pip install python-dotenv mcp tigo-python fastmcp
```

### Setup

1. **Clone or download the server files**
   ```bash
   # Save the server.py file to your desired location
   ```

2. **Configure environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your Tigo credentials
   TIGO_USERNAME=your_tigo_username
   TIGO_PASSWORD=your_tigo_password
   ```

3. **Test the server**
   ```bash
   python server.py
   ```

## Configuration

### Environment Variables

Create a `.env` file in the same directory as `server.py`:

```env
TIGO_USERNAME=your_tigo_username
TIGO_PASSWORD=your_tigo_password
```

**Security Note**: Keep your `.env` file secure and never commit it to version control. The `.env.example` file is provided as a template.

## Available Tools

### System Information Tools

#### `Fetch_Configuration`
Retrieves user account information and lists all available solar systems.

**Returns**: User details and system list with IDs and basic information.

#### `Get_System_Details`
Get comprehensive information about a specific solar system including layout, sources, and detailed specifications.

**Parameters**:
- `system_id` (optional): Specific system ID, uses first available system if not provided

### Production & Performance Tools

#### `Get_Current_Production`
Retrieve today's production data and real-time system summary.

**Parameters**:
- `system_id` (optional): Target system ID

**Returns**: Current production metrics, today's generation data, and system status.

#### `Get_Performance_Analysis`
Comprehensive performance analysis including efficiency metrics and panel-by-panel performance.

**Parameters**:
- `system_id` (optional): Target system ID
- `days_back` (default: 7): Number of days to analyze

**Returns**: Efficiency metrics, top/bottom performing panels, and performance summary.

#### `Get_Historical_Data`
Retrieve historical production data with configurable granularity.

**Parameters**:
- `system_id` (optional): Target system ID
- `days_back` (default: 30): Number of days of historical data
- `level` (default: "day"): Data granularity - "minute", "hour", or "day"

**Returns**: Historical production data with statistical summary.

### System Health Tools

#### `Get_System_Alerts`
Retrieve recent system alerts and health information.

**Parameters**:
- `system_id` (optional): Target system ID
- `days_back` (default: 30): Number of days to look back for alerts

**Returns**: Active and recent alerts with categorization and status.

#### `Get_System_Health`
Comprehensive system health status combining multiple data sources.

**Parameters**:
- `system_id` (optional): Target system ID

**Returns**: Overall health rating (Excellent/Good/Fair/Needs Attention) with supporting metrics and recommendations.

### Maintenance Tools

#### `Get_Maintenance_Insights`
AI-powered maintenance recommendations based on performance analysis.

**Parameters**:
- `system_id` (optional): Target system ID
- `threshold_percent` (default: 85.0): Performance threshold for identifying underperforming panels

**Returns**: Prioritized maintenance recommendations with affected components and next actions.

## Usage Examples

### Basic System Status Check
```python
# Get overall system health
health_status = await get_system_health()

# Check for any alerts
alerts = await get_system_alerts(days_back=7)

# Get current production
production = await get_current_production()
```

### Performance Analysis
```python
# Analyze performance over the last 30 days
performance = await get_performance_analysis(days_back=30)

# Get historical data at hourly granularity
historical = await get_historical_data(days_back=7, level="hour")

# Find maintenance issues
maintenance = await get_maintenance_insights(threshold_percent=80.0)
```

### Multi-System Management
```python
# Get all systems first
config = await fetch_configuration()

# Analyze specific system
system_details = await get_system_details(system_id=12345)
performance = await get_performance_analysis(system_id=12345, days_back=14)
```

## Integration with AI Assistants

This MCP server is designed to work seamlessly with AI assistants like Claude. The server provides structured JSON responses that enable natural language interactions about your solar system:

- "How is my solar system performing today?"
- "Show me any underperforming panels"
- "What maintenance does my system need?"
- "Compare this month's production to last month"
- "Are there any active alerts I should know about?"

## Error Handling

The server includes comprehensive error handling:
- Safe JSON serialization with fallback for complex data types
- Graceful handling of API connection issues
- Automatic fallback to primary system when system_id is not specified
- Detailed error messages for troubleshooting

## Security Considerations

- Credentials are loaded from environment variables, never hardcoded
- The server uses the official Tigo Python client with proper authentication
- All API responses are properly sanitized before returning
- No sensitive information is logged or exposed

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify your Tigo username and password in the `.env` file
   - Ensure your Tigo account has API access enabled

2. **No Systems Found**
   - Check that your Tigo account has associated solar systems
   - Verify the systems are properly configured in your Tigo dashboard

3. **Connection Issues**
   - Check your internet connection
   - Verify Tigo API service status

### Debug Mode
Set debug logging by modifying the server startup:
```python
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    mcp.run(transport="stdio")
```

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing patterns and error handling
- New tools include proper documentation
- Environment variables are used for configuration
- JSON responses are properly structured and safe

## License

This project uses the Tigo Python API client and follows its licensing terms. Please refer to the Tigo Energy API documentation for usage guidelines and restrictions.

## Support

For issues related to:
- **MCP Server**: Create an issue in this repository
- **Tigo API**: Contact Tigo Energy support
- **Tigo Python Client**: Refer to the tigo-python package documentation

---

*This MCP server enables powerful AI-driven solar system monitoring and maintenance insights. Monitor your solar investment with confidence and get proactive maintenance recommendations to maximize your system's performance.*