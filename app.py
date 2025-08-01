import streamlit as st
import nbformat
from nbconvert import WebPDFExporter
import os
import sys
import asyncio
import playwright

# --- Core Conversion Logic ---

def convert_notebook_to_pdf(notebook_path, output_path):
    """
    Converts an .ipynb notebook file to a PDF file using a headless browser (WebPDF).
    This method does not require a LaTeX installation.

    Args:
        notebook_path (str): The full path to the input notebook file.
        output_path (str): The full path where the output PDF will be saved.

    Returns:
        bool: True if conversion is successful, False otherwise.
        str: A message indicating the result or error.
    """
    try:
        # Ensure playwright's browser dependencies are installed
        # This is a fallback, ideally handled by packages.txt on deployment
        try:
            # In a deployed environment, this might not be possible, but it's good for local testing.
            os.system("playwright install-deps")
            os.system("playwright install chromium")
        except Exception:
            # Silently fail if system calls are not allowed
            pass

        # 1. Read the notebook
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)

        # 2. Configure the WebPDF exporter
        # This exporter uses a headless browser to "print" the notebook to PDF.
        # To remove the default title and date, we can use the 'exclude' options.
        config = {
            "Exporter": {
                "exclude_input_prompt": True,
                "exclude_output_prompt": True,
            }
        }
        
        web_pdf_exporter = WebPDFExporter(config=config)
        
        # 3. Convert the notebook to PDF
        pdf_data, resources = web_pdf_exporter.from_notebook_node(nb)

        # 4. Write the PDF to a file
        with open(output_path, 'wb') as f:
            f.write(pdf_data)
        
        return True, f"Successfully converted to {os.path.basename(output_path)}"

    except FileNotFoundError:
        return False, f"Error: The file '{notebook_path}' was not found."
    except Exception as e:
        # Catches errors from nbconvert or playwright
        error_message = str(e)
        if "command not found" in error_message.lower() or "chromium" in error_message.lower():
             return False, ("ERROR: Headless browser (Chromium) is not installed or not found. "
                           "Please ensure your deployment environment includes the necessary browser dependencies.")
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
        "**Note:** This converter uses a headless browser. If it fails, there might be an issue with the browser dependency installation on the server."
    )


if __name__ == "__main__":
    # Fix for asyncio event loop error in Streamlit on Windows
    if sys.platform == "win32" and sys.version_info >= (3, 8, 0):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
