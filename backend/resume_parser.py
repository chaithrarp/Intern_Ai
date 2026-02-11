import os
import PyPDF2
import docx
from typing import Dict, Optional
import re

class ResumeParser:
    """Handles resume upload and text extraction"""
    
    def __init__(self, upload_folder: str = "resume_uploads"):
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
            return text
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            print(f"Error extracting DOCX: {e}")
            return ""
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error extracting TXT: {e}")
            return ""
    
    def parse_resume(self, file_path: str) -> Dict[str, any]:
        """Parse resume and extract text based on file type"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        text = ""
        if file_extension == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_extension == '.docx' or file_extension == '.doc':
            text = self.extract_text_from_docx(file_path)
        elif file_extension == '.txt':
            text = self.extract_text_from_txt(file_path)
        else:
            return {"success": False, "error": "Unsupported file format"}
        
        if not text.strip():
            return {"success": False, "error": "Could not extract text from resume"}
        
        # Extract key sections (optional enhancement)
        parsed_data = {
            "success": True,
            "raw_text": text,
            "summary": self._create_summary(text),
            "file_path": file_path
        }
        
        return parsed_data
    
    def _create_summary(self, text: str) -> str:
        """Create a brief summary of the resume for context"""
        # Simple summary - first 500 characters
        return text[:500] + "..." if len(text) > 500 else text
    
    def save_uploaded_file(self, file, session_id: str) -> str:
        """Save uploaded file and return path"""
        filename = f"{session_id}_{file.filename}"
        file_path = os.path.join(self.upload_folder, filename)
        file.save(file_path)
        return file_path