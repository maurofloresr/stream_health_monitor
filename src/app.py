import threading
from datetime import datetime
from dataclasses import asdict
from flask import Flask, jsonify, render_template, Response

from models import Report
from client import monitor_stream

app = Flask(__name__)

# Shared state: the monitor thread writes, Flask reads.
latest_reports: list[Report] = []
_monitor_started = False


def run_monitor() -> None:
    # Runs in a background thread, refreshing latest_reports each cycle.
    global latest_reports
    for reports in monitor_stream():
        latest_reports = reports


def start_monitor_once() -> None:
    # Launch the monitor exactly once, inside the worker process that serves
    # requests, so the thread and Flask share the same latest_reports.
    global _monitor_started
    if not _monitor_started:
        _monitor_started = True
        thread = threading.Thread(target=run_monitor, daemon=True)
        thread.start()


@app.before_request
def _ensure_monitor() -> None:
    start_monitor_once()


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/status")
def status() -> Response:
    return jsonify({
        "generated_at": datetime.now().isoformat(),
        "services": [asdict(r) for r in latest_reports],
    })


if __name__ == "__main__":
    app.run()