"""
Document processing module for loading, chunking, and vectorizing documents
"""

import os
import logging
from typing import List, Dict, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import Config

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles document loading, processing, and vector database creation"""
    
    def __init__(self, document_paths: Dict[str, str], persist_directory: str):
        self.document_paths = document_paths
        self.persist_directory = persist_directory
        self.loaded_documents = []
        self.vectorstore = None
        
        # Initialize components
        Config.setup_environment()
        self.embeddings = GoogleGenerativeAIEmbeddings(model=Config.EMBEDDING_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            length_function=len
        )
    
    def load_single_document(self, doc_name: str, doc_path: str) -> List:
        """Load and process a single PDF document"""
        try:
            logger.info(f"Loading {doc_name}...")
            
            if not os.path.exists(doc_path):
                logger.warning(f"File not found: {doc_path}")
                return []
            
            # Load PDF
            loader = PyPDFLoader(doc_path)
            documents = loader.load()
            
            if not documents:
                logger.warning(f"No content found in {doc_name}")
                return []
            
            logger.info(f"Loaded {len(documents)} pages from {doc_name}")
            
            # Add metadata
            for doc in documents:
                doc.metadata['document_name'] = doc_name
                doc.metadata['source'] = doc_path
            
            # Split into chunks
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Split into {len(chunks)} chunks")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error loading {doc_name}: {e}")
            return []
    
    def load_all_documents(self) -> tuple:
        """Load all documents and return chunks"""
        all_chunks = []
        successful_docs = []
        
        logger.info("Loading all documents...")
        
        for doc_name, doc_path in self.document_paths.items():
            chunks = self.load_single_document(doc_name, doc_path)
            if chunks:
                all_chunks.extend(chunks)
                successful_docs.append(doc_name)
                logger.info(f"✅ {doc_name}: {len(chunks)} chunks")
            else:
                logger.warning(f"❌ Failed to load {doc_name}")
        
        logger.info(f"Total documents loaded: {len(successful_docs)}")
        logger.info(f"Total chunks: {len(all_chunks)}")
        
        return all_chunks, successful_docs
    
    def create_vector_database(self, document_chunks: List) -> Optional[Chroma]:
        """Create vector database from document chunks"""
        try:
            logger.info(f"Creating vector database with {len(document_chunks)} chunks...")
            
            vectorstore = Chroma.from_documents(
                documents=document_chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory,
                collection_name='multi_doc_collection'
            )
            
            collection_count = vectorstore._collection.count()
            logger.info(f"✅ Vector database created with {collection_count} chunks")
            
            return vectorstore
            
        except Exception as e:
            logger.error(f"Error creating vector database: {e}")
            return None
    
    def load_existing_database(self) -> Optional[Chroma]:
        """Load existing vector database"""
        try:
            logger.info("Loading existing vector database...")
            
            vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name='multi_doc_collection'
            )
            
            collection_count = vectorstore._collection.count()
            if collection_count > 0:
                logger.info(f"✅ Loaded existing database with {collection_count} chunks")
                return vectorstore
            else:
                logger.warning("Existing database is empty")
                return None
                
        except Exception as e:
            logger.info(f"No existing database found: {e}")
            return None
    
    def setup_documents(self) -> bool:
        """Complete document setup process"""
        try:
            # Try to load existing database first
            self.vectorstore = self.load_existing_database()
            
            if self.vectorstore:
                # Load document names from config
                self.loaded_documents = list(self.document_paths.keys())
                logger.info("Using existing vector database")
                return True
            
            # Create new database
            logger.info("Creating new vector database...")
            all_chunks, successful_docs = self.load_all_documents()
            
            if not all_chunks:
                logger.error("No documents loaded successfully")
                return False
            
            self.vectorstore = self.create_vector_database(all_chunks)
            if not self.vectorstore:
                logger.error("Failed to create vector database")
                return False
            
            self.loaded_documents = successful_docs
            logger.info("✅ Document setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in document setup: {e}")
            return False
    
    def test_search(self, query: str, k: int = 3):
        """Test vector search functionality"""
        if not self.vectorstore:
            logger.error("Vector database not available")
            return []
        
        try:
            results = self.vectorstore.similarity_search(query, k=k)
            logger.info(f"Search '{query}' returned {len(results)} results")
            
            for i, result in enumerate(results, 1):
                doc_name = result.metadata.get('document_name', 'Unknown')
                page = result.metadata.get('page', 'Unknown')
                content_preview = result.page_content[:200] + '...'
                logger.info(f"Result {i}: {doc_name} (Page {page})")
            
            return results
            
        except Exception as e:
            logger.error(f"Error testing search: {e}")
            return []