import logging, io
import boto3
import pandas as pd
import duckdb
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger()

def load_fips_data():
# AWS session
    session = boto3.Session(profile_name=os.getenv("AWS_PROFILE"))
    s3 = session.resource("s3")

    bucket = "de-project2-nppes"
    key = "kssnppes2/ssa_fips_state_county_2025.csv"

# NUCC Taxonomy 250

    obj = s3.Object(bucket, key)
    data = obj.get().get("Body").read()
    df_fips = pd.read_csv(io.BytesIO(data))

# DuckDB: register df then create table

    duckdb_conn = duckdb.connect("dev.duckdb")
    duckdb_conn.register("df_fips", df_fips)
    
    duckdb_conn.execute(" CREATE SCHEMA IF NOT EXISTS raw;")


    duckdb_conn.execute("""
        CREATE OR REPLACE TABLE raw.fips AS
        SELECT * FROM df_fips 
    """)

    fips = duckdb_conn.execute("SELECT * FROM raw.fips").fetchdf()
    print(fips.head())  
    duckdb_conn.close()

if __name__ == "__main__":
    load_fips_data()