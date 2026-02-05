import logging, io
import boto3
import pandas as pd
import duckdb

logger = logging.getLogger()

def load_nppes_data():
# AWS session
    session = boto3.Session(profile_name="First_Project")
    s3 = session.resource("s3")

    bucket = "de-project2-nppes"
    key = "kssnppes2/nppes_sample.csv"

# NUCC Taxonomy 250

    obj = s3.Object(bucket, key)
    data = obj.get().get("Body").read()
    df_nppes = pd.read_csv(io.BytesIO(data))

# DuckDB: register df then create table

    duckdb_conn = duckdb.connect("dev.duckdb")
    duckdb_conn.register("df_nppes", df_nppes)
    
    duckdb_conn.execute(" CREATE SCHEMA IF NOT EXISTS raw;")


    duckdb_conn.execute("""
        CREATE OR REPLACE TABLE raw.nppes AS
        SELECT * FROM df_nppes 
    """)

    nppes = duckdb_conn.execute("SELECT * FROM raw.nppes").fetchdf()
    print(nppes.head())  
    duckdb_conn.close()

if __name__ == "__main__":
    load_nppes_data()


