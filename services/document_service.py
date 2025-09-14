import logging
import asyncio
import base64
import io
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain_pinecone import PineconeVectorStore
import openai
import PyPDF2
import pdfplumber

from config import settings
from models import DocumentUploadRequest, DocumentProcessingResult

logger = logging.getLogger(__name__)

class DocumentService:
    """Service for document processing and vector storage"""
    
    def __init__(self):
        self.pinecone_client = None
        self.index = None
        self.embeddings = None
        self.vectorstore = None
        self.text_splitter = None
        self.processed_documents = 0
        
    async def initialize(self):
        """Initialize document processing components"""
        try:
            # Initialize OpenAI embeddings
            self.embeddings = OpenAIEmbeddings(
                model=settings.embedding_model,
                openai_api_key=settings.openai_api_key
            )
            
            # Initialize Pinecone
            self.pinecone_client = Pinecone(api_key=settings.pinecone_api_key)
            
            # Check if index exists, create if not
            existing_indexes = [idx.name for idx in self.pinecone_client.list_indexes()]
            
            if settings.pinecone_index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {settings.pinecone_index_name}")
                self.pinecone_client.create_index(
                    name=settings.pinecone_index_name,
                    dimension=settings.vector_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                
            # Connect to index
            self.index = self.pinecone_client.Index(settings.pinecone_index_name)
            
            # Initialize vectorstore
            self.vectorstore = PineconeVectorStore(
                index=self.index,
                embedding=self.embeddings,
                text_key="text"
            )
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
                separators=["\n\n", "\n", " ", ""]
            )
            
            logger.info("Document service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize document service: {e}")
            raise
    
    async def upload_documents(self, request: DocumentUploadRequest) -> Dict[str, Any]:
        """Upload and process documents"""
        results = []
        processed = 0
        
        try:
            logger.info(f"Starting upload of {len(request.documents)} documents")
            
            for i, doc_data in enumerate(request.documents):
                try:
                    logger.info(f"Processing document {i+1}/{len(request.documents)}: {doc_data.get('title', 'Untitled')}")
                    result = await self._process_document(doc_data, request.metadata)
                    results.append(result)
                    
                    if result.status == "success":
                        processed += 1
                        logger.info(f"Successfully processed document: {result.document_id} ({result.chunks_created} chunks)")
                    else:
                        logger.warning(f"Document processing failed: {result.document_id} - {result.error_message}")
                        
                except Exception as e:
                    logger.error(f"Error processing document {doc_data.get('id', 'unknown')}: {e}")
                    results.append(DocumentProcessingResult(
                        document_id=doc_data.get("id", "unknown"),
                        chunks_created=0,
                        status="failed",
                        error_message=str(e)
                    ))
            
            self.processed_documents += processed
            logger.info(f"Upload complete: {processed}/{len(request.documents)} documents processed successfully")
            
            return {
                "processed": processed,
                "total": len(request.documents),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error in document upload: {e}")
            raise
    
    async def _process_document(self, doc_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> DocumentProcessingResult:
        """Process a single document"""
        try:
            document_id = doc_data.get("id")
            title = doc_data.get("title", "Untitled")
            content = doc_data.get("content", "")
            doc_metadata = doc_data.get("metadata", {})
            
            if not document_id or not content:
                raise ValueError("Document ID and content are required")
            
            # Handle PDF content
            if doc_metadata.get("is_pdf", False):
                content = await self._extract_pdf_text(content)
            
            # Split document into chunks
            logger.info(f"Original content length: {len(content)} characters")
            texts = self.text_splitter.split_text(content)
            logger.info(f"Split into {len(texts)} chunks")
            
            if not texts or not any(text.strip() for text in texts):
                raise ValueError("Document content is empty after processing")
            
            # Create Document objects
            documents = []
            for i, text in enumerate(texts):
                chunk_metadata = {
                    "document_id": document_id,
                    "title": title,
                    "chunk_id": f"{document_id}_{i}",
                    "chunk_index": i,
                    "total_chunks": len(texts)
                }
                
                # Add original document metadata
                if doc_metadata:
                    chunk_metadata.update(doc_metadata)
                
                if metadata:
                    chunk_metadata.update(metadata)
                
                documents.append(Document(page_content=text, metadata=chunk_metadata))
            
            # Add to vectorstore
            await self._add_documents_to_vectorstore(documents)
            
            return DocumentProcessingResult(
                document_id=document_id,
                chunks_created=len(texts),
                status="success"
            )
            
        except Exception as e:
            logger.error(f"Error processing document {doc_data.get('id', 'unknown')}: {e}")
            return DocumentProcessingResult(
                document_id=doc_data.get("id", "unknown"),
                chunks_created=0,
                status="failed",
                error_message=str(e)
            )
    
    async def _extract_pdf_text(self, base64_content: str) -> str:
        """Extract text from PDF base64 content"""
        try:
            logger.info("Starting PDF text extraction")
            
            # Decode base64 content
            pdf_bytes = base64.b64decode(base64_content)
            logger.info(f"Decoded PDF: {len(pdf_bytes)} bytes")
            
            # Use pdfplumber for better text extraction
            text_content = []
            try:
                with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                    logger.info(f"PDF has {len(pdf.pages)} pages")
                    for i, page in enumerate(pdf.pages):
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
                            logger.debug(f"Extracted text from page {i+1}: {len(text)} characters")
                        else:
                            logger.warning(f"No text found on page {i+1}")
                
                # Join all pages with double newlines
                full_text = "\n\n".join(text_content)
                logger.info(f"pdfplumber extracted {len(full_text)} characters")
                
            except Exception as e:
                logger.warning(f"pdfplumber failed: {e}, trying PyPDF2")
                full_text = ""
            
            if not full_text.strip():
                # Fallback to PyPDF2 if pdfplumber fails
                logger.info("Trying PyPDF2 as fallback")
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                    text_content = []
                    for i, page in enumerate(pdf_reader.pages):
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
                            logger.debug(f"PyPDF2 extracted text from page {i+1}: {len(text)} characters")
                    full_text = "\n\n".join(text_content)
                    logger.info(f"PyPDF2 extracted {len(full_text)} characters")
                except Exception as e:
                    logger.error(f"PyPDF2 also failed: {e}")
            
            if not full_text.strip():
                raise ValueError("Could not extract text from PDF - both pdfplumber and PyPDF2 failed")
            
            logger.info(f"PDF text extraction successful: {len(full_text)} characters")
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise ValueError(f"Failed to process PDF: {str(e)}")

    async def _add_documents_to_vectorstore(self, documents: List[Document]):
        """Add documents to Pinecone vectorstore"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.vectorstore.add_documents(documents)
            )
            
        except Exception as e:
            logger.error(f"Error adding documents to vectorstore: {e}")
            raise
    
    async def search_similar_documents(self, query: str, k: int = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if k is None:
            k = settings.top_k_results
            
        try:
            # Run similarity search in thread pool
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(
                None,
                lambda: self.vectorstore.similarity_search_with_score(query, k=k)
            )
            
            # Format results
            results = []
            for doc, score in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def delete_document(self, document_id: str):
        """Delete a document from the index"""
        try:
            # Delete all chunks for the document
            filter_dict = {"document_id": document_id}
            self.index.delete(filter=filter_dict)
            
            logger.info(f"Deleted document: {document_id}")
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise
    
    async def get_document_count(self) -> int:
        """Get total number of indexed documents"""
        try:
            stats = self.index.describe_index_stats()
            return stats.get('total_vector_count', 0)
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get document service statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.get('total_vector_count', 0),
                "processed_documents": self.processed_documents,
                "index_fullness": stats.get('index_fullness', 0.0)
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                "total_vectors": 0,
                "processed_documents": self.processed_documents,
                "index_fullness": 0.0
            }
