import os
from PyPDF2 import PdfReader

pdf_dir = 'pdfs'
text_dir = 'text_docs'

if not os.path.exists(text_dir):
    os.makedirs(text_dir)

for filename in os.listdir(pdf_dir):
    if filename.endswith('.pdf'):
        pdf_path = os.path.join(pdf_dir, filename)
        text_path = os.path.join(text_dir, filename[:-4] + '.txt')

        print(f"Processing {pdf_path}...")
        pdf = PdfReader(pdf_path)
        text_content = ''

        for page in pdf.pages:
            text_content += page.extract_text()

        print(f"Writing text content to {text_path}...")
        with open(text_path, 'w') as text_file:
            text_file.write(text_content)

        print(f"Text content saved to {text_path}")
