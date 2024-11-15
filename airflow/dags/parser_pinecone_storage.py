from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import json
import boto3
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import PdfFormatOption
from docling_core.types.doc import PictureItem, TableItem
from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

# Initialize API keys and credentials
PINECONE_API_KEY = ''
PINECONE_ENVIRONMENT = 'us-east-1'
INDEX_NAME = 'assignment4-index'
EMBEDDING_DIMENSION = 1536
OPENAI_API_KEY = ''
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
S3_BUCKET_NAME = 'cfai-three'
S3_EXTRACTION_BUCKET_NAME = 'cfai-three-extraction'

# Initialize Pinecone, OpenAI embeddings, and boto3 client for S3
pc = Pinecone(api_key=PINECONE_API_KEY)
spec = ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT)
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(name=INDEX_NAME, dimension=EMBEDDING_DIMENSION, metric="cosine", spec=spec)
index = pc.Index(INDEX_NAME)
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=OPENAI_API_KEY)
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
        kwargs['ti'].xcom_push(key='s3_keys', value=keys)

def extract_content(**kwargs):
    """Extract document content using Docling and save locally for each S3 key."""
    s3_keys = kwargs['ti'].xcom_pull(task_ids='list_s3_files', key='s3_keys')
    for s3_key in s3_keys:
        try:
            file_path = f"/tmp/{s3_key.split('/')[-1]}"
            s3_client.download_file(S3_BUCKET_NAME, s3_key, file_path)
            output_dir = "/tmp/docling_output"
            os.makedirs(output_dir, exist_ok=True)

            # Set up Docling extraction options
            pipeline_options = PdfPipelineOptions(
                do_ocr=True,
                do_table_structure=True,
                table_structure_options={"mode": TableFormerMode.ACCURATE},
                extract_images=True,
                extract_figures=True,
                extract_graphs=True,
                images_scale=2.0,
                generate_table_images=True,
                generate_picture_images=True
            )
            converter = DocumentConverter(
                format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
            )
            result = converter.convert(file_path)
            document = result.document
            doc_filename = os.path.splitext(os.path.basename(file_path))[0]

            # Save text and JSON representations
            json_path = os.path.join(output_dir, f"{doc_filename}.json")
            text_path = os.path.join(output_dir, f"{doc_filename}.txt")
            
            with open(json_path, "w", encoding="utf-8") as json_file:
                json.dump(document.export_to_dict(), json_file, ensure_ascii=False, indent=4)
            with open(text_path, "w", encoding="utf-8") as text_file:
                text_file.write(document.export_to_text())

            # Save extracted tables and images
            table_counter = 0
            picture_counter = 0
            for element, _ in document.iterate_items():
                # Process and save tables as CSV
                if isinstance(element, TableItem):
                    table_counter += 1
                    table_df = element.export_to_dataframe()
                    table_csv_path = os.path.join(output_dir, f"{doc_filename}-table-{table_counter}.csv")
                    table_df.to_csv(table_csv_path, index=False)
                    
                    # Upload to S3
                    with open(table_csv_path, 'rb') as csv_file:
                        s3_client.put_object(
                            Body=csv_file,
                            Bucket=S3_EXTRACTION_BUCKET_NAME,
                            Key=f"{doc_filename}/table_{table_counter}.csv"
                        )

                # Process and save figures as PNG
                if isinstance(element, PictureItem):
                    picture_counter += 1
                    picture_path = os.path.join(output_dir, f"{doc_filename}-figure-{picture_counter}.png")
                    element.image.pil_image.save(picture_path, format="PNG")
                    
                    # Upload to S3
                    with open(picture_path, 'rb') as img_file:
                        s3_client.put_object(
                            Body=img_file,
                            Bucket=S3_EXTRACTION_BUCKET_NAME,
                            Key=f"{doc_filename}/figure_{picture_counter}.png"
                        )

            # Push paths to XCom for later tasks
            kwargs['ti'].xcom_push(key=f"extracted_data_{s3_key}", value={
                "json_path": json_path,
                "text_path": text_path,
                "title": s3_key,
                "doc_filename": doc_filename
            })

        except Exception as e:
            print(f"Error processing {s3_key}: {e}")

def store_in_pinecone_and_s3(**kwargs):
    """Store extracted document content in Pinecone and S3."""
    s3_keys = kwargs['ti'].xcom_pull(task_ids='list_s3_files', key='s3_keys')
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=200)

    for s3_key in s3_keys:
        data = kwargs['ti'].xcom_pull(task_ids='extract_content', key=f"extracted_data_{s3_key}")
        json_path = data["json_path"]
        text_path = data["text_path"]
        title = data["title"]
        doc_filename = data["doc_filename"]

        # Parse and upsert text content into Pinecone
        if os.path.exists(text_path):
            with open(text_path, "r", encoding="utf-8") as txt_file:
                text_data = txt_file.read()
                for chunk in text_splitter.split_text(text_data):
                    vector_id = f"{doc_filename}_text_chunk_{datetime.now().timestamp()}"
                    embedding = embeddings.embed_query(chunk)
                    metadata = {
                        "title": title[:50],
                        "content_type": "text",
                        "content": chunk[:200]  # Storing a snippet of the text for reference
                    }
                    index.upsert([(vector_id, embedding, metadata)])

        # Parse the JSON file for tables and images metadata and upsert into Pinecone
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as json_file:
                doc_data = json.load(json_file)
                tables = doc_data.get("tables", [])
                pictures = doc_data.get("pictures", [])

                # Upsert table references in Pinecone
                for idx, table in enumerate(tables):
                    vector_id = f"{doc_filename}_table_{idx}_{datetime.now().timestamp()}"
                    metadata = {
                        "title": title[:50],
                        "content_type": "table",
                        "s3_path": f"{doc_filename}/table_{idx}.csv"
                    }
                    embedding = embeddings.embed_query("Table data")
                    index.upsert([(vector_id, embedding, metadata)])

                # Upsert picture references in Pinecone
                for idx, picture in enumerate(pictures):
                    vector_id = f"{doc_filename}_figure_{idx}_{datetime.now().timestamp()}"
                    metadata = {
                        "title": title[:50],
                        "content_type": "figure",
                        "s3_path": f"{doc_filename}/figure_{idx}.png"
                    }
                    embedding = embeddings.embed_query("Figure data")
                    index.upsert([(vector_id, embedding, metadata)])

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
