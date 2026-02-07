import requests
import polars as pl
import boto3
import os
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils.logger import my_logger

logger = my_logger()

load_dotenv()

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")
AWS_PROFILE = os.getenv("AWS_PROFILE")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_PREFIX = os.getenv("S3_PREFIX")

BASE_URL = "https://api.census.gov/data/2022/acs/acs5"

def extract_census_data():

    variables = "NAME,B01003_001E,B19013_001E,B01002_001E"

    params = {
        "get": variables,
        "for": "zip code tabulation area:*",
        "key": CENSUS_API_KEY
    }

    logger.info("Extracting census data from API...")

    try:
        response = requests.get(BASE_URL, params=params) # schema means columns in polars
        response.raise_for_status()

        data = response.json()

        headers = data[0]
        rows = data[1:]

        census = pl.DataFrame(rows, schema=headers, orient="row")  # schema means columns in polars

        census = census.rename({
            "B01003_001E": "total_population",
            "B19013_001E": "median_household_income",
            "B01002_001E": "median_age",
            "zip code tabulation area": "zip_code"
        })

        logger.info("Census data extracted successfully.")
        return census
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error extracting census data: {e}")
        return None
    
def upload_to_s3(census):
    logger.info("Uploading census data to S3...")

    logger.info("Connecting to S3...")
    session = boto3.Session(profile_name=AWS_PROFILE)
    s3_client = session.client("s3")
    logger.info("Successfully connected to S3.")

    file_name = f"census_data.csv"
    s3_key = f"{S3_PREFIX}{file_name}"
    
    logger.info(f"Uploading file {file_name} to S3 key {s3_key}")

    csv_data = census.write_csv()

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=csv_data
        )
        logger.info("Census data uploaded to S3 successfully.")
    
    except Exception as e:
        logger.error(f"Error uploading census data to S3: {e}")
        raise e

if __name__ == "__main__":
    census = extract_census_data()
    if census is not None:
        print(census.head())
        upload_to_s3(census)
    else:
        logger.error("Census data extraction failed. Upload to S3 aborted.")