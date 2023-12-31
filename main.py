import os
import logging
from pdf_processor import PdfProcessor
from graph_generator import GenerateGraphs
import log_config

logger = log_config.setup_logger(__name__, logging.DEBUG)


# pdf_file_path = 'files/REP-2022.pdf'
pdf_dir = "files"


def decoded_file_exists(pdf_file: str) -> bool:
    txt_file = pdf_file.replace("pdf", "txt")
    return os.path.exists(txt_file)


def check_and_decode_new_files():
    """
    Checks is new PDFs have been added, opens and decodes them
    """
    pdfs = os.listdir(pdf_dir)
    pdfs = [f"{pdf_dir}/{f}" for f in pdfs if f.endswith("pdf")]
    for pdf in pdfs:
        if not decoded_file_exists(pdf):
            logger.info(f"Found new file {pdf} that needs to be decoded")
            proc = PdfProcessor(pdf)
            proc.process_file()


if __name__ == '__main__':
    logger.info("Attempting to find and decode new files (if any)")
    check_and_decode_new_files()

    logger.info("Generating the graphs per company")
    graphs = GenerateGraphs(pdf_dir)
    for company in graphs.companies:
        graphs.analyse_and_plot_data_for_company(company, force_generate=False)
    # in the end need to generate the aggregated doc with all the companies
    graphs.generate_aggregated_doc()
