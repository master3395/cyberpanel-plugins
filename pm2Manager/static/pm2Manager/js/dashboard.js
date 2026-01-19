// PM2 Manager Dashboard JavaScript
// Real-time monitoring with WebSocket support

let apps = [];
let monitorInterval = null;
let isWebSocketSupported = false;
let ws = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadApps();
    startRealTimeMonitoring();
    document.getElementById('addAppForm').addEventListener('submit', handleAddApp);
});

// Load PM2 apps list
function loadApps() {
    fetch('/plugins/pm2Manager/api/list/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                apps = data.apps;
                updateStats(data.apps);
                renderAppsTable(data.apps);
            } else {
                showError(data.error || 'Failed to load PM2 apps');
            }
        })
        .catch(error => {
            console.error('Error loading apps:', error);
            showError('Error loading PM2 applications');
        });
}

// Start real-time monitoring
function startRealTimeMonitoring() {
    if (window.WebSocket) {
        try {
            connectWebSocket();
        } catch (e) {
            console.log('WebSocket not available, using polling');
            startPolling();
        }
    } else {
        startPolling();
    }
}

// Connect WebSocket for real-time updates
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/plugins/pm2Manager/api/monitor/`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = function() {
        console.log('WebSocket connected');
        isWebSocketSupported = true;
    };
    
    ws.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.success) {
                updateRealTimeData(data.data);
            }
        } catch (e) {
            console.error('Error parsing WebSocket message:', e);
        }
    };
    
    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
        startPolling();
    };
    
    ws.onclose = function() {
        console.log('WebSocket closed, reconnecting...');
        setTimeout(connectWebSocket, 5000);
    };
}

// Start polling as fallback
function startPolling() {
    if (monitorInterval) clearInterval(monitorInterval);
    
    monitorInterval = setInterval(() => {
        fetch('/plugins/pm2Manager/api/monitor/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateRealTimeData(data.data);
                }
            })
            .catch(error => console.error('Polling error:', error));
    }, 2000);
}

// Update real-time data
function updateRealTimeData(monitorData) {
    monitorData.forEach(monitor => {
        const app = apps.find(a => a.name === monitor.name);
        if (app) {
            app.cpu = monitor.cpu;
            app.memory = monitor.memory;
            app.status = monitor.status;
            app.uptime = monitor.uptime;
            app.restarts = monitor.restarts;
        }
    });
    updateStats(apps);
    renderAppsTable(apps);
}

// Update statistics
function updateStats(appsList) {
    const total = appsList.length;
    const running = appsList.filter(a => a.status === 'online').length;
    const stopped = appsList.filter(a => a.status === 'stopped').length;
    const avgCpu = appsList.length > 0 
        ? (appsList.reduce((sum, a) => sum + (a.cpu || 0), 0) / appsList.length).toFixed(1)
        : 0;
    
    document.getElementById('totalApps').textContent = total;
    document.getElementById('runningApps').textContent = running;
    document.getElementById('stoppedApps').textContent = stopped;
    document.getElementById('avgCpu').textContent = avgCpu + '%';
}

// Render apps table
function renderAppsTable(appsList) {
    const tbody = document.getElementById('appsTableBody');
    
    if (appsList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state"><div class="empty-icon"><i class="fas fa-cube"></i></div><div>No PM2 applications found</div></td></tr>';
        return;
    }
    
    tbody.innerHTML = appsList.map(app => {
        const statusClass = app.status === 'online' ? 'status-online' : 
                           app.status === 'stopped' ? 'status-stopped' : 'status-restarting';
        const statusText = app.status === 'online' ? 'Running' : 
                          app.status === 'stopped' ? 'Stopped' : 'Restarting';
        
        const uptime = formatUptime(app.uptime);
        const cpuPercent = (app.cpu || 0).toFixed(1);
        const memoryMB = ((app.memory || 0) / 1024 / 1024).toFixed(2);
        
        const actionButtons = app.status === 'online' 
            ? `<button class="action-btn btn-stop" onclick="stopApp('${escapeHtml(app.name)}')"><i class="fas fa-stop"></i> Stop</button>
               <button class="action-btn btn-restart" onclick="restartApp('${escapeHtml(app.name)}')"><i class="fas fa-redo"></i> Restart</button>`
            : `<button class="action-btn btn-start" onclick="startApp('${escapeHtml(app.name)}')"><i class="fas fa-play"></i> Start</button>`;
        
        return `<tr>
            <td><strong>${escapeHtml(app.name)}</strong><br><small style="color: var(--text-secondary, #64748b);">PID: ${app.pid || 'N/A'}</small></td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td><div>${cpuPercent}%</div><div class="usage-bar"><div class="usage-fill usage-cpu" style="width: ${Math.min(cpuPercent, 100)}%"></div></div></td>
            <td><div>${memoryMB} MB</div><div class="usage-bar"><div class="usage-fill usage-memory" style="width: ${Math.min((app.memory || 0) / 1024 / 1024 / 100, 100)}%"></div></div></td>
            <td>${uptime}</td>
            <td>${app.restarts || 0}</td>
            <td>${actionButtons}
                <button class="action-btn btn-view" onclick="viewAppDetails('${escapeHtml(app.name)}')"><i class="fas fa-info-circle"></i> Details</button>
                <button class="action-btn btn-delete" onclick="deleteApp('${escapeHtml(app.name)}')"><i class="fas fa-trash"></i> Delete</button>
            </td>
        </tr>`;
    }).join('');
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
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function startApp(name) {
    if (!confirm(`Start ${name}?`)) return;
    fetch(`/plugins/pm2Manager/api/start/${encodeURIComponent(name)}/`, {
        method: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess(data.message || 'App started successfully');
            loadApps();
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
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess(data.message || 'App stopped successfully');
            loadApps();
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
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess(data.message || 'App restarted successfully');
            loadApps();
        } else {
            showError(data.error || 'Failed to restart app');
        }
    })
    .catch(error => {
        console.error('Error restarting app:', error);
        showError('Error restarting application');
    });
}

function deleteApp(name) {
    if (!confirm(`Delete ${name}? This action cannot be undone.`)) return;
    fetch(`/plugins/pm2Manager/api/delete/${encodeURIComponent(name)}/`, {
        method: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess(data.message || 'App deleted successfully');
            loadApps();
        } else {
            showError(data.error || 'Failed to delete app');
        }
    })
    .catch(error => {
        console.error('Error deleting app:', error);
        showError('Error deleting application');
    });
}

function viewAppDetails(name) {
    window.location.href = `/plugins/pm2Manager/node/${encodeURIComponent(name)}/`;
}

function refreshApps() {
    loadApps();
}

function showAddAppModal() {
    document.getElementById('addAppModal').style.display = 'flex';
}

function closeAddAppModal() {
    document.getElementById('addAppModal').style.display = 'none';
    document.getElementById('addAppForm').reset();
}

function handleAddApp(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
        name: formData.get('name'),
        script_path: formData.get('script_path'),
        args: formData.get('args') || '',
        instances: parseInt(formData.get('instances')) || 1,
        exec_mode: formData.get('exec_mode') || 'fork'
    };
    
    fetch('/plugins/pm2Manager/api/add/', {
        method: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess(result.message || 'App added successfully');
            closeAddAppModal();
            loadApps();
        } else {
            showError(result.error || 'Failed to add app');
        }
    })
    .catch(error => {
        console.error('Error adding app:', error);
        showError('Error adding application');
    });
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
    if (monitorInterval) clearInterval(monitorInterval);
    if (ws) ws.close();
});
