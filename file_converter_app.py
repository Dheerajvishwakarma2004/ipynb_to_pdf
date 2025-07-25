import streamlit as st
from PIL import Image
from fpdf import FPDF
import nbformat
from nbconvert import PDFExporter
import pandas as pd
from pdf2image import convert_from_path
import os
import tempfile
from io import BytesIO
from docx import Document
from markdown import markdown
from weasyprint import HTML

st.set_page_config(page_title="Universal File Converter", layout="centered")
st.title("📁 Universal File Converter")

# ----------------- Conversion Functions -----------------
def convert_image_to_format(image, target_format):
    img = Image.open(image)
    buffered = BytesIO()
    img.convert("RGB").save(buffered, format=target_format)
    return buffered.getvalue()

def convert_ipynb_to_pdf(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ipynb") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp.flush()
        exporter = PDFExporter()
        body, _ = exporter.from_filename(tmp.name)
        return body

def convert_text_to_pdf(text_file):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    text = text_file.read().decode("utf-8")
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, txt=line)
    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()

def convert_docx_to_pdf(file):
    document = Document(file)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for para in document.paragraphs:
        pdf.multi_cell(0, 10, para.text)
    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()

def convert_csv_to_xlsx(file):
    df = pd.read_csv(file)
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    return output.getvalue()

def convert_xlsx_to_csv(file):
    df = pd.read_excel(file, engine='openpyxl')
    output = BytesIO()
    df.to_csv(output, index=False)
    return output.getvalue()

def convert_json_to_csv(json_file):
    df = pd.read_json(json_file)
    output = BytesIO()
    df.to_csv(output, index=False)
    return output.getvalue()

def convert_csv_to_json(csv_file):
    df = pd.read_csv(csv_file)
    output = BytesIO()
    df.to_json(output, orient='records', lines=True)
    return output.getvalue()

def convert_pdf_to_images(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.getvalue())
        tmp.flush()
        images = convert_from_path(tmp.name)
        img_buffers = []
        for i, img in enumerate(images):
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            img_buffers.append((f"page_{i+1}.jpg", buffer.getvalue()))
        return img_buffers

def image_to_pdf(file):
    img = Image.open(file)
    img = img.convert("RGB")
    buffer = BytesIO()
    img.save(buffer, format="PDF")
    return buffer.getvalue()

def convert_html_to_pdf(html_file):
    html_content = html_file.read().decode('utf-8')
    pdf_file = BytesIO()
    HTML(string=html_content).write_pdf(target=pdf_file)
    return pdf_file.getvalue()

def convert_markdown_to_pdf(md_file):
    html = markdown(md_file.read().decode("utf-8"))
    pdf_file = BytesIO()
    HTML(string=html).write_pdf(target=pdf_file)
    return pdf_file.getvalue()

# ----------------- UI Section -----------------
conversion_options = {
    "PNG → JPG": ("image", "JPG"),
    "JPG → PNG": ("image", "PNG"),
    "WebP → PNG": ("webp", "PNG"),
    "PNG → WebP": ("png", "WebP"),
    "GIF → PNG": ("gif", "PNG"),
    "Image → PDF": ("image", "PDF"),
    "PDF → Images (JPG)": ("pdf", "IMG"),
    "IPYNB → PDF": ("ipynb", "PDF"),
    "TXT → PDF": ("txt", "PDF"),
    "DOCX → PDF": ("docx", "PDF"),
    "HTML → PDF": ("html", "PDF"),
    "Markdown (.md) → PDF": ("md", "PDF"),
    "CSV → XLSX": ("csv", "XLSX"),
    "XLSX → CSV": ("xlsx", "CSV"),
    "JSON → CSV": ("json", "CSV"),
    "CSV → JSON": ("csv", "JSON")
}

conversion_type = st.selectbox("Select Conversion Type", list(conversion_options.keys()))
input_type, output_ext = conversion_options[conversion_type]

uploaded_file = st.file_uploader("Upload File", type=None)

if uploaded_file and st.button("Convert"):
    try:
        result = None
        filename = uploaded_file.name.rsplit(".", 1)[0]

        if conversion_type in ["PNG → JPG", "JPG → PNG", "WebP → PNG", "GIF → PNG", "PNG → WebP"]:
            result = convert_image_to_format(uploaded_file, output_ext)

        elif conversion_type == "IPYNB → PDF":
            result = convert_ipynb_to_pdf(uploaded_file)

        elif conversion_type == "TXT → PDF":
            result = convert_text_to_pdf(uploaded_file)

        elif conversion_type == "DOCX → PDF":
            result = convert_docx_to_pdf(uploaded_file)

        elif conversion_type == "HTML → PDF":
            result = convert_html_to_pdf(uploaded_file)

        elif conversion_type == "Markdown (.md) → PDF":
            result = convert_markdown_to_pdf(uploaded_file)

        elif conversion_type == "CSV → XLSX":
            result = convert_csv_to_xlsx(uploaded_file)

        elif conversion_type == "XLSX → CSV":
            result = convert_xlsx_to_csv(uploaded_file)

        elif conversion_type == "JSON → CSV":
            result = convert_json_to_csv(uploaded_file)

        elif conversion_type == "CSV → JSON":
            result = convert_csv_to_json(uploaded_file)

        elif conversion_type == "PDF → Images (JPG)":
            images = convert_pdf_to_images(uploaded_file)
            for name, img_data in images:
                st.download_button(f"Download {name}", img_data, file_name=name, mime="image/jpeg")

        elif conversion_type == "Image → PDF":
            result = image_to_pdf(uploaded_file)

        if result and conversion_type != "PDF → Images (JPG)":
            download_name = f"{filename}_converted.{output_ext.lower()}"
            st.download_button("Download File", result, file_name=download_name)

    except Exception as e:
        st.error(f"Conversion failed: {e}")
