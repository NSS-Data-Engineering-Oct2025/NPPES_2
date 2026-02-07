import duckdb
import boto3
import os
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils.logger import my_logger

logger = my_logger()

load_dotenv()

AWS_PROFILE = os.getenv('AWS_PROFILE')
S3_BUCKET = os.getenv('S3_BUCKET')
S3_PREFIX = os.getenv('S3_PREFIX')
DUCKDB_PATH = "dev.duckdb"

def ingest_census_to_duckdb():
    logger.info("Starting census data ingestion to DuckDB.")
    
    s3_key = f"{S3_PREFIX}census_data.csv"
    logger.info(f"Using census file: {s3_key}")

    logger.info(f"Connecting to DuckDB at {DUCKDB_PATH}.")
    conn = duckdb.connect(DUCKDB_PATH)

    try:
        logger.info("Loading AWS extension...")
        conn.execute("INSTALL  httpfs;")
        conn.execute("LOAD httpfs;")

        logger.info("Setting AWS credentials from SSO profile.")
        session = boto3.Session(profile_name=AWS_PROFILE)
        credentials = session.get_credentials()

        conn.execute("SET s3_region='us-west-2';")
        conn.execute(f"SET s3_access_key_id='{credentials.access_key}';")
        conn.execute(f"SET s3_secret_access_key='{credentials.secret_key}';")

        if credentials.token:
            conn.execute(f"SET s3_session_token='{credentials.token}';")

        logger.info("Creating raw schema if not exists...")
        conn.execute("CREATE SCHEMA IF NOT EXISTS raw;")

        s3_path = f"s3://{S3_BUCKET}/{s3_key}"

        logger.info("Creating census table if not exists...")
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS raw.census AS
                     SELECT * FROM read_csv_auto('{s3_path}')
        """)

        row_count = conn.execute("SELECT COUNT(*) FROM raw.census;").fetchone()[0]
        logger.info(f"Successfully loaded {row_count} rows into raw.census table.")

    except Exception as e:
        logger.error(f"Error during census data ingestion: {e}")
        raise

    finally:
        conn.close()
        logger.info("DuckDB connection closed.")

if __name__ == "__main__":
    ingest_census_to_duckdb()