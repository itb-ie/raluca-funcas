from copy import deepcopy
from typing import List, Dict, Union
import re

import logging
import os
import log_config
import pandas as pd
import matplotlib.pyplot as plt

logger = log_config.setup_logger(__name__, logging.DEBUG)


class GenerateGraphs:
    CSV_DIR = "csvs"
    YEARS = list(range(2012, 2023))
    DATAFRAME_COLUMNS = {
        "gender": ["Gender", "Gender/Woman Board", "Gender/Woman Executive"],
        "inclusivity": ["Inclusivity", "Inclusivity Board", "Inclusivity Executive"],
        "sustainability": ["Sustainability", "Sustainability Board", "Sustainability Executive"],
        "esg": ["ESG", "ESG Board", "ESG Executive"]
    }

    REGEX_PATTERNS = {
        "gender": [r"\bgender[a-z]*\b", r"\bwom[ae]n\b", r"\bboard(s)?\b", r"\bexecutiv[a-z]+"],
        "inclusivity": [r"\binclusiv[a-z]+\b", r"\bboard(s)?\b", r"\bexecutiv[a-z]+"],
        "sustainability": [r"\bsustain[a-z]+\b", r"\bboard(s)?\b", r"\bexecutiv[a-z]+"],
        "esg": [r"\besg\b", r"\bboard(s)?\b", r"\bexecutiv[a-z]+"]
    }

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

    def extract_values(self, file: str, key: str) -> List:
        """
        Extract the needed values for the company
        :param file: The name of the file containing the PDF decoded into txt format
        :param key: The key for the dataframe determining the search terms
        :return: A list of values for the company
        """
        values = []
        for idx in range(3):
            if len(self.REGEX_PATTERNS[key]) == 4:
                main_pattern = re.compile(self.REGEX_PATTERNS[key][0], re.IGNORECASE)
                secondary_pattern = re.compile(self.REGEX_PATTERNS[key][1], re.IGNORECASE)
                board_pattern = re.compile(self.REGEX_PATTERNS[key][2], re.IGNORECASE)
                executive_pattern = re.compile(self.REGEX_PATTERNS[key][3], re.IGNORECASE)
            else:
                main_pattern = re.compile(self.REGEX_PATTERNS[key][0], re.IGNORECASE)
                secondary_pattern = None
                board_pattern = re.compile(self.REGEX_PATTERNS[key][1], re.IGNORECASE)
                executive_pattern = re.compile(self.REGEX_PATTERNS[key][2], re.IGNORECASE)

            with open(f"{self.location}/{file}", encoding="utf8") as f:
                text = f.read()
                value = 0
                for paragraph in text.split("\n"):
                    if idx == 0:
                        # first column, just a simple count for the main pattern
                        value += len(main_pattern.findall(paragraph))
                    elif idx == 1:
                        # second column, if secondary pattern is None, then just a simple count for the main + board pattern
                        # else, count the main + secondary + board pattern
                        if secondary_pattern is None:
                            if main_pattern.search(paragraph) and board_pattern.search(paragraph):
                                value += 1
                        else:
                            if (main_pattern.search(paragraph) or secondary_pattern.search(paragraph)) and board_pattern.search(paragraph):
                                value += 1
                    elif idx == 2:
                        # third column, if secondary pattern is None, then just a simple count for the main + executive pattern
                        # else, count the main + secondary + executive pattern
                        if secondary_pattern is None:
                            if main_pattern.search(paragraph) and executive_pattern.search(paragraph):
                                value += 1
                        else:
                            if (main_pattern.search(paragraph) or secondary_pattern.search(paragraph)) and executive_pattern.search(paragraph):
                                value += 1
                values.append(value)

        return values

    def update_df(self, file: Union[str, None], company: str, year: int, add_empty=False):
        """
        Updates the dataframe for that particular company with the results
        :param file: The name of the file containing the PDF decoded into txt format
        :param company: The name of the company file in the PDF file, eg REP for REPSOL
        :param year: The year as coded in the PDF file name
        :param add_empty: bool to add an empty row of Zeroes if there is no PDF for that company that year
        """
        for key in self.DATAFRAME_COLUMNS:
            df_id = f"{key}-{company}"
            if df_id not in self.dfs:
                self.dfs[df_id] = pd.DataFrame(columns=self.DATAFRAME_COLUMNS[key], index=self.YEARS)
            if add_empty:
                self.dfs[df_id].loc[year] = 0
                continue
            values = self.extract_values(file, key)
            self.dfs[df_id].loc[year] = values
        return

    def generate_csvs_for_company(self, company_name: str):
        """
        Generates the CSV files for the company, based on the self.REGEX_PATTERNS and saves them in the CSV_DIR
        :param company_name: The name of the company
        :return:
        """
        company_files = [f for f in self.files if company_name in f]
        for year in self.YEARS:
            for file in company_files:
                if str(year) in file:
                    # found the file for that particular year
                    logger.debug(f"Found data for company {company_name} for year {year}")
                    self.update_df(file, company_name, year)
                    break
            else:
                logger.debug(f"Did not find data for company {company_name} for year {year}")
                self.update_df(None, company_name, year, add_empty=True)

        for df_id in self.dfs:
            if company_name in df_id:
                self.dfs[df_id].to_csv(f"{self.CSV_DIR}/{df_id}.csv")

    def generate_graphs(self, company_name: str):
        """
        Generates the graph for the company
        :param company_name: The name of the company
        """
        files = os.listdir(self.CSV_DIR)
        files = [f for f in files if f.endswith("csv") and company_name in f]
        for file in files:
            df = pd.read_csv(f"{self.CSV_DIR}/{file}", index_col=0)
            # Plotting the graph
            plt.figure(figsize=(10, 6))  # You can change the figure size as needed
            # Loop through each column (except the index) and plot
            for column in df.columns:
                plt.plot(df.index, df[column], marker='o', label=column)
            # Adding labels and title
            plt.xlabel('Year')
            plt.ylabel('Values')
            plt.title(f'{company_name} Data Over Years')
            plt.legend()
            plt.grid(True)
            # Save the figure
            plt.savefig(f"{self.CSV_DIR}/{file.split('.csv')[0]}_graph.jpg")

    def analyse_and_plot_data_for_company(self, company_name: str, force_generate: bool = False):
        """
        Main function in the class, that does the following:
        1. Gets the files and searches for the key terms
        2. Puts the results into CSV files
        3. Create graphs based on the CSV data
        4. Populate doc files with these graphs
        :param company_name: String identifing the company, same as in the PDF file, REP for Reposol
        :param force_generate: bool, set to True to generate the CSV even is found
        """
        if not os.path.exists(f"{self.CSV_DIR}/{company_name}.csv") or force_generate:
            logger.info(f"Generating based on txt files for company {company_name}")
            self.generate_csvs_for_company(company_name)
        else:
            logger.info(f"The CSV data for company {company_name} is already generated")

        self.generate_graphs(company_name)

