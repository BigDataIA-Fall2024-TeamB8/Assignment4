# Use Python 3.12 as the base image
FROM python:3.12-slim

# Install essential packages and Airflow dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libblas-dev \
    liblapack-dev \
    libpq5 \
    libjpeg-dev \
    gcc \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables for Airflow
ENV AIRFLOW_HOME=/opt/airflow
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__CORE__EXECUTOR=LocalExecutor

# Create the Airflow home directory
RUN mkdir -p $AIRFLOW_HOME
WORKDIR $AIRFLOW_HOME

# Copy the requirements file
COPY requirements.txt .

# Install pip and required Python packages
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Install Airflow
RUN pip install apache-airflow==2.6.0

# Set the Airflow user as the default user
USER root
