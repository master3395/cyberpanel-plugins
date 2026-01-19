// PM2 Node Detail JavaScript

let refreshInterval = null;

document.addEventListener('DOMContentLoaded', function() {
    loadAppInfo();
    loadLogs();
    startAutoRefresh();
});

function loadAppInfo() {
    fetch(`/plugins/pm2Manager/api/info/${encodeURIComponent(appName)}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderAppInfo(data.info);
                updateActionButtons(data.info);
            } else {
                showError(data.error || 'Failed to load app information');
            }
        })
        .catch(error => {
            console.error('Error loading app info:', error);
            showError('Error loading application information');
        });
}

function renderAppInfo(info) {
    // Application Information
    const appInfoHtml = `
        <div class="info-row">
            <span class="info-label">{% trans "Status" %}</span>
            <span class="info-value" id="appStatus">${getStatusBadge(info.status || 'unknown')}</span>
        </div>
        <div class="info-row">
            <span class="info-label">{% trans "PID" %}</span>
            <span class="info-value">${info.pid || 'N/A'}</span>
        </div>
        <div class="info-row">
            <span class="info-label">{% trans "PM ID" %}</span>
            <span class="info-value">${info.pm_id || 'N/A'}</span>
        </div>
        <div class="info-row">
            <span class="info-label">{% trans "Script Path" %}</span>
            <span class="info-value" style="font-size: 12px; word-break: break-all;">${escapeHtml(info.script_path || 'N/A')}</span>
        </div>
        <div class="info-row">
            <span class="info-label">{% trans "Mode" %}</span>
            <span class="info-value">${info.mode || 'fork'}</span>
        </div>
        <div class="info-row">
            <span class="info-label">{% trans "Instances" %}</span>
            <span class="info-value">${info.instances || 1}</span>
        </div>
        <div class="info-row">
            <span class="info-label">{% trans "Restarts" %}</span>
            <span class="info-value">${info.restarts || 0}</span>
        </div>
    `;
    
    document.getElementById('appInfo').innerHTML = appInfoHtml;
    
    // Resource Usage
    const cpu = (info.cpu || 0).toFixed(1);
    const memory = ((info.memory || 0) / 1024 / 1024).toFixed(2);
    const uptime = formatUptime(info.uptime);
    
    const resourceHtml = `
        <div class="info-row">
            <span class="info-label">{% trans "CPU Usage" %}</span>
            <span class="info-value">${cpu}%</span>
        </div>
        <div class="info-row">
            <span class="info-label">{% trans "Memory Usage" %}</span>
            <span class="info-value">${memory} MB</span>
        </div>
        <div class="info-row">
            <span class="info-label">{% trans "Uptime" %}</span>
            <span class="info-value">${uptime}</span>
        </div>
    `;
    
    document.getElementById('resourceUsage').innerHTML = resourceHtml;
}

function updateActionButtons(info) {
    const status = info.status || 'unknown';
    const btnStart = document.getElementById('btnStart');
    const btnStop = document.getElementById('btnStop');
    const btnRestart = document.getElementById('btnRestart');
    
    if (status === 'online') {
        btnStart.style.display = 'none';
        btnStop.style.display = 'inline-block';
        btnRestart.style.display = 'inline-block';
    } else {
        btnStart.style.display = 'inline-block';
        btnStop.style.display = 'none';
        btnRestart.style.display = 'none';
    }
}

function loadLogs() {
    fetch(`/plugins/pm2Manager/api/logs/${encodeURIComponent(appName)}/?lines=200`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderLogs(data.logs);
            } else {
                document.getElementById('logsContainer').innerHTML = 
                    `<div class="log-line" style="color: #ef4444;">Error: ${escapeHtml(data.error || 'Failed to load logs')}</div>`;
            }
        })
        .catch(error => {
            console.error('Error loading logs:', error);
            document.getElementById('logsContainer').innerHTML = 
                '<div class="log-line" style="color: #ef4444;">Error loading logs</div>';
        });
}

function renderLogs(logs) {
    const container = document.getElementById('logsContainer');
    if (!logs || logs.length === 0) {
        container.innerHTML = '<div class="log-line">No logs available</div>';
        return;
    }
    
    container.innerHTML = logs.map(log => {
        const logText = escapeHtml(log);
        let color = '#d4d4d4';
        if (logText.includes('ERROR') || logText.includes('error')) {
            color = '#f48771';
        } else if (logText.includes('WARN') || logText.includes('warning')) {
            color = '#dcdcaa';
        }
        
        return `<div class="log-line" style="color: ${color};">${logText}</div>`;
    }).join('');
    
    // Auto-scroll to bottom
    container.scrollTop = container.scrollHeight;
}

function refreshLogs() {
    loadLogs();
}

function startAutoRefresh() {
    // Refresh info and logs every 3 seconds
    refreshInterval = setInterval(() => {
        loadAppInfo();
        loadLogs();
    }, 3000);
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

function startApp(name) {
    if (!confirm(`Start ${name}?`)) return;
    
    fetch(`/plugins/pm2Manager/api/start/${encodeURIComponent(name)}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess(data.message || 'App started successfully');
            loadAppInfo();
        } else {
            showError(data.error || 'Failed to start app');
        }
    })
    .catch(error => {
        console.error('Error starting app:', error);
        showError('Error starting application');
    });
}

function stopApp(name) {
    if (!confirm(`Stop ${name}?`)) return;
    
    fetch(`/plugins/pm2Manager/api/stop/${encodeURIComponent(name)}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess(data.message || 'App stopped successfully');
            loadAppInfo();
        } else {
            showError(data.error || 'Failed to stop app');
        }
    })
    .catch(error => {
        console.error('Error stopping app:', error);
        showError('Error stopping application');
    });
}

function restartApp(name) {
    if (!confirm(`Restart ${name}?`)) return;
    
    fetch(`/plugins/pm2Manager/api/restart/${encodeURIComponent(name)}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess(data.message || 'App restarted successfully');
            loadAppInfo();
        } else {
            showError(data.error || 'Failed to restart app');
        }
    })
    .catch(error => {
        console.error('Error restarting app:', error);
        showError('Error restarting application');
    });
}

function getStatusBadge(status) {
    const badges = {
        'online': '<span class="status-badge status-online">Running</span>',
        'stopped': '<span class="status-badge status-stopped">Stopped</span>',
        'restarting': '<span class="status-badge status-restarting">Restarting</span>'
    };
    return badges[status] || `<span class="status-badge">${status}</span>`;
}

function formatUptime(seconds) {
    if (!seconds || seconds < 0) return '0s';
    
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showSuccess(message) {
    alert(message);
}

function showError(message) {
    alert('Error: ' + message);
}

window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});
