import streamlit as st
import requests
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet

# Function to get records from API
def get_records(api_url):
    response = requests.get(api_url)
    
    if response.status_code == 200:
        st.write("API request successful.")
        try:
            records_json = response.json()
            if records_json:
                return records_json
            else:
                st.write("No records found.")
        except ValueError:
            st.error("Failed to parse JSON response.")
    else:
        st.error(f"API request failed with status code {response.status_code}.")
    return None

# Function to format text based on specified conditions
def format_text(value):
    if isinstance(value, str):
        words = value.split()
        formatted_lines = []
        for word in words:
            if len(word) > 2:
                formatted_lines.append(word)  # Place long words on a new line
            else:
                # Add word to the current line
                if len(formatted_lines) == 0 or len(formatted_lines[-1].split()) >= 2:
                    formatted_lines.append(word)  # Start a new line if the last one has 2 words
                else:
                    formatted_lines[-1] += ' ' + word  # Add to the current line
        return '\n'.join(formatted_lines)
    return value

# Function to create a PDF with dynamic headers
def create_pdf_with_header(pdf_file, table_data, headers):
    pdf = SimpleDocTemplate(pdf_file, pagesize=A3, rightMargin=60, leftMargin=60, topMargin=60, bottomMargin=30)
    elements = []

    # Add dynamic header texts
    styles = getSampleStyleSheet()
    for header in headers:
        if header.strip():  # Check if header is not empty
            header_paragraph = Paragraph(header, styles['Title'])
            elements.append(header_paragraph)

    # Calculate column width based on the number of columns
    max_table_width = A3[0] - 2 * inch  # Allow for side margins
    num_columns = len(table_data[0])
    col_width = min(4 * inch, max_table_width / num_columns)  # Adjust width to fit all columns

    # Prepare the table with dynamic column width
    table = Table(table_data, colWidths=[col_width] * num_columns)

    # Table styling
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D9D9D9')), 
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Header alignment remains center
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),  # Align value fields to the left
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),  # Set header font to Times New Roman Bold
        ('FONTSIZE', (0, 0), (-1, 0), 7),  # Header font size
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),  # Set value font to Times New Roman Regular
        ('FONTSIZE', (0, 1), (-1, -1), 7),  # Value font size
        # ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Commented out background for body
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), 
    ])

    table.setStyle(style)

    elements.append(table)

    # Build the PDF
    pdf.build(elements)

# Display records in a table
st.title("Records Viewer and Exporter")
st.header("View and Export Records")

# Input for API URL
api_url = st.text_input("Enter your API request URL")

# Input for dynamic header texts
header_texts = st.text_area("Enter header texts (one per line)", height=150)
headers = header_texts.splitlines()  # Split the text into lines

# Fetch records when the API URL is provided
if api_url:
    records_json = get_records(api_url)

    if records_json and 'data' in records_json:
        records = records_json['data']
        field_labels = records_json.get('field_labels', {})

        # Convert records to DataFrame
        df = pd.DataFrame(records)

        # Drop ROW_ID if it exists
        df = df.drop(columns=['ROW_ID'], errors='ignore')

        # Rename columns based on field labels
        df = df.rename(columns=field_labels)

        # Select fields to display
        fields_to_display = st.multiselect("Select fields to display", options=df.columns.tolist())

        if fields_to_display:
            filtered_df = df[fields_to_display]

            # Apply formatting to each cell and column name in the DataFrame
            formatted_df = filtered_df.applymap(format_text)
            formatted_df.columns = [format_text(col) for col in formatted_df.columns]
            
            st.write(formatted_df)
            
            if st.button("Export to PDF"):
                pdf_file = "records.pdf"
                
                # Prepare data for the table
                table_data = [formatted_df.columns.tolist()] + formatted_df.values.tolist()

                # Create the PDF with headers
                create_pdf_with_header(pdf_file, table_data, headers)
                st.success("PDF created successfully!")

                # Provide a download link
                with open(pdf_file, "rb") as file:
                    st.download_button(label="Download PDF", data=file, file_name=pdf_file, mime="application/pdf")
    else:
        st.write("No records to display.")
