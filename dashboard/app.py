from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/group_stats')
def group_stats():
    stats_file = '/tmp/group_stats.json'
    if os.path.exists(stats_file):
        with open(stats_file) as f:
            stats = json.load(f)
    else:
        stats = {'faculty': 0, 'lab': 0, 'student': 0}
    # Convert bytes to Mbps (approx)
    for k in stats:
        stats[k] = round(stats[k] * 8 / 1_000_000, 2)
    return jsonify(stats)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
