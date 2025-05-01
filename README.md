# AI-Powered Observability and Log Analysis System

This project presents an integrated observability solution that combines traditional monitoring tools (Prometheus, Grafana, Loki) with an AI-powered log analysis engine. Designed for distributed environments, the system captures and analyzes metrics and logs in real-time, detects anomalies, and provides root cause analysis using a language model (LLM) integrated through LangChain and Groq Cloud.

### Snap-Short of Dashboard: [Link for the Grafana-Dashboard](http://localhost:3000/dashboard/snapshot/ef5YGybGLI716vB2BTCs8eU0Wcc4fBNm?orgId=0&from=2025-03-31T14:14:34.993Z&to=2025-03-31T14:29:34.993Z&timezone=browser&refresh=10s)

---

## Table of Contents

- [Introduction](#introduction)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Components](#components)
- [Technologies Used](#technologies-used)
- [Setup Instructions](#setup-instructions)
- [Sample Output](#sample-output)
- [Known Limitations](#known-limitations)

---

## Introduction

Modern distributed systems generate vast amounts of logs and metrics. This system extends conventional observability stacks by integrating a Language Model (LLM) to intelligently interpret logs, detect anomalies, and recommend actionable solutions. The system is capable of live analysis, supports threshold-based inference, and can significantly reduce mean time to detect (MTTD) and mean time to resolution (MTTR) for production issues.

---

## Key Features

- Real-time monitoring of server metrics via Prometheus and Grafana.
- Centralized logging using Loki.
- Anomaly detection based on log level (ERROR/WARNING).
- Root cause analysis and structured recommendations using an LLM.
- Instruction templates via LangChain to guide the model.
- Configurable threshold-based log inference to reduce overhead.
- Distributed server log collection and analysis.
- Supports scalability with master-agent architecture.

---

## System Architecture

![Image](https://github.com/user-attachments/assets/c0e500ac-3937-4964-bd42-c10f05d2bcdb)

- **Slave Servers**: Push logs to designated log shipper files.
- **Prometheus**: Scrapes metrics at regular intervals.
- **Loki**: Aggregates and stores logs.
- **Grafana**: Provides dashboards for metrics and AI-generated analysis.
- **LLM Server**: Runs a language model using LangChain + Groq Cloud for inference.
- **WebSocket**: Facilitates continuous log stream and communication between master and model.

---

## Response Logs from LLM:

![Image](https://github.com/user-attachments/assets/87e1482c-daee-48b1-a031-f99fb4828c7d)


## Components

### 1. Prometheus Configuration
- Scrapes CPU, Memory, Response Time, Error Rate, DB Query Time, and Throughput metrics.
- Supports distributed server metrics scraping.

### 2. Loki Integration
- Collects logs from all servers.
- Includes separate log shippers for each slave node.

### 3. Grafana Dashboards
- Live visualization of metrics and logs.
- Custom panels for LLM-generated insights.

### 4. LangChain + LLM (via Groq Cloud)
- Generates structured JSON responses containing:
  - Root Cause
  - Severity Level
  - Affected Services
  - Metric Analysis
  - Log Snapshot
  - Performance Comparison
  - Recommended Actions
  - Next Steps

### 5. Log Trigger Conditions
- Model inference is triggered only on ERROR or WARNING logs to optimize performance.

---

## Technologies Used

- **Prometheus** – Metrics collection
- **Grafana** – Data visualization
- **Loki** – Log aggregation.
- **Transformer-Model (Groq-Cloud Model - temporary)** - t5-base Model, Finetuned and deployed on ModelBit.
- **WebSocket** – Bi-directional communication
- **Python** – Backend orchestration and model interface

---

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/ai-observability-system.git
   cd ai-observability-system
   ```

2. **Start Prometheus and Loki**
   - Use `docker-compose` or manual binaries.
   - Ensure scrape configs are updated for all slave servers.

3. **Configure Slave Log Shippers**
   - Log files should follow structured format.
   - Add log shipping paths to Loki config.

4. **Run LLM Master Server**
   ```bash
   python llm_master_server.py
   ```

5. **Connect WebSocket Clients**
   - Slave servers should open socket to master for real-time log push.

6. **Launch Grafana**
   - Import prebuilt dashboards.
   - Integrate with Loki and Prometheus data sources.

7. **Verify LLM Inference**
   - Trigger a warning/error event.
   - Check Grafana JSON panel for AI response.

---

## Sample Output

```json
{
  "Root Cause": "Database query performance issue and slow API response",
  "Severity Level": "Medium",
  "Affected Services": ["Database Service", "API Endpoint /slow"],
  "Metrics Analysis": {
    "CPU Usage": 85.4,
    "Memory Usage": 72.1,
    "Response Time": 2.3,
    "Error Rate": 5.2,
    "DB Query Time": 1.8,
    "Throughput": 30
  },
  "Log Analysis": [
    {"Timestamp": "2025-03-31 12:00:02", "Log Level": "WARNING", "Message": "Response time exceeded threshold (2s)"},
    {"Timestamp": "2025-03-31 12:00:02", "Log Level": "ERROR", "Message": "Database query took too long (1.8s)"}
  ],
  "Performance Comparison": {
    "Response Time": "Exceeded threshold of 2s",
    "DB Query Time": "Took 1.8s, indicating a potential database performance issue"
  },
  "Recommended Solution": [
    "Optimize database queries to reduce query time",
    "Improve error handling for slow API responses",
    "Consider implementing caching or load balancing"
  ],
  "Next Steps": [
    "Investigate and optimize database queries",
    "Monitor API response times and adjust thresholds",
    "Consider scaling up or optimizing backend algorithms"
  ]
}
```

---

## Known Limitations

- LLM is not triggered for every log due to performance constraints.
- Currently inference is conditional (ERROR/WARNING only).
- System is partially automated; engineers are still required for critical intervention.
- No direct source file modification or automatic patching is implemented yet.
