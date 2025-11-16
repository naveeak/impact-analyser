"""
RAG Pipeline - Retrieval Augmented Generation for code analysis
"""
import os
import logging
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.callbacks import StreamingStdOutCallbackHandler

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Retrieval Augmented Generation pipeline for code analysis"""
    
    def __init__(self):
        """Initialize RAG components"""
        try:
            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(
                model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                api_key=os.getenv("OPENAI_API_KEY")
            )
            
            # Initialize LLM
            self.llm = ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
                api_key=os.getenv("OPENAI_API_KEY")
            )
            
            # Initialize ChromaDB vector store
            persist_dir = os.getenv("CHROMADB_PERSIST_DIR", "./chroma_db")
            os.makedirs(persist_dir, exist_ok=True)
            
            self.vector_store = Chroma(
                collection_name=os.getenv("CHROMADB_COLLECTION_NAME", "code_analysis"),
                embedding_function=self.embeddings,
                persist_directory=persist_dir
            )
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
                chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
                separators=["\n\n", "\n", " ", ""]
            )
            
            logger.info("RAG Pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG Pipeline: {str(e)}")
            raise
    
    def index_documents(self, documents: List[str], metadata: List[Dict] = None) -> int:
        """
        Index documents in the vector store
        
        Args:
            documents: List of document texts to index
            metadata: List of metadata dictionaries for documents
            
        Returns:
            Number of documents indexed
        """
        try:
            if not documents:
                logger.warning("No documents to index")
                return 0
            
            logger.info(f"Starting indexing of {len(documents)} documents")
            
            # Ensure metadata list matches documents length
            if not metadata:
                metadata = [{}] * len(documents)
            elif len(metadata) != len(documents):
                logger.warning(f"Metadata count ({len(metadata)}) doesn't match documents ({len(documents)})")
                metadata = metadata + [{}] * (len(documents) - len(metadata))
            
            # Split documents into chunks
            doc_objects = []
            for i, (doc_text, meta) in enumerate(zip(documents, metadata)):
                # Split into chunks
                chunks = self.text_splitter.split_text(doc_text)
                
                for j, chunk in enumerate(chunks):
                    meta_with_position = {
                        **meta,
                        "doc_index": i,
                        "chunk_index": j,
                        "total_chunks": len(chunks)
                    }
                    
                    doc_obj = Document(page_content=chunk, metadata=meta_with_position)
                    doc_objects.append(doc_obj)
            
            # Add to vector store
            self.vector_store.add_documents(doc_objects)
            self.vector_store.persist()
            
            logger.info(f"Successfully indexed {len(doc_objects)} chunks from {len(documents)} documents")
            return len(doc_objects)
            
        except Exception as e:
            logger.error(f"Error indexing documents: {str(e)}")
            raise
    
    def retrieve_context(self, query: str, k: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from the vector store
        
        Args:
            query: Query string for semantic search
            k: Number of documents to retrieve
            
        Returns:
            List of retrieved documents with scores
        """
        try:
            if not query or not query.strip():
                logger.warning("Empty query provided")
                return []
            
            k = k or int(os.getenv("TOP_K_RETRIEVAL", "10"))
            
            logger.debug(f"Retrieving {k} documents for query: {query[:100]}")
            
            # Perform similarity search
            results = self.vector_store.similarity_search_with_relevance_scores(query, k=k)
            
            # Format results
            retrieved_docs = []
            for doc, score in results:
                retrieved_docs.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "relevance_score": float(score)
                })
            
            logger.debug(f"Retrieved {len(retrieved_docs)} documents with scores")
            return retrieved_docs
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return []
    
    def generate_response(self, query: str, context: List[Dict] = None, system_prompt: str = None) -> Dict[str, Any]:
        """
        Generate response using LLM with retrieved context
        
        Args:
            query: User query
            context: Retrieved context documents
            system_prompt: System prompt for the LLM
            
        Returns:
            Generated response with metadata
        """
        try:
            # Retrieve context if not provided
            if context is None:
                context = self.retrieve_context(query)
            
            # Build augmented prompt
            augmented_prompt = self._build_augmented_prompt(query, context, system_prompt)
            
            logger.debug(f"Generating response for query: {query[:100]}")
            
            # Generate response
            response = self.llm.invoke(augmented_prompt)
            
            result = {
                "response": response.content if hasattr(response, 'content') else str(response),
                "query": query,
                "context_count": len(context),
                "context_sources": [doc['metadata'] for doc in context]
            }
            
            logger.debug("Response generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "response": f"Error generating response: {str(e)}",
                "query": query,
                "error": True
            }
    
    def _build_augmented_prompt(self, query: str, context: List[Dict], system_prompt: str = None) -> str:
        """
        Build augmented prompt with context
        
        Args:
            query: User query
            context: Retrieved context
            system_prompt: System prompt (optional)
            
        Returns:
            Formatted augmented prompt
        """
        # Default system prompt if not provided
        if not system_prompt:
            system_prompt = """You are an expert software architect analyzing code changes.
            Use the provided context to analyze the code structure and dependencies.
            Provide clear, structured analysis in JSON format."""
        
        # Format context
        context_text = ""
        if context:
            context_text = "Context from codebase:\n"
            for i, doc in enumerate(context, 1):
                relevance = doc.get('relevance_score', 0)
                context_text += f"\n--- Source {i} (Relevance: {relevance:.2f}) ---\n"
                context_text += doc['content'][:500] + "...\n"
        
        # Build full prompt
        full_prompt = f"""{system_prompt}

{context_text}

Question: {query}

Analysis:"""
        
        return full_prompt
    
    def clear_collection(self):
        """Clear all documents from the vector store"""
        try:
            # Delete and recreate collection
            self.vector_store = Chroma(
                collection_name=os.getenv("CHROMADB_COLLECTION_NAME", "code_analysis"),
                embedding_function=self.embeddings,
                persist_directory=os.getenv("CHROMADB_PERSIST_DIR", "./chroma_db")
            )
            logger.info("Vector store cleared")
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        try:
            collection = self.vector_store._collection
            return {
                "collection_name": collection.name,
                "document_count": collection.count(),
                "metadata_schema": collection.metadata_schema if hasattr(collection, 'metadata_schema') else {}
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {}
