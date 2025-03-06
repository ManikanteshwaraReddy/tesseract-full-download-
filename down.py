import streamlit as st
import requests
from PyPDF2 import PdfMerger
import os
import re
import base64

# Function to sanitize filenames
def sanitize_filename(filename):
    filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', "", filename)
    return filename

# Function to download a PDF from a URL
def download_pdf(url, filename):
    response = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(response.content)

# Function to merge multiple PDFs into one
def merge_pdfs(pdf_list, output):
    merger = PdfMerger()
    for pdf in pdf_list:
        merger.append(pdf)
    merger.write(output)
    merger.close()

# Function to generate a download link for the merged PDF
def generate_download_link(file_path, file_label):
    with open(file_path, "rb") as file:
        base64_pdf = base64.b64encode(file.read()).decode('utf-8')
    file_name = os.path.basename(file_path)
    download_link = f'<a href="data:application/octet-stream;base64,{base64_pdf}" download="{file_name}">{file_label}</a>'
    return download_link

# Main function
def main():
    # Set page title and icon
    st.set_page_config(page_title="PDF Merger", page_icon="📄", layout="centered")

    # Add a title with custom styling
    st.markdown(
        """
        <h1 style='text-align: center; color: #4A90E2;'>
            📄 PDF Merger from Tess
        </h1>
        """,
        unsafe_allow_html=True,
    )

    # Add a sidebar for additional information or inputs
    with st.sidebar:
        st.markdown("### About")
        st.markdown(
            "This app allows you to download and merge PDFs from Tess using an API. "
            "Enter your authorization key, unit ID, and a custom filename for the merged PDF."
        )
        st.markdown("---")
        st.markdown("### Instructions")
        st.markdown(
            """
            1. Enter your **Authorization Key** and **Unit ID**.
            2. Provide a custom name for the merged PDF.
            3. Click the **Download PDFs** button to fetch and merge the PDFs.
            4. Download the merged PDF using the provided link.
            """
        )

    # Main content
    col1, col2 = st.columns(2)

    with col1:
        auth_key = st.text_input("🔑 Enter Authorization Key", type="password", help="Your API authorization key.")

    with col2:
        unit_id = st.text_input("📂 Enter Unit ID", help="The ID of the unit you want to fetch PDFs from.")

    custom_filename = st.text_input(
        "✏️ Enter Desired Name for Merged PDF",
        "Merged_Document.pdf",
        help="Provide a custom name for the merged PDF (e.g., My_Merged_File.pdf).",
    )

    if st.button("🚀 Download PDFs", help="Click to fetch and merge PDFs."):
        if not auth_key or not unit_id:
            st.error("❌ Please enter both Authorization Key and Unit ID.")
            return

        # Fetch data from the API
        url = f"https://api.tesseractonline.com/studentmaster/get-topics-unit/{unit_id}"
        headers = {"Authorization": auth_key}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            st.error("❌ Failed to fetch data from API. Please check the Authorization Key and Unit ID.")
            return

        data = response.json()

        if data.get("Error", True):
            st.error("❌ Error in API response. Please check the Authorization Key and Unit ID.")
            return

        topics = data.get("payload", {}).get("topics", [])
        if not topics:
            st.warning("⚠️ No topics found in the given unit.")
            return

        # Download and merge PDFs
        pdf_files = []
        output_dir = "pdfs"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with st.spinner("⏳ Downloading and merging PDFs..."):
            for topic in topics:
                pdf_url = topic.get("pdf")
                if pdf_url:
                    full_pdf_url = f"https://api.tesseractonline.com/{pdf_url}"
                    filename = sanitize_filename(f"{topic.get('name', 'topic')}.pdf")
                    filepath = os.path.join(output_dir, filename)
                    download_pdf(full_pdf_url, filepath)
                    pdf_files.append(filepath)

            if pdf_files:
                # Ensure the custom filename has a .pdf extension
                if not custom_filename.lower().endswith('.pdf'):
                    custom_filename += '.pdf'

                output_file = os.path.join(output_dir, sanitize_filename(custom_filename))
                merge_pdfs(pdf_files, output_file)

                # Generate download link
                download_link = generate_download_link(output_file, f"📥 Click here to download the merged PDF")
                st.markdown(download_link, unsafe_allow_html=True)

                st.success("✅ PDFs downloaded and merged successfully!")
            else:
                st.warning("⚠️ No PDFs found to download.")

# Run the app
if __name__ == "__main__":
    main()
