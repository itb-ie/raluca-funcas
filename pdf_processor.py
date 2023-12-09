import pdfplumber
import logging
import os


logger = logging.getLogger()


class PdfProcessor:
    """
    My class that processes multiple column PDF files and extract the text per paragraph
    """
    def __init__(self, filename:str):
        self.filename = filename
        if not os.path.exists(filename):
            logger.error(f"Invalid file path {filename}")
            raise Exception("File not found")
        try:
            self.plumber = pdfplumber.open(self.filename)
            logger.info(f"Successfully loaded file {self.filename} with {len(self.plumber.pages)} pages")
        except Exception as e:
            logger.error(e)
            raise e


