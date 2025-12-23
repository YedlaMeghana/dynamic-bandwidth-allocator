from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime

app = Flask(__name__)

# Configuration files
STATS_FILE = '/tmp/group_stats.json'
EXAM_SCHEDULE_FILE = '/tmp/exam_schedule.json'
BANDWIDTH_LOG_FILE = '/tmp/bandwidth.log'

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

@app.route('/api/group_stats')
def group_stats():
    """
    API endpoint: Get current bandwidth usage per group.
    Returns bandwidth in Mbps.
    """
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE) as f:
                stats = json.load(f)
        except:
            stats = {'faculty': 0, 'lab': 0, 'student': 0}
    else:
        stats = {'faculty': 0, 'lab': 0, 'student': 0}
    
    # Stats are already in Mbps from enhanced controller
    # Just ensure they're rounded
    for k in stats:
        stats[k] = round(stats[k], 2)
    
    return jsonify(stats)

@app.route('/api/exam_mode', methods=['GET', 'POST'])
def exam_mode():
    """
    API endpoint: Get or set exam mode status.
    GET: Returns current exam mode status
    POST: Activate/deactivate exam mode
    """
    if request.method == 'GET':
        # Check if exam mode is active
        if os.path.exists(EXAM_SCHEDULE_FILE):
            try:
                with open(EXAM_SCHEDULE_FILE) as f:
                    schedules = json.load(f)
                    active = any(s.get('active', False) for s in schedules)
                    return jsonify({'active': active, 'schedules': schedules})
            except:
                return jsonify({'active': False, 'schedules': []})
        return jsonify({'active': False, 'schedules': []})
    
    elif request.method == 'POST':
        # Toggle exam mode
        data = request.json
        active = data.get('active', False)
        
        # Write to control file that controller can read
        control_file = '/tmp/exam_mode_control.json'
        with open(control_file, 'w') as f:
            json.dump({'active': active, 'timestamp': datetime.now().isoformat()}, f)
        
        return jsonify({'status': 'success', 'active': active})

@app.route('/api/schedule_exam', methods=['POST'])
def schedule_exam():
    """
    API endpoint: Schedule an exam mode session.
    Expects JSON: {"name": "Exam Name", "start_time": "HH:MM", "end_time": "HH:MM"}
    """
    data = request.json
    name = data.get('name', 'Exam')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    if not start_time or not end_time:
        return jsonify({'error': 'Missing start_time or end_time'}), 400
    
    # Validate time format
    try:
        datetime.strptime(start_time, "%H:%M")
        datetime.strptime(end_time, "%H:%M")
    except ValueError:
        return jsonify({'error': 'Invalid time format. Use HH:MM'}), 400
    
    # Load existing schedules
    schedules = []
    if os.path.exists(EXAM_SCHEDULE_FILE):
        try:
            with open(EXAM_SCHEDULE_FILE) as f:
                schedules = json.load(f)
        except:
            schedules = []
    
    # Add new schedule
    new_schedule = {
        'name': name,
        'start_time': start_time,
        'end_time': end_time,
        'active': False,
        'created': datetime.now().isoformat()
    }
    schedules.append(new_schedule)
    
    # Save schedules
    with open(EXAM_SCHEDULE_FILE, 'w') as f:
        json.dump(schedules, f)
    
    return jsonify({'status': 'scheduled', 'schedule': new_schedule})

@app.route('/api/clear_schedules', methods=['POST'])
def clear_schedules():
    """API endpoint: Clear all exam schedules."""
    if os.path.exists(EXAM_SCHEDULE_FILE):
        os.remove(EXAM_SCHEDULE_FILE)
    return jsonify({'status': 'cleared'})

@app.route('/api/update_faculty_ips', methods=['POST'])
def update_faculty_ips():
    """
    API endpoint: Update faculty IP addresses.
    Expects JSON: {"ips": ["10.0.1.10", "10.0.1.11", ...]}
    """
    data = request.json
    ips = data.get('ips', [])
    
    # Validate IPs
    if not isinstance(ips, list) or len(ips) == 0:
        return jsonify({'error': 'Invalid IPs format'}), 400
    
    # Write to config file that controller can read
    config_file = '/tmp/faculty_ips.json'
    with open(config_file, 'w') as f:
        json.dump({'ips': ips, 'updated': datetime.now().isoformat()}, f)
    
    return jsonify({'status': 'updated', 'ips': ips})

@app.route('/api/bandwidth_history')
def bandwidth_history():
    """
    API endpoint: Get historical bandwidth data.
    Returns last 100 data points from log file.
    """
    history = []
    if os.path.exists(BANDWIDTH_LOG_FILE):
        try:
            with open(BANDWIDTH_LOG_FILE) as f:
                lines = f.readlines()
                # Get last 100 lines
                for line in lines[-100:]:
                    try:
                        entry = json.loads(line.strip())
                        history.append(entry)
                    except:
                        pass
        except:
            pass
    
    return jsonify(history)

@app.route('/api/system_status')
def system_status():
    """
    API endpoint: Get overall system status.
    """
    status = {
        'controller_active': os.path.exists(STATS_FILE),
        'last_update': None,
        'exam_mode': False
    }
    
    if os.path.exists(STATS_FILE):
        stat_info = os.stat(STATS_FILE)
        status['last_update'] = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
    
    if os.path.exists(EXAM_SCHEDULE_FILE):
        try:
            with open(EXAM_SCHEDULE_FILE) as f:
                schedules = json.load(f)
                status['exam_mode'] = any(s.get('active', False) for s in schedules)
        except:
            pass
    
    return jsonify(status)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
