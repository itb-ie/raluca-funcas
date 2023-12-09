from copy import deepcopy
from typing import List, Dict
import re

import logging
import os
import log_config
import pandas as pd

logger = log_config.setup_logger(__name__, logging.DEBUG)


class GenerateGraphs:
    CSV_DIR = "csvs"
    YEARS = list(range(2012, 2023))
    DATAFRAME_COLUMNS = ["Gender Diversity", "Gender Diversity Board", "Gender Diversity Executive"]

    def __init__(self, location: str):
        """
        Initialize the class
        :param location: The location where the pdfs have been decoded into txt
        """
        self.location = location
        self._companies = []
        files = os.listdir(self.location)
        self.files = [f for f in files if f.endswith("txt")]
        self.dfs = {}

    @property
    def companies(self) -> List:
        """
        Property that returns the list of companies that have been analysed
        :return: The list of individual companies
        """
        for f in self.files:
            company = next(iter(f.split("-")))
            if company not in self._companies:
                self._companies.append(company)
        return self._companies

    def extract_values(self, file):
        """
        Extract the needed values for the company
        :param file:
        :return:
        """
        values = []
        with open(f"{self.location}/{file}", encoding="utf8") as f:
            text = f.read()
            for column in self.DATAFRAME_COLUMNS:
                if column == "Gender Diversity":
                    values.append(text.lower().count("gender"))

                gender_pattern = r"\bgender\b"
                woman_pattern = r"\bwom[ae]n\b"
                board_patters = r"\bboard(s)?\b"
                executive_pattern = r"\bexecutiv[a-z]+"
                g_re = re.compile(gender_pattern, re.IGNORECASE)
                w_re = re.compile(woman_pattern, re.IGNORECASE)
                b_re = re.compile(board_patters, re.IGNORECASE)
                e_re = re.compile(executive_pattern, re.IGNORECASE)
                if column == "Gender Diversity Board":
                    value = 0
                    for paragraph in text.split("\n"):
                        if (g_re.search(paragraph) or w_re.search(paragraph)) and b_re.search(paragraph):
                            value += 1
                    values.append(value)
                if column == "Gender Diversity Executive":
                    value = 0
                    for paragraph in text.split("\n"):
                        if (g_re.search(paragraph) or w_re.search(paragraph)) and e_re.search(paragraph):
                            value += 1
                    values.append(value)
        return values

    def update_df(self, file: str, company: str, add_empty=False):
        """
        Updates the dataframe for that particular company with the results
        :param file:
        :param year:
        :return:
        """
        if company not in self.dfs:
            self.dfs[company] = pd.DataFrame(columns=self.DATAFRAME_COLUMNS)
        if add_empty:
            new_row = pd.DataFrame([{c: 0 for c in self.DATAFRAME_COLUMNS}])
            self.dfs[company] = pd.concat([self.dfs[company], new_row], ignore_index=True)
            return
        values = self.extract_values(file)
        new_row = pd.DataFrame([{c: val for c, val in zip(self.DATAFRAME_COLUMNS, values)}])
        self.dfs[company] = pd.concat([self.dfs[company], new_row], ignore_index=True)

    def generate_csvs_for_company(self, company_name: str):
        """

        :param company_name:
        :return:
        """
        company_files = [f for f in self.files if company_name in f]
        for year in self.YEARS:
            for file in company_files:
                if str(year) in file:
                    # found the file for that particular year
                    logger.debug(f"Found data for company {company_name} for year {year}")
                    self.update_df(file, company_name)
                    break
            else:
                logger.debug(f"Did not find data for company {company_name} for year {year}")
                self.update_df(None, company_name, add_empty=True)

        self.dfs[company_name].to_csv(f"{self.CSV_DIR}/{company_name}.csv")