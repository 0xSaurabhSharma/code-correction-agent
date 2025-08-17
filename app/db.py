import logging
from typing import Optional
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger(__name__)
class ChromaCompatibleGoogleEmbeddings(GoogleGenerativeAIEmbeddings):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.model
        
class VectorDB:
    """
    A modular class to handle ChromaDB vector database operations.
    It encapsulates the client and collection and is initialized with an embedding function.
    """
    def __init__(self, embedding_function):
        """
        Initializes the VectorDB with a ChromaDB instance.
        
        Args:
            embedding_function: The embedding function to use for the collection.
        """
        self.collection = None
        
        try:
    
            self.collection = Chroma(
                collection_name="bug-reports",
                embedding_function=embedding_function,
            )
            logger.info("✅ Successfully connected to ChromaDB using langchain-chroma.")
        except Exception as e:
            logger.error(f"❌ Failed to connect to ChromaDB or load collection: {e}")
            self.collection = None

    def get_collection(self):
        """Returns the initialized ChromaDB collection."""
        if not self.collection:
            logger.error("Attempted to access collection before successful initialization.")
        return self.collection




# # File: db.py
# import os
# import logging
# from typing import Optional

# # LangChain and Pinecone imports
# from pinecone import Pinecone as PineconeClient, ServerlessSpec
# from langchain_pinecone import PineconeVectorStore

# # Assuming these are available from your project
# from app.settings_loader import settings

# logger = logging.getLogger(__name__)


# # It's recommended to initialize the Pinecone client once at startup
# try:
#     # Use the API key and environment from your settings loader
#     pinecone_client = PineconeClient(
#         api_key=settings.PINECONE_API_KEY,
#         # environment=settings.PINECONE_ENVIRONMENT # Use this for Pod-based indexes
#     )
#     logger.info("✅ Successfully initialized Pinecone client.")
# except Exception as e:
#     logger.error(f"❌ Failed to initialize Pinecone client: {e}")
#     pinecone_client = None


# class VectorDB:
#     """
#     A modular class to handle Pinecone vector database operations.
#     """
#     def __init__(self, embedding_function, index_name: str = "bug-reports"):
#         """
#         Initializes the VectorDB with a Pinecone index.
        
#         Args:
#             embedding_function: The embedding function to use for the collection.
#             index_name: The name of the Pinecone index to connect to.
#         """
#         self.vector_store = None
#         self.embedding_function = embedding_function
#         self.index_name = index_name

#         if not pinecone_client:
#             logger.error("Pinecone client not initialized. Cannot create vector store.")
#             return

#         try:
#             # Get the list of index names and check for the index's existence
#             index_names = pinecone_client.list_indexes().names
#             if self.index_name not in index_names:
#                 raise FileNotFoundError(
#                     f"Pinecone index '{self.index_name}' not found. Please create it first."
#                 )

#             # Connect to the existing index
#             index = pinecone_client.Index(self.index_name)

#             # Initialize the LangChain PineconeVectorStore
#             self.vector_store = PineconeVectorStore(
#                 index=index, 
#                 embedding=self.embedding_function, 
#                 text_key="bug_report"
#             )
#             logger.info(f"✅ Successfully connected to Pinecone index '{self.index_name}'.")

#         except Exception as e:
#             logger.error(f"❌ Failed to connect to Pinecone index: {e}")
#             self.vector_store = None

#     def get_collection(self):
#         """
#         Returns the initialized Pinecone vector store.
#         Note: Pinecone uses a vector store object, not a 'collection' object.
#         """
#         if not self.vector_store:
#             logger.error("Attempted to access vector store before successful initialization.")
#         return self.vector_store