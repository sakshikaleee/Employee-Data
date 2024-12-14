import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re
import cv2
import numpy as np

def preprocess_image(image):
    """
    Enhance image for better OCR results.
    """
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    resized = cv2.resize(thresh, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
    return Image.fromarray(resized)

def extract_text_from_pdf(pdf_path):
    """
    Converts a PDF file to text using OCR and prints each page's extracted text in the terminal.
    """
    pages = convert_from_path(pdf_path, dpi=300)
    text = ""
    for page_num, page in enumerate(pages):
        print(f"\nProcessing page {page_num + 1}...")
        processed_image = preprocess_image(page)
        page_text = pytesseract.image_to_string(processed_image, config="--psm 11 --oem 1")
        print(f"Extracted Text from Page {page_num + 1}:")
        print(page_text)  # Print the raw extracted text
        text += page_text + "\n"
    return text

def extract_table_data(image):
    """
    Extracts text from table-like structures using contour detection and OCR.
    """
    # Convert image to grayscale
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    # Apply threshold to highlight lines (table borders)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    # Find contours to detect table structure
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours by size, area that looks like a table
    table_contours = [contour for contour in contours if cv2.contourArea(contour) > 1000]
    
    # Draw contours on the image (for visualization)
    table_image = cv2.drawContours(np.array(image), table_contours, -1, (0, 255, 0), 2)
    
    # Crop out the table regions for better OCR results
    table_text = []
    for contour in table_contours:
        x, y, w, h = cv2.boundingRect(contour)
        table_crop = table_image[y:y+h, x:x+w]
        table_text.append(pytesseract.image_to_string(table_crop, config="--psm 6 --oem 1"))
    
    return "\n".join(table_text)

def parse_extracted_text(text):
    """
    Parses OCR text to extract structured fields based on the form template.
    """
    data = {
        "personal_info": {
            "first_name": "N/A",
            "middle_name": "N/A",
            "last_name": "N/A",
            "dob": "N/A",
            "age": "N/A",
            "gender": "N/A",
            "passport": "N/A",
            "email": "N/A",
            "mobile": "N/A",
        },
        "addresses": {
            "permanent_address": "N/A",
            "current_address": "N/A",
        },
        "education": [],
        "certifications": [],
        "family_info": [],
        "references": []
    }

    # Regex patterns for personal info (same as before)
    patterns = {
        "first_name": r"(?i)First Name[:\-]?\s*([A-Za-z]+)",
        "middle_name": r"(?i)Middle Name[:\-]?\s*([A-Za-z]+)",
        "last_name": r"(?i)Last Name[:\-]?\s*([A-Za-z]+)",
        "dob": r"(?i)Date of Birth[:\-]?\s*([\d/]+)",
        "age": r"(?i)Age[:\-]?\s*(\d+)",
        "gender": r"(?i)Gender[:\-]?\s*(\w+)",
        "passport": r"(?i)Passport[:\-]?\s*(\w+)",
        "email": r"(?i)Email[:\-]?\s*([\w\.-]+@[\w\.-]+\.\w+)",
        "mobile": r"(?i)Mobile[:\-]?\s*(\d+)",
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            data["personal_info"][field] = match.group(1).strip()

    # Addresses (same as before)
    data["addresses"]["permanent_address"] = re.search(
        r"(?i)Permanent Address[:\-]?\s*(.+)", text
    ).group(1).strip() if re.search(r"(?i)Permanent Address[:\-]?\s*(.+)", text) else "N/A"

    data["addresses"]["current_address"] = re.search(
        r"(?i)Current Address[:\-]?\s*(.+)", text
    ).group(1).strip() if re.search(r"(?i)Current Address[:\-]?\s*(.+)", text) else "N/A"

   # Education Section
    education_pattern = r"(?i)\d+\s+([A-Za-z\s]+)\s+([A-Za-z]+)\s+(\d{1,3})\s+(\d{4})"
    education_matches = re.findall(education_pattern, text)

# Only process matches if found
    if education_matches:
        for match in education_matches:
            education_entry = {
            "school_university": match[0].strip(),
            "qualification": match[1].strip(),
            "percentage": match[2].strip(),
            "year": match[3].strip(),
        }
        data["education"].append(education_entry)
    else:
        print("No educational qualifications found in the text.")

        
    # Certifications (same as before)
    certification_matches = re.findall(
        r"(?i)Certification[:\-]?.+?Organizer[:\-]?.+?Duration[:\-]?.+", text, re.DOTALL
    )
    for cert in certification_matches:
        data["certifications"].append(cert.strip())

    # Family Information (same as before)
    family_matches = re.findall(
        r"(?i)Relation[:\-]?.+?Occupation[:\-]?.+?Location[:\-]?.+", text, re.DOTALL
    )
    for family in family_matches:
        data["family_info"].append(family.strip())

    # References (same as before)
    reference_matches = re.findall(
        r"(?i)Name[:\-]?.+?Designation[:\-]?\s*Contact[:\-]?", text, re.DOTALL
    )
    for ref in reference_matches:
        data["references"].append(ref.strip())

    print("\nParsed Data:", data)
    return data

def process_pdf(pdf_path):
    """
    Combines OCR and parsing to extract structured data from a PDF.
    """
    try:
        text = extract_text_from_pdf(pdf_path)  # This will print extracted text to terminal
        print("\nComplete Extracted Text from PDF:")
        print(text)  # Print the complete extracted text to terminal
        parsed_data = parse_extracted_text(text)
        return parsed_data
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return None


# Example usage
if __name__ == "__main__":
    pdf_path = r'C:\Users\HP\Downloads\Sakshi info.pdf'  # Replace with your PDF path
    extracted_data = process_pdf(pdf_path)
    print("Extracted Data:", extracted_data)
