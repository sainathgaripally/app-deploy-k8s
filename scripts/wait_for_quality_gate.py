#!/usr/bin/env python3
import os, time, sys, requests

SONAR_HOST_URL = os.getenv("SONAR_HOST_URL")
SONAR_TOKEN = os.getenv("SONAR_TOKEN")
REPORT_FILE = "target/sonar/report-task.txt"

if not SONAR_HOST_URL or not SONAR_TOKEN:
    print("❌ SONAR_HOST_URL or SONAR_TOKEN not set")
    sys.exit(1)

if not os.path.exists(REPORT_FILE):
    print(f"❌ Report file not found at {REPORT_FILE}")
    sys.exit(1)

# --- Read analysis ID from report-task.txt
analysis_id = None
with open(REPORT_FILE) as f:
    for line in f:
        if line.startswith("ceTaskId="):
            analysis_id = line.strip().split("=")[1]
            break

if not analysis_id:
    print("❌ Could not extract ceTaskId from report-task.txt")
    sys.exit(1)

print(f"🔎 Analysis ID: {analysis_id}")
print("⏳ Waiting for SonarQube analysis to finish...")

# --- Poll until Compute Engine completes
for attempt in range(1, 21):
    r = requests.get(f"{SONAR_HOST_URL}/api/ce/task?id={analysis_id}",
                     auth=(SONAR_TOKEN, ""))
    status = r.json().get("task", {}).get("status")
    print(f"Attempt {attempt}: {status}")
    if status == "SUCCESS":
        break
    if status == "FAILED":
        print("❌ SonarQube background task failed.")
        sys.exit(1)
    time.sleep(5)
else:
    print("❌ Timeout waiting for SonarQube to finish.")
    sys.exit(1)

# --- Fetch Quality Gate result
r = requests.get(f"{SONAR_HOST_URL}/api/qualitygates/project_status?analysisId={analysis_id}",
                 auth=(SONAR_TOKEN, ""))
gate_status = r.json().get("projectStatus", {}).get("status")

print(f"🏁 Quality Gate: {gate_status}")
if gate_status != "OK":
    print("❌ Quality Gate failed.")
    sys.exit(1)

print("✅ Quality Gate passed.")
sys.exit(0)
