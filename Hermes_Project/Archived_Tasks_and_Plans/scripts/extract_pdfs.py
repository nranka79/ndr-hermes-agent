import subprocess
import sys
import glob
import os

try:
    import PyPDF2
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
    import PyPDF2

pdf_files = glob.glob('Ruhaan Math Syllabus/*.pdf')
for f in pdf_files:
    try:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            extr = page.extract_text()
            if extr:
                text += extr + "\n"
        with open(f + '.txt', 'w', encoding='utf-8') as out:
            out.write(text)
        print(f"Extracted: {f}")
    except Exception as e:
        print(f"Error extracting {f}: {e}")
