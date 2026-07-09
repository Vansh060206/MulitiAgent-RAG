import os
import sys
import urllib.request
import logging
from app.services.parser import PDFParserService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_sample_pdf(url: str, dest_path: str):
    """Downloads a public sample PDF file for testing."""
    logger.info(f"Downloading sample PDF from: {url}...")
    try:
        # Set a user-agent header to avoid HTTP blocks
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            with open(dest_path, 'wb') as out_file:
                out_file.write(response.read())
        logger.info(f"Sample PDF downloaded successfully to {dest_path}")
    except Exception as e:
        logger.error(f"Failed to download sample PDF: {e}")
        raise e

def test_parser_service():
    print("==================================================")
    print("           Testing PDF Parser Service             ")
    print("==================================================")
    
    sample_pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    local_pdf_path = "backend/sample_dummy.pdf"
    
    try:
        # Download the sample file first
        download_sample_pdf(sample_pdf_url, local_pdf_path)
        
        # Initialize parser service
        service = PDFParserService()
        
        # Test PDF Extraction
        print("\n[TEST] Parsing PDF file...")
        pages = service.parse_pdf(local_pdf_path)
        
        # Assertions
        assert len(pages) > 0, "No pages extracted from PDF"
        print(f"[OK] Successfully extracted {len(pages)} pages.")
        print(f"[INFO] Page 1 preview: '{pages[0]['text'][:100]}...'")
        
        # Test Text Chunking
        print("\n[TEST] Chunking extracted text...")
        chunks, metadata = service.chunk_text(
            pages=pages,
            doc_name="sample_dummy.pdf",
            chunk_size=150,  # Small chunk size to force multiple splits on a single page
            chunk_overlap=30
        )
        
        # Assertions
        assert len(chunks) > 0, "No chunks created"
        assert len(chunks) == len(metadata), "Chunks count and metadata count mismatch"
        print(f"[OK] Successfully generated {len(chunks)} overlapping chunks.")
        
        # Print sample chunk details
        for i in range(min(3, len(chunks))):
            print(f"     Chunk {i+1}: File: {metadata[i]['doc_name']} | Page: {metadata[i]['page_number']}")
            print(f"             Text: '{chunks[i]}'")
            
        # Cleanup sample file
        if os.path.exists(local_pdf_path):
            os.remove(local_pdf_path)
            logger.info("Cleaned up local test PDF file.")
            
        print("\n[SUCCESS] PDF Ingestion & Chunking are fully operational!")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n[FAILED] PDF parser test failed. Error: {e}")
        # Clean up in case of failure
        if os.path.exists(local_pdf_path):
            os.remove(local_pdf_path)
        sys.exit(1)

if __name__ == "__main__":
    test_parser_service()
