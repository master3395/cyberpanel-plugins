# Memcache Manager Plugin for CyberPanel

A free, comprehensive Memcache management plugin for CyberPanel with enhanced visualizations and support for both standard Memcached and LiteSpeed LSMCD.

## Features

### Service Management
- **Auto-Detection**: Automatically detects whether Memcached or LSMCD is installed
- **Service Control**: Start, Stop, Restart services with one click
- **Boot Options**: Enable/Disable service at system startup
- **Status Monitoring**: Real-time service status display

### Statistics & Visualization
- **Memory Usage Chart**: Doughnut chart showing used vs. free memory
- **Cache Hit Rate Chart**: Visual representation of hit/miss ratio
- **Operations Chart**: Bar chart showing GET, SET, DELETE command counts
- **Quick Stats Cards**: Connections, Items, Commands, Evictions, Uptime
- **Auto-Refresh**: Statistics refresh automatically every 30 seconds
- **Manual Refresh**: Click refresh button for immediate updates

### Cache Operations
- **Flush All**: Clear entire cache with confirmation dialog
- **Connection Test**: Automatic connection verification to memcache server

### Configuration Display
- Service type and name
- Host and port configuration
- Config file location
- Service-specific settings (memory limits, connections, etc.)

### Raw Stats Output
- View complete raw stats output from memcache server
- Useful for debugging and detailed analysis

## Requirements

### Server
- AlmaLinux 8.8, 9.6, or 10
- CyberPanel with OpenLiteSpeed or LiteSpeed Enterprise

### Memcache Service (one of)
- **Memcached**: Standard memcached service (`/usr/bin/memcached`)
- **LSMCD**: LiteSpeed Memcached (`/usr/local/lsmcd/bin/lsmcd`)

### Network
- Port 11211 must be accessible locally (default memcache port)
- No external dependencies - all communication is local

## Installation

### Via CyberPanel Plugin Manager
1. Go to **CyberPanel > Plugins > Plugin Manager**
2. Find "Memcache Manager" in the available plugins list
3. Click **Install**
4. The plugin will be automatically configured

### Manual Installation
1. Copy the `memcacheManager` folder to `/usr/local/CyberCP/`
2. Add to `INSTALLED_APPS` in `/usr/local/CyberCP/CyberCP/settings.py`:
   ```python
   INSTALLED_APPS = [
       # ... other apps ...
       'memcacheManager',
   ]
   ```
3. Add URL route to `/usr/local/CyberCP/CyberCP/urls.py`:
   ```python
   path('plugins/memcacheManager/', include('memcacheManager.urls')),
   ```
4. Restart lscpd:
   ```bash
   systemctl restart lscpd
   ```

## Usage

### Accessing the Plugin
1. Log into CyberPanel
2. Navigate to **Plugins > Memcache Manager**
3. The dashboard will display current status and statistics

### Service Control
- **Start**: Start the memcache service
- **Stop**: Stop the memcache service
- **Restart**: Restart the memcache service
- **Enable**: Enable service to start at boot
- **Disable**: Disable service from starting at boot

### Viewing Statistics
Statistics are displayed in real-time when the service is running:
- Memory usage percentage and actual bytes
- Cache hit rate percentage
- Command counts (GET, SET, DELETE)
- Current connections and items
- Eviction count
- Service uptime

### Flushing Cache
1. Click the **Flush All** button
2. Confirm the action in the dialog
3. All cache data will be cleared immediately

## API Endpoints

The plugin provides REST API endpoints for programmatic access:

### GET /plugins/memcacheManager/
Main dashboard page

### POST /plugins/memcacheManager/api/control/
Control service actions

**Request Body:**
```json
{
    "action": "start|stop|restart|enable|disable"
}
```

**Response:**
```json
{
    "success": true,
    "message": "MEMCACHED started successfully."
}
```

### GET /plugins/memcacheManager/api/stats/
Get current statistics

**Response:**
```json
{
    "success": true,
    "stats": {
        "bytes": 1234567,
        "limit_maxbytes": 67108864,
        "hit_rate": 95.5,
        "miss_rate": 4.5,
        "curr_connections": 10,
        "curr_items": 500,
        "cmd_get": 10000,
        "cmd_set": 5000,
        "evictions": 0,
        "uptime": 86400,
        "uptime_formatted": "1d 0h 0m"
    }
}
```

### POST /plugins/memcacheManager/api/flush/
Flush all cache data

**Response:**
```json
{
    "success": true,
    "message": "Cache flushed successfully."
}
```

### GET /plugins/memcacheManager/api/config/
Get configuration details

**Response:**
```json
{
    "success": true,
    "config": {
        "service_type": "memcached",
        "service_name": "memcached",
        "host": "127.0.0.1",
        "port": 11211,
        "config_file": "/etc/sysconfig/memcached",
        "settings": {
            "cache_size_mb": "64",
            "max_connections": "1024"
        }
    }
}
```

## Troubleshooting

### Service Not Detected
- Ensure Memcached or LSMCD is installed
- Check marker files exist: `/home/cyberpanel/memcached` or `/home/cyberpanel/lsmcd`
- Verify binary exists: `/usr/bin/memcached` or `/usr/local/lsmcd/bin/lsmcd`

### Cannot Connect to Service
- Verify service is running: `systemctl status memcached` or `systemctl status lsmcd`
- Check port 11211 is listening: `netstat -tlnp | grep 11211`
- Test connection: `echo "stats" | nc localhost 11211`

### Stats Not Loading
- Ensure `nc` (netcat) is installed: `yum install nc` or `dnf install nc`
- Check firewall allows local connections on port 11211
- Verify memcache is responding: `echo "stats" | nc 127.0.0.1 11211`

### Permission Issues
- Ensure CyberPanel user has permission to run systemctl commands
- Check sudoers configuration for lscpd service

## Configuration Files

### Memcached
- RedHat/CentOS/AlmaLinux: `/etc/sysconfig/memcached`
- Debian/Ubuntu: `/etc/memcached.conf`

### LSMCD
- Configuration: `/usr/local/lsmcd/conf/node.conf`

## Security Considerations

- The plugin requires CyberPanel admin authentication
- All API endpoints are protected with login verification
- Service control operations use systemctl (requires appropriate permissions)
- Cache flush requires user confirmation
- No sensitive data is exposed in error messages

## Compatibility

| Component | Supported Versions |
|-----------|-------------------|
| CyberPanel | 2.0+ |
| AlmaLinux | 8.8, 9.6, 10 |
| OpenLiteSpeed | All versions |
| LiteSpeed Enterprise | All versions |
| Memcached | 1.5+ |
| LSMCD | All versions |

## License

This is a free plugin distributed under the MIT License.

## Author

**master3395**

## Support

For issues and feature requests, please use the CyberPanel community forums or GitHub issues.

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.
