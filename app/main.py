from flask import Flask, jsonify, render_template_string, request
import psutil
import platform
import datetime
import os
import subprocess
import json
from threading import Lock

app = Flask(__name__)

# Store deployment info and metrics
deployment_info = {
    "version": "v6.0",
    "deployed_at": datetime.datetime.now().isoformat(),
    "environment": os.getenv("ENVIRONMENT", "development"),
    "git_commit": os.getenv("GIT_COMMIT", "unknown"),
    "build_number": os.getenv("BUILD_NUMBER", "local")
}

# Thread-safe counter for demo purposes
request_counter = {"count": 0}
counter_lock = Lock()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flask CI/CD Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .status-badge {
            display: inline-block;
            padding: 8px 16px;
            background: #4CAF50;
            color: white;
            border-radius: 20px;
            font-weight: bold;
            margin: 10px 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .card h3 {
            color: #5a67d8;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }
        .card h3::before {
            content: "🔧";
            margin-right: 10px;
            font-size: 1.2em;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 10px;
            background: #f8f9ff;
            border-radius: 8px;
            border-left: 4px solid #5a67d8;
        }
        .metric-value {
            font-weight: bold;
            color: #5a67d8;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #45a049);
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        .interactive-section {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .button-group {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 20px 0;
        }
        .btn {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        .log-container {
            background: #1a202c;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 10px;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            margin: 10px 0;
        }
        .deployment-info h3::before { content: "🚀"; }
        .system-info h3::before { content: "💻"; }
        .health-check h3::before { content: "❤️"; }
        .auto-refresh {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .updating { animation: pulse 1s infinite; }
        .footer {
            text-align: center;
            color: white;
            padding: 20px;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="auto-refresh">
        <button class="btn" onclick="toggleAutoRefresh()" id="refreshBtn">🔄 Auto Refresh: OFF</button>
    </div>

    <div class="container">
        <div class="header">
            <h1>🐍 Flask CI/CD Dashboard</h1>
            <p>Real-time Application Monitoring & DevOps Showcase</p>
            <div class="status-badge">✅ HEALTHY</div>
            <div class="status-badge">🔄 VERSION: {{ deployment_info.version }}</div>
            <div class="status-badge">🌍 ENV: {{ deployment_info.environment.upper() }}</div>
        </div>

        <div class="dashboard">
            <div class="card deployment-info">
                <h3>Deployment Information</h3>
                <div class="metric">
                    <span>Version:</span>
                    <span class="metric-value">{{ deployment_info.version }}</span>
                </div>
                <div class="metric">
                    <span>Deployed:</span>
                    <span class="metric-value">{{ deployment_info.deployed_at[:19] }}</span>
                </div>
                <div class="metric">
                    <span>Environment:</span>
                    <span class="metric-value">{{ deployment_info.environment }}</span>
                </div>
                <div class="metric">
                    <span>Build:</span>
                    <span class="metric-value">#{{ deployment_info.build_number }}</span>
                </div>
                <div class="metric">
                    <span>Git Commit:</span>
                    <span class="metric-value">{{ deployment_info.git_commit[:8] }}</span>
                </div>
            </div>

            <div class="card system-info">
                <h3>System Metrics</h3>
                <div class="metric">
                    <span>CPU Usage:</span>
                    <span class="metric-value" id="cpu-usage">--</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="cpu-bar" style="width: 0%"></div>
                </div>
                
                <div class="metric">
                    <span>Memory Usage:</span>
                    <span class="metric-value" id="memory-usage">--</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="memory-bar" style="width: 0%"></div>
                </div>
                
                <div class="metric">
                    <span>Request Count:</span>
                    <span class="metric-value" id="request-count">{{ request_counter.count }}</span>
                </div>
                
                <div class="metric">
                    <span>Uptime:</span>
                    <span class="metric-value" id="uptime">--</span>
                </div>
            </div>

            <div class="card health-check">
                <h3>Health Monitoring</h3>
                <div class="metric">
                    <span>Status:</span>
                    <span class="metric-value" style="color: #4CAF50;" id="health-status">HEALTHY</span>
                </div>
                <div class="metric">
                    <span>Response Time:</span>
                    <span class="metric-value" id="response-time">-- ms</span>
                </div>
                <div class="metric">
                    <span>Last Check:</span>
                    <span class="metric-value" id="last-check">--</span>
                </div>
                <div class="log-container" id="health-logs">
                    > System initialized successfully<br>
                    > All health checks passed<br>
                    > Monitoring active<br>
                </div>
            </div>
        </div>

        <div class="interactive-section">
            <h3 style="color: #5a67d8; margin-bottom: 20px;">🎮 Interactive DevOps Tools</h3>
            
            <div class="button-group">
                <button class="btn" onclick="simulateLoad()">🔥 Simulate Load</button>
                <button class="btn" onclick="runHealthCheck()">🏥 Health Check</button>
                <button class="btn" onclick="clearLogs()">🧹 Clear Logs</button>
                <button class="btn" onclick="showDeploymentHistory()">📋 Deploy History</button>
                <button class="btn" onclick="toggleFeatureFlag()">🎛️ Feature Flag</button>
                <button class="btn" onclick="generateReport()">📊 Generate Report</button>
            </div>

            <div class="log-container" id="activity-logs">
                > Welcome to Flask CI/CD Interactive Dashboard<br>
                > Click buttons above to simulate DevOps operations<br>
                > All operations are logged here in real-time<br>
            </div>
        </div>

        <div class="footer">
            <p>🛠️ Built for DevOps Excellence | Last Updated: <span id="last-updated">--</span></p>
        </div>
    </div>

    <script>
        let autoRefresh = false;
        let refreshInterval;

        // Update metrics on page load
        updateMetrics();
        updateTimestamp();

        function updateMetrics() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('cpu-usage').textContent = data.cpu_percent + '%';
                    document.getElementById('cpu-bar').style.width = data.cpu_percent + '%';
                    
                    document.getElementById('memory-usage').textContent = data.memory_percent + '%';
                    document.getElementById('memory-bar').style.width = data.memory_percent + '%';
                    
                    document.getElementById('request-count').textContent = data.request_count;
                    document.getElementById('uptime').textContent = data.uptime;
                    document.getElementById('response-time').textContent = data.response_time + ' ms';
                    
                    updateTimestamp();
                })
                .catch(err => console.error('Error fetching metrics:', err));
        }

        function toggleAutoRefresh() {
            autoRefresh = !autoRefresh;
            const btn = document.getElementById('refreshBtn');
            
            if (autoRefresh) {
                btn.textContent = '🔄 Auto Refresh: ON';
                btn.style.background = 'linear-gradient(135deg, #4CAF50, #45a049)';
                refreshInterval = setInterval(updateMetrics, 3000);
            } else {
                btn.textContent = '🔄 Auto Refresh: OFF';
                btn.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
                clearInterval(refreshInterval);
            }
        }

        function addLog(message, container = 'activity-logs') {
            const logContainer = document.getElementById(container);
            const timestamp = new Date().toLocaleTimeString();
            logContainer.innerHTML += `> [${timestamp}] ${message}<br>`;
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        function simulateLoad() {
            addLog('🔥 Simulating high load on system...');
            fetch('/api/simulate-load', { method: 'POST' })
                .then(() => {
                    addLog('✅ Load simulation completed');
                    updateMetrics();
                });
        }

        function runHealthCheck() {
            addLog('🏥 Running comprehensive health check...');
            fetch('/api/health-detailed')
                .then(response => response.json())
                .then(data => {
                    addLog(`✅ Health Check: ${data.status} (${data.checks_passed}/${data.total_checks} passed)`);
                    addLog('📊 Database: OK | API: OK | Services: OK', 'health-logs');
                    document.getElementById('last-check').textContent = new Date().toLocaleTimeString();
                });
        }

        function clearLogs() {
            document.getElementById('activity-logs').innerHTML = '> Logs cleared<br>';
            addLog('🧹 Activity logs cleared');
        }

        function showDeploymentHistory() {
            addLog('📋 Fetching deployment history...');
            fetch('/api/deployment-history')
                .then(response => response.json())
                .then(data => {
                    data.history.forEach(deploy => {
                        addLog(`📦 ${deploy.version} - ${deploy.date} (${deploy.status})`);
                    });
                });
        }

        function toggleFeatureFlag() {
            addLog('🎛️ Toggling feature flag...');
            fetch('/api/toggle-feature', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    addLog(`🎛️ Feature flag "${data.feature}" is now ${data.enabled ? 'ENABLED' : 'DISABLED'}`);
                });
        }

        function generateReport() {
            addLog('📊 Generating system report...');
            setTimeout(() => {
                addLog('📋 System Report Generated:');
                addLog('  - Uptime: 99.9% | Avg Response: 45ms');
                addLog('  - Total Requests: 1,247 | Errors: 0');
                addLog('  - Memory Usage: Optimal | CPU: Normal');
                addLog('📧 Report sent to DevOps team');
            }, 1500);
        }

        function updateTimestamp() {
            document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
        }

        // Auto-update timestamp every minute
        setInterval(updateTimestamp, 60000);
    </script>
</body>
</html>
"""

@app.route("/")
def dashboard():
    with counter_lock:
        request_counter["count"] += 1
    return render_template_string(HTML_TEMPLATE, 
                                deployment_info=deployment_info, 
                                request_counter=request_counter)

@app.route('/health')
def health():
    return jsonify({"status": "OK", "timestamp": datetime.datetime.now().isoformat()}), 200

@app.route('/api/metrics')
def metrics():
    """Real-time system metrics API"""
    with counter_lock:
        request_counter["count"] += 1
    
    try:
        cpu_percent = round(psutil.cpu_percent(interval=0.1), 1)
        memory = psutil.virtual_memory()
        memory_percent = round(memory.percent, 1)
        
        # Calculate uptime (mock calculation)
        uptime_seconds = (datetime.datetime.now() - datetime.datetime.fromisoformat(deployment_info["deployed_at"])).total_seconds()
        uptime = f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m"
        
        # Mock response time
        response_time = 45 + (cpu_percent / 10)  # Simulate response time based on CPU
        
        return jsonify({
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "request_count": request_counter["count"],
            "uptime": uptime,
            "response_time": round(response_time, 1),
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health-detailed')
def health_detailed():
    """Detailed health check API"""
    checks = [
        {"name": "Database", "status": "OK"},
        {"name": "Redis Cache", "status": "OK"},
        {"name": "External API", "status": "OK"},
        {"name": "Disk Space", "status": "OK"},
        {"name": "Memory", "status": "OK"}
    ]
    
    passed = len([c for c in checks if c["status"] == "OK"])
    
    return jsonify({
        "status": "HEALTHY" if passed == len(checks) else "DEGRADED",
        "checks": checks,
        "checks_passed": passed,
        "total_checks": len(checks),
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/api/simulate-load', methods=['POST'])
def simulate_load():
    """Simulate system load for demo purposes"""
    import time
    import random
    
    # Simulate some CPU intensive work
    start_time = time.time()
    for _ in range(100000):
        _ = random.random() ** 2
    
    duration = round((time.time() - start_time) * 1000, 2)
    
    return jsonify({
        "message": "Load simulation completed",
        "duration_ms": duration,
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/api/deployment-history')
def deployment_history():
    """Mock deployment history"""
    history = [
        {"version": "v6.0", "date": "2024-01-15 14:30", "status": "SUCCESS", "commit": "abc123"},
        {"version": "v5.2", "date": "2024-01-10 09:15", "status": "SUCCESS", "commit": "def456"},
        {"version": "v5.1", "date": "2024-01-08 16:45", "status": "ROLLBACK", "commit": "ghi789"},
        {"version": "v5.0", "date": "2024-01-05 11:20", "status": "SUCCESS", "commit": "jkl012"}
    ]
    
    return jsonify({"history": history})

@app.route('/api/toggle-feature', methods=['POST'])
def toggle_feature():
    """Toggle feature flag demo"""
    import random
    features = ["dark_mode", "new_dashboard", "advanced_metrics", "beta_features"]
    feature = random.choice(features)
    enabled = random.choice([True, False])
    
    return jsonify({
        "feature": feature,
        "enabled": enabled,
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/api/system-info')
def system_info():
    """System information API"""
    return jsonify({
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
        "hostname": platform.node(),
        "deployment_info": deployment_info
    })

if __name__ == "__main__":
    print("🚀 Starting Flask CI/CD Dashboard...")
    print(f"📊 Dashboard will be available at: http://localhost:5000")
    print(f"🔧 Version: {deployment_info['version']}")
    print(f"🌍 Environment: {deployment_info['environment']}")
    app.run(host="0.0.0.0", port=5000, debug=False)