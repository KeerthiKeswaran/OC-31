from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import random
import psutil
import asyncpg, os, time, json
import redis.asyncio as redis
from dotenv import load_dotenv
from model import SampleData, DateTimeEncoder
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge, Counter
import logging

# Setup logging
logging.basicConfig(
    filename="slave2.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info("Slave2 server starting...")

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
REDIS_URL = os.getenv("REDIS_URL")

Instrumentator().instrument(app).expose(app)

# Define Prometheus metrics
s_cpu_usage = Gauge('cpu_usage_slave2', 'CPU Usage Percentage')
s_memory_usage = Gauge('memory_usage_slave2', 'Memory Usage Percentage')
s_response_time = Gauge('response_time_slave2', 'API Response Time')
s_error_rate = Gauge('error_rate_slave2', 'Percentage of Failed Requests')
s_throughput = Gauge('throughput_slave2', 'Requests per Second')
s_db_query_time = Gauge('db_query_time_slave2', 'Database Query Execution Time')

request_counter = Counter('http_requests_total', 'Total HTTP Requests')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    request_counter.inc()
    start_time = time.time()
    response = await call_next(request)
    response_time = time.time() - start_time

    # Update metrics
    s_response_time.set(response_time)
    s_throughput.set(request_counter._value.get())
    s_cpu_usage.set(psutil.cpu_percent())
    s_memory_usage.set(psutil.virtual_memory().percent)

    # Log all updated metrics including DB Query Time
    logging.info(f"Metrics updated - CPU Usage: {psutil.cpu_percent()}%, "
                 f"Memory Usage: {psutil.virtual_memory().percent}%, "
                 f"Response Time: {response_time}s, Throughput: {request_counter._value.get()}, "
                 f"DB Query Time: {s_db_query_time._value.get()}s")

    return response


pool = None
c_redis = None

@app.on_event("startup")
async def startup():
    global pool, c_redis
    pool = await asyncpg.create_pool(DATABASE_URL)
    c_redis = await redis.from_url(REDIS_URL, decode_responses=True)


@app.on_event("shutdown")
async def shutdown():
    await pool.close()
    await c_redis.close()


async def get_db_connection():
    return await pool.acquire()


async def release_db_connection(conn):
    await pool.release(conn)


@app.get("/")
def home():
    logging.info("Home endpoint accessed")
    return {"message": "Slave Server Running"}


@app.get("/get_data")
async def get_data():
    try:
        logging.info("Fetching data from the database...")
        start_time = time.time()
        cached_data = await c_redis.get("sample_data")
        
        if cached_data:
            logging.info("Cache hit: Returning cached data.")
            return json.loads(cached_data)
        
        conn = await get_db_connection()
        query = "SELECT id, name, value, created_at FROM sample_data"
        results = await conn.fetch(query)
        db_query_time = time.time() - start_time
        s_db_query_time.set(db_query_time)

        data_list = [
            {"id": row["id"], "name": row["name"], "value": row["value"], "created_at": row["created_at"]}
            for row in results
        ]

        await c_redis.set("sample_data", json.dumps(data_list, cls=DateTimeEncoder), ex=3600)

        logging.info("Data fetched successfully.")
        logging.info(f"DB Query Time: {db_query_time}s")

        return {"data": data_list}
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        s_error_rate.inc()
        raise HTTPException(status_code=500, detail=f"Error fetching data: {e}")
    finally:
        if 'conn' in locals():
            await release_db_connection(conn)


@app.post("/add_data")
async def add_data(data: SampleData):
    try:
        logging.info("Inserting new data into the database...")
        start_time = time.time()
        conn = await get_db_connection()
        query = "INSERT INTO sample_data (name, value) VALUES ($1, $2) RETURNING id, created_at"
        result = await conn.fetchrow(query, data.name, data.value)
        db_query_time = time.time() - start_time
        s_db_query_time.set(db_query_time)

        logging.info("Data inserted successfully.")
        logging.info(f"DB Query Time: {db_query_time}s")

        return {
            "id": result["id"],
            "name": data.name,
            "value": data.value,
            "created_at": result["created_at"]
        }
    except Exception as e:
        logging.error(f"Error inserting data: {e}")
        s_error_rate.inc()
        raise HTTPException(status_code=500, detail=f"Error inserting data: {e}")
    finally:
        await release_db_connection(conn)


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
        s_error_rate.inc()
        raise ValueError("Simulated Server Error")
