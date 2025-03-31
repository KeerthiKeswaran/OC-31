import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import random
import psutil
import asyncpg, os, time
from dotenv import load_dotenv
from model import SampleData
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge, Counter

# Setup logging
logging.basicConfig(
    filename="slave1.log",  # Log file location
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,  # Set logging level to INFO or DEBUG
)

# Log initial message
logging.info("Slave1 server starting...")

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")

Instrumentator().instrument(app).expose(app)

# Metrics definitions
g_cpu_usage = Gauge('cpu_usage_slave1', 'CPU Usage Percentage')
g_memory_usage = Gauge('memory_usage_slave1', 'Memory Usage Percentage')
g_response_time = Gauge('response_time_slave1', 'API Response Time')
g_error_rate = Gauge('error_rate_slave1', 'Percentage of Failed Requests')
g_throughput = Gauge('throughput_slave1', 'Requests per Second')
g_db_query_time = Gauge('db_query_time_slave1', 'Database Query Execution Time')

request_counter = Counter('http_requests_total', 'Total HTTP Requests')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    request_counter.inc()  # Increment total HTTP requests count
    start_time = time.time()
    response = await call_next(request)
    response_time = time.time() - start_time
    
    # Track and log all metrics
    g_response_time.set(response_time)  # Track response time
    g_throughput.set(request_counter._value.get())  # Track throughput
    g_cpu_usage.set(psutil.cpu_percent())  # Track CPU usage
    g_memory_usage.set(psutil.virtual_memory().percent)  # Track memory usage
    
    # Log metrics
    logging.info(f"Metrics updated - CPU Usage: {psutil.cpu_percent()}%, "
                 f"Memory Usage: {psutil.virtual_memory().percent}%, "
                 f"Response Time: {response_time}s, Throughput: {request_counter._value.get()}, "
                 f"DB Query Time: {g_db_query_time._value.get()}s")
    
    return response

@app.get("/")
def home():
    logging.info("Home endpoint accessed")
    return {"message": "Slave1 Server Running"}

@app.get("/get_data")
async def get_data():
    try:
        logging.info("Fetching data from the database...")
        start_time = time.time()
        conn = await asyncpg.connect(DATABASE_URL)
        query = "SELECT id, name, value, created_at FROM sample_data"
        results = await conn.fetch(query)
        g_db_query_time.set(time.time() - start_time)  # Track DB query time
        await conn.close()
        logging.info("Data fetched successfully.")
        
        # Log data retrieval metrics
        logging.info(f"DB Query Time: {g_db_query_time._value.get()}s")
        
        return {"data": [
            {"id": row["id"], "name": row["name"], "value": row["value"], "created_at": row["created_at"]}
            for row in results
        ]}
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        g_error_rate.inc()
        raise HTTPException(status_code=500, detail=f"Error fetching data: {e}")

@app.post("/add_data")
async def add_data(data: SampleData):
    try:
        logging.info("Inserting new data into the database...")
        start_time = time.time()
        conn = await asyncpg.connect(DATABASE_URL)
        query = "INSERT INTO sample_data (name, value) VALUES ($1, $2) RETURNING id, created_at"
        result = await conn.fetchrow(query, data.name, data.value)
        g_db_query_time.set(time.time() - start_time)  # Track DB query time
        await conn.close()
        logging.info("Data inserted successfully.")
        
        # Log data insertion metrics
        logging.info(f"DB Query Time: {g_db_query_time._value.get()}s")
        
        return {"id": result["id"], "name": data.name, "value": data.value, "created_at": result["created_at"]}
    except Exception as e:
        logging.error(f"Error inserting data: {e}")
        g_error_rate.inc()
        raise HTTPException(status_code=500, detail=f"Error inserting data: {e}")

@app.get("/health")
def health_check():
    logging.info("Health check endpoint accessed")
    return {"status": "healthy"}

@app.get("/error")
def error_endpoint():
    if random.choice([True, False]):
        logging.info("/error endpoint accessed successfully")
        return {"message": "Success"}
    else:
        logging.error("Simulated error occurred!")
        g_error_rate.inc()
        raise ValueError("Simulated Server Error")
