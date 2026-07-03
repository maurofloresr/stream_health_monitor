import threading
from datetime import datetime
from dataclasses import asdict
from flask import Flask, jsonify, render_template, Response

from models import Report
from client import monitor_stream

app = Flask(__name__)
latest_reports:list[Report] = [] # shared state: the monitor thread writes, Flask reads


def run_monitor() -> None:
    # Runs in a background thread, updating latest_reports each cycle.
    global latest_reports
    for reports in monitor_stream():
        latest_reports = reports
        
        
@app.route("/")
def index() -> str:
    return render_template("index.html")

@app.route("/status")
def status() -> Response:
    return jsonify({
        "generated_at": datetime.now().isoformat(),
        "services": [asdict(r) for r in latest_reports],
    })  


thread = threading.Thread(target=run_monitor, daemon=True)
thread.start()

if __name__ == "__main__":
    app.run()