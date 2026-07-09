import os
import logging
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class PDFParserService:
    """
    PDF Parsing & Document Chunking Service.
    Extracts text page-by-page (using pypdf or LlamaParse if API key exists)
    and segments the text recursively to maintain paragraph and sentence bounds.
    """
    def __init__(self):
        # Optional layout-aware parser credentials
        self.llama_api_key = os.getenv("LLAMA_CLOUD_API_KEY")
        if self.llama_api_key:
            logger.info("LlamaParse API Key detected. Layout-aware parsing is enabled.")
        else:
            logger.info("LlamaParse API Key not set. Defaulting to local PyPDF parser.")

    def parse_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parses a PDF file and returns text extracted page-by-page.
        
        Inputs:
            file_path: str - Path to the PDF file on disk.
        Outputs:
            List[Dict[str, Any]] - List of pages, e.g., [{"text": "...", "page_number": 1}]
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
            
        pages = []
        
        # If LlamaParse key is configured, utilize layout-aware vision parsing
        if self.llama_api_key:
            try:
                from llama_parse import LlamaParse
                # LlamaParse handles tables, columns, and visual structures by compiling to markdown
                parser = LlamaParse(
                    api_key=self.llama_api_key,
                    result_type="markdown",
                    verbose=True
                )
                logger.info(f"Uploading {file_path} to LlamaParse...")
                documents = parser.load_data(file_path)
                
                # Process the returned pages
                for idx, doc in enumerate(documents, start=1):
                    pages.append({
                        "text": doc.text,
                        # LlamaParse returns pages sequentially
                        "page_number": idx
                    })
                logger.info(f"LlamaParse completed. Extracted {len(pages)} pages.")
                return pages
            except Exception as e:
                logger.warning(f"LlamaParse failed. Falling back to local PyPDF. Error: {e}")
                
        # Default local PyPDF extraction (Fast, free, and runs on CPU offline)
        try:
            logger.info(f"Parsing {file_path} using local PyPDF parser...")
            reader = PdfReader(file_path)
            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text:
                    # Basic whitespace cleanup to remove redundant line-breaks
                    clean_text = " ".join(text.split())
                    pages.append({
                        "text": clean_text,
                        "page_number": idx
                    })
            logger.info(f"PyPDF completed. Extracted {len(pages)} pages.")
        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path} using PyPDF: {e}")
            raise e
            
        return pages

    def chunk_text(
        self, 
        pages: List[Dict[str, Any]], 
        doc_name: str, 
        chunk_size: int = 600, 
        chunk_overlap: int = 120
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Partitions page text list into overlapping semantic chunks, tracking page numbers.
        
        Inputs:
            pages: List[Dict[str, Any]] - Extracted pages with page numbers.
            doc_name: str - Filename for citation.
            chunk_size: int - Max character length per chunk (default 600).
            chunk_overlap: int - Character overlap size (default 120).
        Outputs:
            Tuple[List[str], List[Dict[str, Any]]] - List of chunk texts, and matching metadata dicts.
        """
        chunks_list = []
        metadata_list = []
        
        # Initialize LangChain's recursive splitter.
        # It attempts to split on paragraphs (\n\n), then lines (\n), then words ( ),
        # preserving semantic structures within the chunk bounds.
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        for page_data in pages:
            text = page_data["text"]
            page_num = page_data["page_number"]
            
            if not text.strip():
                continue
                
            # Split the single page text into chunks
            page_chunks = splitter.split_text(text)
            
            for chunk in page_chunks:
                chunks_list.append(chunk)
                # Formulate structural metadata for citation highlighting
                metadata_list.append({
                    "doc_name": doc_name,
                    "page_number": page_num
                })
                
        logger.info(f"Chunking complete. Created {len(chunks_list)} chunks from {doc_name}.")
        return chunks_list, metadata_list
