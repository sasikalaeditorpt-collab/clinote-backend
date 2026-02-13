import time
import os

AUDIT_STATE = {
    "status": "idle",          # idle | running | finished
    "started_at": None,
    "finished_at": None,
    "latest_report": None
}

AUDIT_DIR = r"D:\AuditEngine\Monthly"


def set_running():
    AUDIT_STATE["status"] = "running"
    AUDIT_STATE["started_at"] = time.time()
    AUDIT_STATE["finished_at"] = None


def set_finished(report_filename):
    AUDIT_STATE["status"] = "finished"
    AUDIT_STATE["finished_at"] = time.time()
    AUDIT_STATE["latest_report"] = report_filename


def get_state():
    return AUDIT_STATE