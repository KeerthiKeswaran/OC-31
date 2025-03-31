import json
import re
import asyncio
import os
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pipeline import init_pipeline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_llm = None
LOG_FILE = "slave1.log"
CODE_FILE = "slave1.py"

@app.on_event("startup")
async def startup():
    global agent_llm
    agent_llm = init_pipeline()

def parse_logs_and_metrics(log_file):
    logs = []
    metrics = {
        "cpu_usage": None,
        "memory_usage": None,
        "response_time": None,
        "error_rate": None,
        "db_query_time": None,
        "throughput": None
    }

    with open(log_file, "r") as file:
        for line in file:
            logs.append(line.strip())

            cpu_match = re.search(r"CPU Usage: (\d+\.\d+)", line)
            if cpu_match:
                metrics["cpu_usage"] = float(cpu_match.group(1))

            memory_match = re.search(r"Memory Usage: (\d+\.\d+)", line)
            if memory_match:
                metrics["memory_usage"] = float(memory_match.group(1))

            response_match = re.search(r"Response Time: (\d+\.\d+)", line)
            if response_match:
                metrics["response_time"] = float(response_match.group(1))

            error_match = re.search(r"Error Rate: (\d+\.\d+)", line)
            if error_match:
                metrics["error_rate"] = float(error_match.group(1))

            db_match = re.search(r"DB Query Time: (\d+\.\d+)", line)
            if db_match:
                metrics["db_query_time"] = float(db_match.group(1))

            throughput_match = re.search(r"Throughput: (\d+\.\d+)", line)
            if throughput_match:
                metrics["throughput"] = float(throughput_match.group(1))
    print(logs,"\n",metrics)
    return metrics


def get_code_context(code_file):
    try:
        with open(code_file, "r") as file:
            return file.read()
    except FileNotFoundError:
        return "Code file not found."

async def monitor_logs(websocket: WebSocket):
    last_size = os.path.getsize(LOG_FILE) if os.path.exists(LOG_FILE) else 0

    await websocket.accept()
    print("WebSocket connection established.")

    while True:
        current_size = os.path.getsize(LOG_FILE) if os.path.exists(LOG_FILE) else 0

        if current_size > last_size:
            with open(LOG_FILE, "r") as file:
                file.seek(last_size)
                new_logs = file.readlines()
            print(new_logs)
            error_logs = [log.strip() for log in new_logs if "ERROR" in log]
            last_size = current_size  

            if error_logs:
                metrics = parse_logs_and_metrics(LOG_FILE)
                code_context = get_code_context(CODE_FILE)

                inputs = {
                    "logs": "\n".join(error_logs),
                    "cpu_usage": metrics["cpu_usage"],
                    "memory_usage": metrics["memory_usage"],
                    "response_time": metrics["response_time"],
                    "error_rate": metrics["error_rate"],
                    "db_query_time": metrics["db_query_time"],
                    "throughput": metrics["throughput"],
                    "code_context": code_context
                }

                response = agent_llm.invoke(inputs)

                try:
                    data = response.content
                    cleaned_data = data.replace('```json', '').replace('```', '').strip()
                    response_json = json.loads(cleaned_data) 
                except json.JSONDecodeError:
                    response_json = {"error": "Invalid response from LLM"}

                with open(LOG_FILE, "a") as log_file:
                    log_file.write("\n--- AI Analysis ---\n")
                    log_file.write(json.dumps(response_json, indent=4))
                    log_file.write("\n-------------------\n")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await monitor_logs(websocket)
