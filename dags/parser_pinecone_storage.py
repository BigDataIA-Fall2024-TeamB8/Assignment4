from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import boto3
from pinecone import Pinecone, ServerlessSpec
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import PdfFormatOption
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import json

# Initialize Pinecone, OpenAI, and AWS S3
PINECONE_API_KEY = 'Your pinecone key'
PINECONE_ENVIRONMENT = 'us-east-1'
INDEX_NAME = 'assignment4-index'
EMBEDDING_DIMENSION = 1536
OPENAI_API_KEY = 'Your OpenAI Key'
AWS_ACCESS_KEY_ID = ' AWS Access Key'
AWS_SECRET_ACCESS_KEY = ' AWS Secret Key'
S3_BUCKET_NAME = 'cfai-three'
S3_EXTRACTION_BUCKET_NAME = 'cfai-three-extraction'

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
spec = ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT)
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(name=INDEX_NAME, dimension=EMBEDDING_DIMENSION, metric="cosine", spec=spec)
index = pc.Index(INDEX_NAME)

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=OPENAI_API_KEY)

# Initialize boto3 client for S3
s3_client = boto3.client(
    's3',
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def list_s3_files(**kwargs):
    """List all PDF files in the S3 bucket and push each key to XCom for batch processing."""
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME)
    keys = [item['Key'] for item in response.get('Contents', []) if item['Key'].endswith('.pdf')]
    if keys:
        print(f"Found {len(keys)} PDF files in S3 bucket '{S3_BUCKET_NAME}': {keys}")
        kwargs['ti'].xcom_push(key='s3_keys', value=keys)  # Push all keys to XCom

def extract_content(**kwargs):
    """Extract document content using Docling for a batch of S3 keys."""
    s3_keys = kwargs['ti'].xcom_pull(task_ids='list_s3_files', key='s3_keys')
    for s3_key in s3_keys:
        print(f"Attempting to process file: {s3_key}")
        
        try:
            # Download the file
            file_path = f"/tmp/{s3_key.split('/')[-1]}"
            s3_client.download_file(S3_BUCKET_NAME, s3_key, file_path)
            print(f"Downloaded {s3_key} to {file_path}")

            # DocumentConverter setup and conversion
            pipeline_options = PdfPipelineOptions(
                do_ocr=True,
                do_table_structure=True,
                table_structure_options={"mode": TableFormerMode.ACCURATE},
                extract_images=True,
                extract_figures=True,
                extract_graphs=True
            )
            converter = DocumentConverter(
                format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
            )
            result = converter.convert(file_path)
            document = result.document
            print(f"Converted document {s3_key} with result: {document}")

            # Process pages and handle attributes carefully
            pages = []
            for page_num, page in enumerate(document.pages):
                page_content = {}
                
                # Extract text if available
                if hasattr(page, 'texts'):
                    page_content["text"] = [text.text for text in page.texts]
                else:
                    print(f"Warning: Page {page_num} in {s3_key} has no 'texts' attribute.")

                # Extract tables, images, graphs, and figures
                page_content.update({
                    "tables": [table.to_dict() for table in getattr(page, 'tables', [])],
                    "images": [img.to_dict() for img in getattr(page, 'pictures', [])],
                    "graphs": [fig.to_dict() for fig in getattr(page, 'figures', []) if fig.metadata.get("type", "").lower() == "graph"],
                    "figures": [fig.to_dict() for fig in getattr(page, 'figures', []) if fig.metadata.get("type", "").lower() == "figure"]
                })
                
                # Log the type and length of content detected on each page
                print(f"Page {page_num} in {s3_key} content types: {[(key, len(val)) for key, val in page_content.items()]}")
                
                pages.append(page_content)
            
            # Push structured data to XCom
            kwargs['ti'].xcom_push(key=f'extracted_data_{s3_key}', value={"pages": pages, "title": s3_key})

        except Exception as e:
            print(f"Error processing {s3_key}: {e}")



def store_in_pinecone_and_s3(**kwargs):
    """Store extracted document content in Pinecone and S3."""
    data = kwargs['ti'].xcom_pull(task_ids='extract_content', key='extracted_data')
    print("Pulled extracted data from XCom.")
    
    if not data:
        print("No data to process.")
        return
    
    pages = data["pages"]
    title = data["title"]
    print(f"Processing document: {title}, with {len(pages)} pages.")
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=200)
    sanitized_title = title.replace(" ", "_")
    
    for idx, page in enumerate(pages):
        for content_type, items in page.items():
            if items:
                print(f"Storing {content_type} items from Page {idx + 1}")
                if content_type == "text":
                    for chunk_idx, chunk in enumerate(text_splitter.split_text(" ".join(items))):
                        vector_id = f"{sanitized_title}_page{idx+1}_{content_type}_chunk{chunk_idx}_{datetime.now().timestamp()}"
                        metadata = {
                            "title": title[:50],
                            "page": idx + 1,
                            "content_type": content_type,
                            "chunk_index": chunk_idx,
                            "text_snippet": chunk[:100]
                        }
                        embedding = embeddings.embed_query(chunk)
                        index.upsert([(vector_id, embedding, metadata)])
                        print(f"Upserted text chunk {chunk_idx} of Page {idx + 1} into Pinecone.")
                
                else:
                    for item_idx, item in enumerate(items):
                        vector_id = f"{sanitized_title}_page{idx+1}_{content_type}_{item_idx}_{datetime.now().timestamp()}"
                        metadata = {
                            "title": title[:50],
                            "page": idx + 1,
                            "content_type": content_type,
                            "item_index": item_idx,
                            "metadata": item
                        }
                        embedding = embeddings.embed_query(str(item))
                        index.upsert([(vector_id, embedding, metadata)])
                        print(f"Upserted {content_type} item {item_idx} of Page {idx + 1} into Pinecone.")
                        
                        s3_key = f"{sanitized_title}/page{idx+1}/{content_type}_{item_idx}.json"
                        s3_client.put_object(
                            Body=json.dumps(item),
                            Bucket=S3_EXTRACTION_BUCKET_NAME,
                            Key=s3_key
                        )
                        print(f"Stored {content_type} item for page {idx + 1} in S3 at {s3_key}.")


def create_dag():
    with DAG(
        'docling_pipeline_detailed',
        default_args={'start_date': datetime(2023, 1, 1)},
        schedule_interval=None,
        catchup=False
    ) as dag:
        
        list_files = PythonOperator(
            task_id='list_s3_files',
            python_callable=list_s3_files,
            provide_context=True
        )
        
        extract_content_task = PythonOperator(
            task_id='extract_content',
            python_callable=extract_content,
            provide_context=True
        )
        
        store_task = PythonOperator(
            task_id='store_in_pinecone_and_s3',
            python_callable=store_in_pinecone_and_s3,
            provide_context=True
        )
        
        list_files >> extract_content_task >> store_task

    return dag

docling_pipeline_detailed = create_dag()
