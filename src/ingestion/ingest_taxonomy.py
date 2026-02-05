import logging, io
import boto3
import pandas as pd
import duckdb
import os
from dotenv import load_dotenv      
load_dotenv()

logger = logging.getLogger()

# AWS session
def load_nucc_taxonomy():
    
    session = boto3.Session(profile_name=os.getenv("AWS_PROFILE"))
    s3 = session.resource("s3")

    bucket = "de-project2-nppes"
    key = "kssnppes2/nucc_taxonomy_250.csv"

    # NUCC Taxonomy 250

    obj = s3.Object(bucket, key)
    data = obj.get().get("Body").read()
    df_nucc_taxonomy_250 = pd.read_csv(io.BytesIO(data))

    # DuckDB: register df then create table

    duckdb_conn = duckdb.connect("dev.duckdb")
    duckdb_conn.register("df_nucc_taxonomy_250", df_nucc_taxonomy_250)

    duckdb_conn.execute(" CREATE SCHEMA IF NOT EXISTS raw;")

    duckdb_conn.execute("""
        CREATE OR REPLACE TABLE raw.nucc_taxonomy_250 AS
        SELECT * FROM df_nucc_taxonomy_250 
    """)

    nucc_taxonomy_250 = duckdb_conn.execute("SELECT * FROM raw.nucc_taxonomy_250").fetchdf()
    print(nucc_taxonomy_250.head(4))  
    duckdb_conn.close()

if __name__ == "__main__":
    load_nucc_taxonomy()
    