"""Helper functions for text processing of schemes data"""

import re

import pandas as pd


def clean_scraped_text(text: str) -> str:
    """
    Helper function to clean scraped text

    Args:
        text (str): scraped text

    Returns
        str: cleaned text
    """

    sentence = re.sub("'", "", text)  # Remove distracting single quotes
    sentence = re.sub(" +", " ", sentence)  # Replace extra spaces
    sentence = re.sub(r"\n: \'\'.*", "", sentence)  # Remove specific unwanted lines
    sentence = re.sub(r"\n!.*", "", sentence)
    sentence = re.sub(r"^:\'\'.*", "", sentence)
    sentence = re.sub(r"\n", " ", sentence)  # Replace non-breaking new lines with space
    sentence = re.sub("[^A-Za-z0-9 @]+", "", sentence)
    return sentence


def dataframe_to_text(df: pd.DataFrame) -> str:
    """
    Function to convert pandas dataframe (of scheme results) to cleaned text

    Args:
        df (pd.DataFrame): schemes in the user query for pandas dataframe

    Returns:
        str: cleaned text of information for each scheme
    """
    text_summary = ""
    for _, row in df.iterrows():
        # Handle both uppercase and lowercase column names
        scheme = row.get("scheme", "")
        agency = row.get("agency", "")
        description = row.get("llm_description", "")
        link = row.get("link", "")
        phone = row.get("phone", "")
        address = row.get("address", "")
        eligibility = row.get("eligibility", "")
        email = row.get("email", "")
        what_it_gives = row.get("what_it_gives", "")
        how_to_apply = row.get("how_to_apply", "")
        service_area = row.get("service_area", "")

        text_summary += f"Scheme Name: {scheme}, Agency: {agency}, Phone: {phone}, Address: {address}, Service Area: {service_area}, Eligibility: {eligibility}, Email: {email}, How to Apply: {how_to_apply}, What it Gives: {what_it_gives}, Description: {description}, Link: {link} \n"
    return text_summary
