import streamlit as st
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert import PDFExporter
import os
import sys
import asyncio

# --- Core Conversion Logic ---

def convert_notebook_to_pdf(notebook_path, output_path):
    """
    Converts an .ipynb notebook file to a PDF file without the default title and date.

    This function uses a custom LaTeX template ('notitle.tplx') to override
    the default title block.

    Args:
        notebook_path (str): The full path to the input notebook file.
        output_path (str): The full path where the output PDF will be saved.

    Returns:
        bool: True if conversion is successful, False otherwise.
        str: A message indicating the result or error.
    """
    try:
        # Get the directory where the script and template are located
        script_dir = os.path.dirname(__file__)
        template_file_name = 'notitle.tplx'
        
        # Check if the custom template file exists in the script's directory
        if not os.path.exists(os.path.join(script_dir, template_file_name)):
            return False, f"Error: The required template file '{template_file_name}' was not found in the project directory."

        # 1. Read the notebook
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)

        # 2. Configure the PDF exporter
        # --- MODIFIED: Removed the problematic get_template_path import ---
        # We will pass our script's directory directly to the exporter.
        # nbconvert will search our directory for 'notitle.tplx' and its own
        # default directories for the base 'article.tplx' template.
        pdf_exporter = PDFExporter(
            template_file=template_file_name,
            template_paths=[script_dir]
        )
        
        # 3. Convert the notebook to PDF
        pdf_data, resources = pdf_exporter.from_notebook_node(nb)

        # 4. Write the PDF to a file
        with open(output_path, 'wb') as f:
            f.write(pdf_data)
        
        return True, f"Successfully converted to {os.path.basename(output_path)}"

    except FileNotFoundError:
        return False, f"Error: The file '{notebook_path}' was not found."
    except Exception as e:
        # Catches errors from nbconvert, often related to missing LaTeX
        error_message = str(e)
        if "xelatex not found on PATH" in error_message or "pdflatex not found on PATH" in error_message:
             return False, ("ERROR: LaTeX is not installed or not in the system's PATH. "
                           "Please install a LaTeX distribution (like MiKTeX for Windows, "
                           "TeX Live for Linux, or MacTeX for macOS) to convert notebooks to PDF.")
        return False, f"An unexpected error occurred: {e}"


# --- Streamlit User Interface ---

def main():
    """
    The main function that runs the Streamlit web application.
    """
    # Set page configuration
    st.set_page_config(
        page_title="IPYNB to PDF Converter",
        page_icon="📄",
        layout="centered",
        initial_sidebar_state="auto",
    )

    st.title("📄 IPYNB to PDF Converter")
    st.write("Upload your Jupyter Notebook (`.ipynb`) file and convert it to a PDF document.")
    st.write("---")

    # File uploader widget
    uploaded_file = st.file_uploader(
        "Choose an .ipynb file",
        type=['ipynb']
    )

    if uploaded_file is not None:
        # Create a temporary directory to store the uploaded file
        temp_dir = "temp_files"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Define file paths
        input_path = os.path.join(temp_dir, uploaded_file.name)
        file_base_name = os.path.splitext(uploaded_file.name)[0]
        output_path = os.path.join(temp_dir, f"{file_base_name}.pdf")

        # Save the uploaded file to the temporary location
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"Uploaded '{uploaded_file.name}' successfully.")

        # Convert button
        if st.button("Convert to PDF", type="primary"):
            with st.spinner("Converting... This may take a moment. Please wait."):
                # Run the conversion
                success, message = convert_notebook_to_pdf(input_path, output_path)

                if success:
                    st.success("✅ Conversion successful!")
                    
                    # Provide download link
                    with open(output_path, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()

                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=os.path.basename(output_path),
                        mime="application/pdf"
                    )
                else:
                    st.error(f"❌ Conversion Failed: {message}")

    st.markdown("---")
    st.info(
        "**Note:** This converter requires a LaTeX installation on the machine where this app is running. "
        "If the conversion fails, it's likely because LaTeX is missing."
    )


if __name__ == "__main__":
    # Fix for asyncio event loop error in Streamlit on Windows
    if sys.platform == "win32" and sys.version_info >= (3, 8, 0):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
