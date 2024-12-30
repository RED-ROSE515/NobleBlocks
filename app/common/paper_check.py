from openai import OpenAI
from spire.pdf import PdfDocument
from spire.pdf import PdfTextExtractOptions
from spire.pdf import PdfTextExtractor
from app.common.secrets import secrets
import os

client = OpenAI(api_key=secrets.apiKey)
pdf = PdfDocument()

def analyze_paper(text):
    response = client.chat.completions.create(
        model="o1-preview",
        messages=[
            {
                "role": "user",
                "content": f"I have a scientific paper that I would like to analyze these papers and identify any errors and give me the solution for each error. These errors could be in calculations, logic, methodology, data interpretation, or even formatting. This is the full paper: " + text
            }
        ]
    )
    return response.choices[0].message.content

def extract_text_from_pdf(file_path):
    extract_options = PdfTextExtractOptions()
    extracted_text = ""
    if os.path.exists(file_path):
        pdf.LoadFromFile(file_path)
        for i in range(pdf.Pages.Count):
            page = pdf.Pages.get_Item(i)
            text_extractor = PdfTextExtractor(page)
            text = text_extractor.ExtractText(extract_options)
            extracted_text += text
        cleaned_text = extracted_text.replace("Evaluation Warning : The document was created with Spire.PDF for Python.", "")
    else:
        print(f"File not found: {file_path}")
        return ""
    return cleaned_text

def check_paper(file_path):
    text = extract_text_from_pdf(file_path)
    results = analyze_paper(text)
    return results
