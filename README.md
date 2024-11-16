# Assignment4
End-to-end research tool using an Airflow pipeline to process documents, store and search vectors, and create a multi-agent research interface.
FastAPI: [http://34.229.200.208:8000/docs]
Airflow: [http://34.229.200.208:8080/]

# Codelabs: []

## Table of Contents
- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)
  - [Step 1: Setting up and Running Airflow](#step-1-setting-up-and-running-airflow)
  - [Step 2: Running the Scraper to Upload Data to S3](#step-2-running-the-scraper-to-upload-data-to-s3)
  - [Step 3: Setting up and Running FastAPI and Streamlit](#step-4-setting-up-and-running-fastapi-and-streamlit)
- [Accessing the Application](#accessing-the-application)
- [Architecture](#architecture)
- [License](#license)

# Architecture Diagram
![image](https://github.com/user-attachments/assets/54ac10a4-2b0b-4ace-b838-76d48b4b9d55)

## Requirements

- **Docker**: Ensure Docker and Docker Compose are installed on your system.
- **Python 3.8+**
- **Airflow**: The Airflow DAGs are set up to be triggered manually after the Docker containers are running.

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
   ```
Install the required Python packages:

```bash

pip install -r requirements.txt
```
Set up environment variables by creating a .env file in the root directory (see Configuration for required variables).

# Configuration
Environment Variables
Create a .env file in the root directory and include the following environment variables:

# AWS S3 credentials
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
S3_BUCKET_NAME=your_s3_bucket_name
AWS_REGION=your_aws_region

# API keys and secrets
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
SECRET_KEY=your_jwt_secret_key
Replace the placeholders (your_*) with actual values for your environment.

## Running the Project

# Step 1: Setting up and Running Airflow
Start the Airflow services using Docker Compose:

```bash
docker-compose up -d
```
Access the Airflow web interface to trigger DAGs:

Go to http://localhost:8080.
Use the default credentials (e.g., airflow/airflow) if prompted.
Trigger the Airflow DAG scraper_to_s3 to scrape data and upload it to S3.

Find the DAG named scraper_to_s3 in the Airflow interface.
Manually trigger it to start the scraping and uploading process.

## Step 2: Running the Scraper to Upload Data to S3
You can also run the scraper script directly from the command line if needed.

```bash
python dags/scraper_to_s3.py
```
This will scrape data from the specified sources and upload it to the S3 bucket specified in the .env file.

### Step 4: Setting up and Running FastAPI and Streamlit
Ensure the necessary environment variables are set in .env.

Start the FastAPI and Streamlit applications using Docker Compose:

```bash
docker-compose up -d
```
FastAPI and Streamlit will be accessible on the following ports:

FastAPI: http://localhost:8000

