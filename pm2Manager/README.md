# PM2 Manager Plugin for CyberPanel

**Author:** Master3395  
**Version:** 1.1.0  
**Compatible with:** CyberPanel 2.5.5-dev and higher

## Description

PM2 Manager is a comprehensive process management plugin for CyberPanel that provides a web-based interface for managing PM2 applications. It offers real-time monitoring, process control, and detailed statistics - essentially a domain manager but for PM2 processes.

## Features

- **Real-time Monitoring**: Live updates of PM2 processes with WebSocket support (fallback to polling)
- **Process Control**: Start, stop, restart, and delete PM2 applications
- **Individual Node Details**: View detailed information for each PM2 application
- **Resource Tracking**: Monitor CPU and memory usage with visual indicators
- **Application Management**: Add new PM2 applications through the web interface
- **Cluster Mode Support**: Manage applications running in cluster mode
- **Log Viewing**: View real-time and historical logs for each application
- **Statistics Dashboard**: Overview of all PM2 applications with aggregate statistics
- **Memory Limit Configuration**: Set memory limits with automatic restart when exceeded
- **Auto Restart Control**: Enable/disable automatic restart on crash
- **Working Directory Configuration**: Specify custom working directory for processes
- **Interpreter Selection**: Choose custom interpreter (node, python, ruby, etc.)

## Requirements

- CyberPanel 2.5.5-dev or higher
- PM2 installed globally (`npm install -g pm2`)
- Node.js installed
- Python 3.6+
- Django (included with CyberPanel)

## Installation

1. **Download the plugin** from the CyberPanel Plugin Store or GitHub
2. **Upload via CyberPanel**:
   - Navigate to **Plugins** → **Installed Plugins**
   - Click **Upload Plugin**
   - Select the PM2 Manager plugin ZIP file
   - Click **Upload**
3. **Install the plugin**:
   - Click **Install** button next to PM2 Manager
   - Wait for installation to complete
4. **Access the plugin**:
   - Navigate to **Plugins** → **PM2 Manager**
   - Or visit `/plugins/pm2Manager/`

## Usage

### Dashboard

The main dashboard shows:
- Total number of PM2 applications
- Running vs stopped applications
- Average CPU usage
- Table of all applications with real-time metrics

### Adding a New Application

1. Click **Add App** button
2. Fill in the form:
   - **Application Name**: Unique name for your app (required)
   - **Script Path**: Full path to your script (required)
   - **Arguments**: Optional command-line arguments
   - **Instances**: Number of instances (for cluster mode)
   - **Execution Mode**: Fork or Cluster
   - **Memory Limit**: Optional memory limit (e.g., "500M", "1G") - app will restart if exceeded
   - **Auto Restart**: Enable or disable automatic restart on crash
   - **Working Directory (CWD)**: Optional custom working directory path
   - **Interpreter**: Optional interpreter (e.g., "node", "python", "ruby")
3. Click **Add App**

### Managing Applications

- **Start**: Start a stopped application
- **Stop**: Stop a running application
- **Restart**: Restart an application
- **Delete**: Remove an application from PM2
- **Details**: View detailed information and logs

### Node Details

Click **Details** on any application to view:
- Application information (PID, status, script path, etc.)
- Resource usage (CPU, memory, uptime)
- Real-time logs with auto-refresh
- Action buttons for process control

## API Endpoints

- `GET /plugins/pm2Manager/api/list/` - List all PM2 applications
- `GET /plugins/pm2Manager/api/info/<app_name>/` - Get app details
- `GET /plugins/pm2Manager/api/logs/<app_name>/` - Get app logs
- `GET /plugins/pm2Manager/api/monitor/` - Real-time monitoring data
- `POST /plugins/pm2Manager/api/start/<app_name>/` - Start app
- `POST /plugins/pm2Manager/api/stop/<app_name>/` - Stop app
- `POST /plugins/pm2Manager/api/restart/<app_name>/` - Restart app
- `POST /plugins/pm2Manager/api/delete/<app_name>/` - Delete app
- `POST /plugins/pm2Manager/api/add/` - Add new app

## Real-time Monitoring

The plugin uses WebSocket connections for real-time updates when available, with automatic fallback to HTTP polling every 2 seconds. This ensures you always have up-to-date information about your PM2 processes.

## Security

- All endpoints require admin authentication
- Input validation and sanitization
- Secure subprocess execution
- Error handling without exposing sensitive information

## Troubleshooting

### PM2 Not Found

If you see "PM2 is not installed" errors:
```bash
npm install -g pm2
```

### Applications Not Showing

- Ensure PM2 is running: `pm2 list`
- Check that applications are managed by PM2
- Verify file permissions

### WebSocket Not Working

The plugin automatically falls back to HTTP polling if WebSocket is unavailable. This is normal and doesn't affect functionality.

## Support

For issues and questions:
- Open an issue on GitHub: https://github.com/master3395/cyberpanel-plugins
- Check CyberPanel documentation
- Review PM2 documentation: https://pm2.keymetrics.io/

## License

MIT License

---

**Author:** Master3395  
**Last Updated:** 2026-01-27  
**Latest Version:** 1.1.0
