#!/usr/bin/env python3
"""
wait_for_quality_gate.py
-----------------------------------
Waits for SonarQube analysis to complete, checks the Quality Gate,
and exports results back to GitHub Actions.
"""

import os
import sys
import time
import requests

SONAR_HOST_URL = os.getenv("SONAR_HOST_URL")
SONAR_TOKEN = os.getenv("SONAR_TOKEN")
REPORT_FILE = "target/sonar/report-task.txt"
GITHUB_OUTPUT = os.getenv("GITHUB_OUTPUT")

def fail(message):
    print(f"❌ {message}")
    if GITHUB_OUTPUT:
        with open(GITHUB_OUTPUT, "a") as f:
            f.write(f"gate_status=ERROR\n")
            f.write(f"gate_message={message}\n")
    sys.exit(1)

def write_output(status, message):
    if GITHUB_OUTPUT:
        with open(GITHUB_OUTPUT, "a") as f:
            f.write(f"gate_status={status}\n")
            f.write(f"gate_message={message}\n")

def main():
    if not SONAR_HOST_URL or not SONAR_TOKEN:
        fail("Environment variables SONAR_HOST_URL or SONAR_TOKEN not set")

    if not os.path.exists(REPORT_FILE):
        fail(f"Report file not found at {REPORT_FILE}")

    # --- Extract ceTaskId and projectKey from report-task.txt
    analysis_id, project_key = None, None
    with open(REPORT_FILE, "r") as f:
        for line in f:
            if line.startswith("ceTaskId="):
                analysis_id = line.strip().split("=")[1]
            elif line.startswith("projectKey="):
                project_key = line.strip().split("=")[1]

    if not analysis_id:
        fail("Could not extract ceTaskId from report-task.txt")
    if not project_key:
        fail("Could not extract projectKey from report-task.txt")

    print(f"🔎 Analysis ID: {analysis_id}")
    print(f"📦 Project Key: {project_key}")
    print("⏳ Waiting for SonarQube analysis to finish...")

    # --- Poll until Compute Engine finishes
    for attempt in range(1, 21):
        try:
            resp = requests.get(
                f"{SONAR_HOST_URL}/api/ce/task?id={analysis_id}",
                auth=(SONAR_TOKEN, "")
            )
            task = resp.json().get("task", {})
            status = task.get("status")
            print(f"Attempt {attempt}: {status}")
        except Exception as e:
            print(f"⚠️ Error contacting SonarQube: {e}")
            status = None

        if status == "SUCCESS":
            print("✅ Analysis processing completed. Waiting 5s for Quality Gate status...")
            time.sleep(5)
            break
        elif status == "FAILED":
            fail("SonarQube background task failed.")
        else:
            time.sleep(5)
    else:
        fail("Timeout waiting for SonarQube to finish.")

    # --- Fetch Quality Gate result
    print("📊 Fetching Quality Gate status...")
    try:
        resp = requests.get(
            f"{SONAR_HOST_URL}/api/qualitygates/project_status?projectKey={project_key}",
            auth=(SONAR_TOKEN, "")
        )
        data = resp.json()
        gate_status = data.get("projectStatus", {}).get("status")
    except Exception as e:
        fail(f"Error fetching Quality Gate status: {e}")

    print(f"🏁 Quality Gate: {gate_status}")

    if not gate_status:
        fail("Quality Gate status is None. SonarQube may still be processing.")

    if gate_status != "OK":
        print("❌ Quality Gate failed.")
        write_output("ERROR", "❌ Quality Gate failed. Check SonarQube dashboard for details.")
        sys.exit(1)

    print("✅ Quality Gate passed successfully.")
    write_output("OK", "✅ Quality Gate passed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
