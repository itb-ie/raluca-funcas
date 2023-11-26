import os
import pdfplumber

pdf_file_path = 'REP-2022.pdf'
word_to_search = "diversity"
# Press the green button in the gutter to run the script.
if __name__ == '__main__':


    # Replace 'your_pdf_file.pdf' with the path to your PDF file


    # Create a pdfplumber.PDF object
    if not os.path.exists(f"pdfs/{pdf_file_path.replace('pdf', 'txt')}"):

        pdf = pdfplumber.open(f"pdfs/{pdf_file_path}")

        # Initialize an empty string to store the extracted text
        extracted_text = ''

        # Iterate through each page in the PDF
        for page in pdf.pages:
            # Extract text from the current page
            page_text = page.extract_text()

            # Append the page's text to the overall extracted_text
            extracted_text += page_text

        # Close the PDF file
        pdf.close()

        with open(f"pdfs/{pdf_file_path.replace('pdf', 'txt')}", "w", encoding="utf-8") as f:
            f.write(extracted_text)


    # Print or use the extracted text as needed
    with open(f"pdfs/{pdf_file_path.replace('pdf', 'txt')}", encoding="utf-8") as f:
        extracted_text = f.read()
        print(extracted_text.lower().count(word_to_search))

