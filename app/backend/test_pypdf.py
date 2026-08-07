import pypdf
from pathlib import Path

pdf_path = Path("D:/projects/chatbot-hospital-system/app/backend/data/patients_documents/patient_MRN0001_lab_result.pdf")
reader = pypdf.PdfReader(str(pdf_path))
print("Pages:", len(reader.pages))
print("Text of page 1:")
print(reader.pages[0].extract_text())
