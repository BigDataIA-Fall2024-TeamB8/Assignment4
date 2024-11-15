# -*- coding: utf-8 -*-
"""Architecture Diagram.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/12DJTgg5OaZKyxA0Ji7AFDjw31TcYl4Z1
"""

!pip install diagrams
!apt-get install -y graphviz

from google.colab import files
uploaded = files.upload()

from diagrams import Diagram, Cluster
from diagrams.onprem.workflow import Airflow
from diagrams.aws.storage import S3
from diagrams.custom import Custom
from diagrams.onprem.client import Users

# Path to custom icons
docling_icon_path = "/content/Docling.png"
pinecone_icon_path = "/content/Pinecone.png"
langraph_icon_path = "/content/Langraph.png"
streamlit_icon_path = "/content/streamlit.png"
pdf_icon_path = "/content/PDF_Report.png"
agent_ai_icon_path = "/content/AgentAI.png"
with Diagram("Research Tool Architecture for Assignment 4", show=True, direction="LR"):

    # Cluster 1: Document Parsing and Vector Storage Pipeline
    with Cluster("Data Ingestion and Vector Storage"):
        cfe_publications = Custom("CFE Publications Files", "/content/CFE_Publications.png")
        airflow = Airflow("Airflow Pipeline")
        docling = Custom("Docling ", docling_icon_path)
        s3_bucket = S3("AWS S3 Bucket ")
        pinecone = Custom("Pinecone ", pinecone_icon_path)

        # Connections within Cluster 1
        cfe_publications >> airflow >> docling >> s3_bucket >> pinecone

    # Cluster 2: Multi-Agent Research System
    with Cluster("Research Agent System"):
        langraph = Custom("Langraph", langraph_icon_path)
        agent_ai = Custom("Agent AI", agent_ai_icon_path)

        # Connections for multi-agent research system
        pinecone >> langraph
        agent_ai >> langraph

    # Cluster 3: User Interaction and Export
    with Cluster("User Interaction Interface"):
        streamlit = Custom("Streamlit Application", streamlit_icon_path)
        user = Users("User")
        pdf_report = Custom("PDF Export", pdf_icon_path)

        # Connections for user interface and export
        langraph >> streamlit >> user
        streamlit >> pdf_report

from IPython.display import Image, display
display(Image(filename="/content/research_tool_architecture_for_assignment_4.png"))

