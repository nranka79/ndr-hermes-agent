import subprocess
import sys
import glob

try:
    import fitz  # PyMuPDF
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyMuPDF"])
    import fitz

pdf_files = glob.glob('Ruhaan Math Syllabus/*.pdf')
for f in pdf_files:
    try:
        doc = fitz.open(f)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        with open(f + '.txt', 'w', encoding='utf-8') as out:
            out.write(text)
        print(f"PyMuPDF Extracted: {f}")
    except Exception as e:
        print(f"Error extracting {f}: {e}")
