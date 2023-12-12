from copy import deepcopy
from typing import List, Dict

import pdfplumber
from pdfplumber.page import Page
import logging
import os
import log_config

logger = log_config.setup_logger(__name__, logging.WARNING)

CUTOFFS = {
    "REP": {"CUTOFF_X": 14, "CUTOFF_Y": 4, "CUTOFF_COL": 14},
    "MTS": {"CUTOFF_X": 5, "CUTOFF_Y": 7, "CUTOFF_COL": 5},
    "ABE": {"CUTOFF_X": 14, "CUTOFF_Y": 4, "CUTOFF_COL": 14},
    "ANA": {"CUTOFF_X": 14, "CUTOFF_Y": 4, "CUTOFF_COL": 14},
    "ANE": {"CUTOFF_X": 14, "CUTOFF_Y": 4, "CUTOFF_COL": 14},
    "AMS": {"CUTOFF_X": 14, "CUTOFF_Y": 4, "CUTOFF_COL": 14},
    "BBVA": {"CUTOFF_X": 14, "CUTOFF_Y": 7, "CUTOFF_COL": 14},
    "default": {"CUTOFF_X": 14, "CUTOFF_Y": 5, "CUTOFF_COL": 14},
}


class PdfProcessor:
    """
    My class that processes multiple column PDF files and extract the text per paragraph
    """
    PUNCTUATION = ".!?\""

    def __init__(self, filename: str):
        self.extracted_text = ""
        self.filename = filename
        self.paragraphs = []
        self.previous_page_paragraphs = []
        if not os.path.exists(filename):
            logger.error(f"Invalid file path {filename}")
            raise Exception("File not found")
        try:
            self.plumber = pdfplumber.open(self.filename)
            logger.info(f"Successfully loaded file {self.filename} with {len(self.plumber.pages)} pages")
        except Exception as e:
            logger.error(e)
            raise e
        else:
            self.pages = self.plumber.pages
        dict_key = filename.split("/")[-1].split("-")[0]
        if dict_key in CUTOFFS:
            self.CUTOFF_X = CUTOFFS[dict_key]["CUTOFF_X"]
            self.CUTOFF_Y = CUTOFFS[dict_key]["CUTOFF_Y"]
            self.CUTOFF_COL = CUTOFFS[dict_key]["CUTOFF_COL"]
        else:
            self.CUTOFF_X = CUTOFFS["default"]["CUTOFF_X"]
            self.CUTOFF_Y = CUTOFFS["default"]["CUTOFF_Y"]
            self.CUTOFF_COL = CUTOFFS["default"]["CUTOFF_COL"]

    def process_page(self, page: Page):
        """
        Extract the text content of a pdf page, by taking into account the columns as all
        :param page: the pdf plumber object
        :return:
        """
        def extract_columns(words: List[Dict]) -> List[Dict]:
            """
            Helper function to extract all the columns from a PDF page
            :param words: a list of wor
            :return: the list of words columns
            """
            if not words:
                return []
            columns = [[]]
            prev_word = (deepcopy(words[0]), 0)
            prev_word[0]['x1'] = words[0]['x0'] - 1
            for word in words:
                # if word['text'] == 'prices':
                #     print("stay")
                if word['x0'] - prev_word[0]['x1'] < self.CUTOFF_X:
                    # determine the column index of this word:
                    if word['x0'] - prev_word[0]['x1'] > 0:
                        idx = prev_word[1]
                    else:
                        # we are starting from a new line, need to determine the column:
                        for i, c in enumerate(columns):
                            if not c:
                                continue
                            if abs(word['x0'] - c[0]['x0']) < self.CUTOFF_COL:
                                idx = i
                                break
                        else:
                            # it is a new column, add it
                            # if it is before existing columns, re-order them
                            idx = len(columns) - 1  # Default index if no reordering is needed
                            for i, column in enumerate(columns):
                                if word['x0'] < column[0]['x0']:
                                    columns.insert(i, [])
                                    idx = i
                                    break
                    columns[idx].append(word)
                else:
                    # new column, need to match with existing columns first
                    for cindex, c in enumerate(columns):
                        if cindex < prev_word[1]:
                            continue
                        if abs(word['x0'] - c[0]['x0']) < self.CUTOFF_COL:
                            idx = cindex
                            break
                    else:
                        columns.append([])
                        idx = 0
                        # we added a column in the middle, need to reshuffle
                        for cindex in range(len(columns) - 1, -1, -1):
                            if columns[cindex - 1][0]['x0'] > word['x0']:
                                columns[cindex] = columns[cindex - 1]
                            else:
                                idx = cindex
                                break
                        columns[idx] = []
                    columns[idx].append(word)
                prev_word = (word, idx)
            return columns

        def extract_paragraphs(columns: List[Dict]) -> List[List]:
            """
            Helper function that puts the words in columns into paragraphs
            :param columns: the list of columns that was determined before
            :return: a list of paragraphs
            """
            # decode columns to paragraphs
            paragraphs = []
            for column in columns:
                if not column:
                    continue
                paragraphs.append([])
                for word in column:
                    if paragraphs[-1] and word["top"] - paragraphs[-1][-1]["bottom"] > self.CUTOFF_Y:
                        # need to add a new paragraph
                        paragraphs.append([])
                    paragraphs[-1].append(word)

            # check if there is a potential multi-column paragraph
            for p in paragraphs:
                if p[0]['text'].islower():
                    logger.debug(f"Found potential multi-column paragraph starting with: '{p[0]['text']}'")
                    prev_paragraphs = []
                    for pre in paragraphs:
                        if pre == p:
                            break
                        prev_paragraphs.append(pre)
                    prev_paragraphs = prev_paragraphs[::-1]
                    for parent in prev_paragraphs:
                        if len(parent) > 10 and parent[-1]['text'][-1] not in PdfProcessor.PUNCTUATION and \
                                abs((parent[-1]["bottom"] - parent[-1]["top"]) - (p[0]["bottom"] - p[0]["top"])) < 0.1:
                            logger.debug(f"Found potential parent paragraph: {' '.join([w['text'] for w in parent])}")
                            parent.extend(p)
                            paragraphs.remove(p)
                            break
                    else:
                        for prev_p in self.previous_page_paragraphs[::-1]:
                            if len(prev_p) > 10 and prev_p[-1]['text'][-1] not in PdfProcessor.PUNCTUATION and \
                                    prev_p[-1]["bottom"] - prev_p[-1]["top"] == p[0]["bottom"] - p[0]["top"]:
                                logger.debug(
                                    f"Found potential parent paragraph on previous page: {' '.join([w['text'] for w in prev_p])}")
                                prev_p.extend(p)
                                paragraphs.remove(p)
                                break
                        else:
                            logger.debug("Was not able the identify the parent of this paragraph")
            return paragraphs

        logger.info(f"Processing page {str(page)} from {self.filename}")
        # Extract text from the current page
        words = page.extract_words()
        columns = extract_columns(words)
        if self.paragraphs:
            self.previous_page_paragraphs = self.paragraphs[-1]
        self.paragraphs.append([])
        self.paragraphs[-1] = extract_paragraphs(columns)
        # paragraphs_to_text(self.paragraphs)

    def paragraphs_to_text(self):
        """
        Convert the list of Word paragraphs into plain text
        """
        # convert the paragraphs into text paragraphs
        for idx, page_para in enumerate(self.paragraphs):
            self.extracted_text += f"\n==Page{idx+1}==\n\n"
            for p in page_para:
                words = [w["text"] for w in p]
                paragraph_text = " ".join(words) + "\n"
                self.extracted_text += paragraph_text

    def process_file(self):
        """
        Decodes the entire pdf file and saves the result
        """
        for page in self.pages:
            self.process_page(page)
        self.paragraphs_to_text()

        with open(f"{self.filename.replace('pdf', 'txt')}", "w", encoding="utf-8") as f:
            f.write(self.extracted_text)
