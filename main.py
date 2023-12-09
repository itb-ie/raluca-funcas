import os
import logging
from pdf_processor import PdfProcessor
import log_config

logger = log_config.setup_logger(__name__, logging.DEBUG)


pdf_file_path = 'files/REP-2022.pdf'
word_to_search = "diversity"


def decoded_file_exists(pdf_file: str) -> bool:
    txt_file = pdf_file.replace("pdf", "txt")
    return os.path.exists(txt_file)


if __name__ == '__main__':
    if not decoded_file_exists(pdf_file_path):
        logger.info(f"File does not exists, decoding file {pdf_file_path}")
        proc = PdfProcessor(pdf_file_path)
        for page in proc.pages:
            proc.process_page(page)

        with open(f"{pdf_file_path.replace('pdf', 'txt')}", "w", encoding="utf-8") as f:
            f.write(proc.extracted_text)
    else:
        logger.info(f"Already decoded {pdf_file_path}")
