from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from datetime import datetime
import os
import pinecone
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import PdfFormatOption

# Initialize Pinecone
pinecone.init(api_key='YOUR_PINECONE_API_KEY', environment='YOUR_PINECONE_ENVIRONMENT')
index = pinecone.Index('your_pinecone_index_name')

# Define your S3 bucket and Pinecone index name
S3_BUCKET_NAME = 'cfai-three'

def parse_and_store_document(s3_key):
    # Fetch document from S3
    s3 = S3Hook(aws_conn_id='aws_default')
    file_path = s3.download_file(bucket_name=S3_BUCKET_NAME, key=s3_key)
    
    # Initialize Docling converter with advanced settings
    pipeline_options = PdfPipelineOptions(
        do_table_structure=True,
        extract_images=True,
        extract_figures=True,
        extract_graphs=True
    )
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )
    
    # Parse document and convert it to the detailed Docling format
    result = converter.convert(file_path)
    
    # Extract individual components and store them with references
    document = result.document
    extracted_content = {
        "text": [item.text for item in document.texts],
        "tables": [item for item in document.tables],
        "images": [item for item in document.pictures],
        "graphs": [item for item in document.figures if 'graph' in item.metadata.get("type", "").lower()],
        "figures": [item for item in document.figures if 'figure' in item.metadata.get("type", "").lower()],
        "references": {item.id: {"page": item.metadata.get("page_no"), "coordinates": item.metadata.get("bbox")} 
                       for item in document.texts + document.tables + document.pictures + document.figures}
    }
    
    # Embed the document's text for initial vector storage in Pinecone
    embedding = pinecone.embeddings("huggingface")  # Replace with the embedding model of choice
    vector = embedding.embed_text("\n".join(extracted_content["text"]))
    
    # Upsert vector into Pinecone index with metadata for retrieval
    index.upsert(vectors=[(s3_key, vector, extracted_content)])

def list_s3_files():
    # List all files in the S3 bucket
    s3 = S3Hook(aws_conn_id='aws_default')
    return s3.list_keys(bucket_name=S3_BUCKET_NAME)

def create_dag():
    with DAG(
        'docling_pipeline_detailed',
        default_args={'start_date': datetime(2023, 1, 1)},
        schedule_interval=None,
        catchup=False
    ) as dag:
        
        list_files = PythonOperator(
            task_id='list_s3_files',
            python_callable=list_s3_files
        )
        
        parse_and_store = PythonOperator(
            task_id='parse_and_store_document',
            python_callable=parse_and_store_document,
            op_args=['{{ ti.xcom_pull(task_ids="list_s3_files") }}']
        )
        
        list_files >> parse_and_store

    return dag

docling_pipeline_detailed = create_dag()
