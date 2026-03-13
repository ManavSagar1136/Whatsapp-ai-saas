import httpx
import json
import time
from datetime import datetime
import os

# Configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
REPORT_OUTPUT_DIR = "reports"

def generate_report():
    print(f"🚀 Generating Operational Report for {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Fetch Health Metrics
    try:
        health_res = httpx.get(f"{API_BASE_URL}/health")
        health_data = health_res.json()
    except Exception as e:
        health_data = {"status": "error", "message": str(e)}

    # 2. Compile Report
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": health_data.get("status", "unknown"),
        "infrastructure": health_data.get("services", {}),
        "performance_metrics": health_data.get("metrics", {}),
        "recommendations": []
    }

    # 3. Dynamic Recommendations
    if report["performance_metrics"].get("queue_depth", 0) > 50:
        report["recommendations"].append("⚠️ High queue depth detected. Consider scaling up Celery workers.")
    
    if report["performance_metrics"].get("cpu_usage_percent", 0) > 80:
        report["recommendations"].append("⚠️ High CPU usage. Check for heavy background tasks or memory leaks.")

    if health_data.get("status") == "degraded":
        report["recommendations"].append("🚨 System is degraded. Investigate service connectivity immediately.")

    # 4. Save/Print Report
    if not os.path.exists(REPORT_OUTPUT_DIR):
        os.makedirs(REPORT_OUTPUT_DIR)
    
    file_path = os.path.join(REPORT_OUTPUT_DIR, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(file_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Report generated: {file_path}")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    generate_report()
