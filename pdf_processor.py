from copy import deepcopy
from typing import List, Dict

import pdfplumber
from pdfplumber.page import Page
import logging
import os
import log_config

logger = log_config.setup_logger(__name__, logging.DEBUG)

class PdfProcessor:
    """
    My class that processes multiple column PDF files and extract the text per paragraph
    """
    # play with these values
    CUTOFF_X = 14
    CUTOFF_Y = 4
    CUTOFF_COL = 14
    PUNCTUATION = ".!?"

    def __init__(self, filename: str):
        self.extracted_text = ""
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
        else:
            self.pages = self.plumber.pages

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
                if word['x0'] - prev_word[0]['x1'] < PdfProcessor.CUTOFF_X:
                    # determine the column index of this word:
                    if word['x0'] - prev_word[0]['x1'] > 0:
                        idx = prev_word[1]
                    else:
                        # we are starting from a new line, need to determine the column:
                        for i, c in enumerate(columns):
                            if not c:
                                continue
                            if abs(word['x0'] - c[0]['x0']) < PdfProcessor.CUTOFF_COL:
                                idx = i
                                break
                        else:
                            # it is a new column, add it
                            # if it is before existing columns, re-order them
                            idx = len(columns) - 1  # Default index if no reordering is needed
                            for i, column in enumerate(columns[:-1]):
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
                        if abs(word['x0'] - c[0]['x0']) < PdfProcessor.CUTOFF_COL:
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

        def extract_paragraphs(columns: List[Dict]) -> List[Dict]:
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
                    if paragraphs[-1] and word["top"] - paragraphs[-1][-1]["bottom"] > PdfProcessor.CUTOFF_Y:
                        # need to add a new paragraph
                        paragraphs.append([])
                    paragraphs[-1].append(word)

            # check if there is a potential multi-column paragraph
            for p in paragraphs:
                if p[0]['text'].islower():
                    logger.debug(f"Found potential multi-column paragraph starting with {p[0]['text']}")
                    for parent in paragraphs:
                        if parent == p:
                            logger.debug("Was not able the identify the parent of this paragraph")
                            break
                        if len(parent) > 20 and parent[-1]['text'][-1] not in PdfProcessor.PUNCTUATION:
                            logger.debug(f"Found potential parent paragraph: {' '.join([w['text'] for w in parent])}")

                            parent.extend(p)
                            paragraphs.remove(p)
                            break
            return paragraphs

        def paragraphs_to_text(paragraphs: List[Dict]):
            """
            Convert the list of Word paragraphs into plain text
            :param paragraphs: The list of paragraphs containing words
            """
            # convert the paragraphs into text paragraphs
            self.extracted_text += f"\n=={str(page)}==\n\n"
            for p in paragraphs:
                words = [w["text"] for w in p]
                paragaph_text = " ".join(words) + "\n"
                self.extracted_text += paragaph_text

        logger.info(f"Processing page {str(page)} from {self.filename}")
        # Extract text from the current page
        words = page.extract_words()
        columns = extract_columns(words)
        paragraphs = extract_paragraphs(columns)
        paragraphs_to_text(paragraphs)
