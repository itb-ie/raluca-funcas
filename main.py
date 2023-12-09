import os
import pdfplumber
import logging
from pdf_processor import PdfProcessor
import log_config

logger = log_config.setup_logger(__name__, logging.DEBUG)


pdf_file_path = 'REP-2022.pdf'
word_to_search = "diversity"



if __name__ == '__main__':
    proc = PdfProcessor("pdfs/REP-2022.pdf")
    for page in proc.pages[20:40]:
        proc.process_page(page)

    with open(f"pdfs/{pdf_file_path.replace('pdf', 'txt')}", "w", encoding="utf-8") as f:
        f.write(proc.extracted_text)

    exit()

    # Replace this condition to not extract all the time:
    # if not os.path.exists(f"pdfs/{pdf_file_path.replace('pdf', 'txt')}"):
    if 1:
        extracted_text = ""
        pdf = pdfplumber.open(f"pdfs/{pdf_file_path}")
        logger.info(f"Processing file {pdf_file_path} with {len(pdf.pages)} pages")

        # Iterate through each page in the PDF
        for page in pdf.pages:
            logger.info(f"Processing page {str(page)}")
            # Initialize an empty string to store the extracted text
            paragraphs = []
            # Extract text from the current page
            page_text = page.extract_text()
            words = page.extract_words()

            # Append the page's text to the overall extracted_text
            columns = [[]]
            prev_word = None
            for word in words:
                # if word['text'] == 'Statement"':
                #     print("stay")
                if not prev_word or word['x0'] - prev_word[0]['x1'] < cutoff_x:
                    # determine the column index of this word:
                    if not prev_word:
                        idx = 0
                    elif word['x0'] - prev_word[0]['x1'] > 0:
                        idx = prev_word[1]
                    else:
                        # we are starting from a new line, need to determine the column:
                        for i, c in enumerate(columns):
                            if not c:
                                continue
                            if abs(word['x0'] - c[0]['x0']) < cutoff_col:
                                idx = i
                                break
                        else:
                            # it is a new column, add it
                            columns.append([])
                            # if it is before existing columns, re-order them
                            for i, c in enumerate(columns[:-1]):

                                if word['x0'] < columns[i][0]['x0']:
                                    for cindex in range(len(columns) - 1, i, -1):
                                        columns[cindex] = columns[cindex-1]
                                    columns[i] = []
                                    idx = i
                                    break
                            else:
                                idx = len(columns) - 1

                    columns[idx].append(word)
                else:
                    # new column, need to match with existing columns first
                    for cindex, c in enumerate(columns):
                        if cindex < prev_word[1]:
                            continue
                        if abs(word['x0'] - c[0]['x0']) < cutoff_col:
                            idx = cindex
                            break
                    else:
                        columns.append([])
                        idx = 0
                        # we added a column in the middle, need to reshuffle
                        for cindex in range(len(columns) - 1, -1, -1):
                            if columns[cindex-1][0]['x0'] > word['x0']:
                                columns[cindex] = columns[cindex - 1]
                            else:
                                idx = cindex
                                break
                        columns[idx] = []
                    columns[idx].append(word)
                prev_word = (word, idx)

            # decode columns to paragraphs
            for column in columns:
                if not column:
                    continue
                paragraphs.append([])
                for word in column:
                    if paragraphs[-1] and word["top"] - paragraphs[-1][-1]["bottom"] > cutoff_y:
                        # need to add a new paragraph
                        paragraphs.append([])
                    paragraphs[-1].append(word)

            # convert the paragraphs into text paragraphs
            extracted_text += f"\n=={str(page)}==\n\n"
            for p in paragraphs:
                words = [w["text"] for w in p]
                paragaph_text = " ".join(words) + "\n"
                extracted_text += paragaph_text

        # Close the PDF file
        pdf.close()

        with open(f"pdfs/{pdf_file_path.replace('pdf', 'txt')}", "w", encoding="utf-8") as f:
            f.write(extracted_text)


    # Print or use the extracted text as needed
    with open(f"pdfs/{pdf_file_path.replace('pdf', 'txt')}", encoding="utf-8") as f:
        extracted_text = f.read()
        print(extracted_text.lower().count(word_to_search))

