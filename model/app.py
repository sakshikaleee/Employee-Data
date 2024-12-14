import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from bson import ObjectId
import re
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)

# MongoDB Configuration
MONGO_URI = "mongodb+srv://sakshikale:HQ7iGpLoPRbiXLDH@dataextraction.8mzff.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client['enzigma']
collection = db['form_data']

# Upload Folder
UPLOAD_FOLDER = 'uploads'
PHOTO_FOLDER = 'photos'
SIGNATURE_FOLDER = 'signatures'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PHOTO_FOLDER'] = PHOTO_FOLDER
app.config['SIGNATURE_FOLDER'] = SIGNATURE_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PHOTO_FOLDER, exist_ok=True)
os.makedirs(SIGNATURE_FOLDER, exist_ok=True)


def preprocess_image(image):
    """
    Preprocesses an image to improve OCR accuracy.
    """
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    resized = cv2.resize(thresh, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
    return Image.fromarray(resized)


def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF using OCR.
    """
    pages = convert_from_path(pdf_path, dpi=300)
    text = ""
    for page_num, page in enumerate(pages):
        try:
            processed_image = preprocess_image(page)
            page_text = pytesseract.image_to_string(processed_image, config="--psm 6 --oem 1")
            text += page_text + "\n"
        except Exception as e:
            print(f"Error processing page {page_num + 1}: {e}")
    return text


def extract_images_from_pdf(pdf_path, output_folder):
    """
    Extracts images from a PDF and saves them to the output folder.
    """
    doc = fitz.open(pdf_path)
    images = []
    for i in range(len(doc)):
        for img_index, img in enumerate(doc.get_page_images(i, full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_path = os.path.join(output_folder, f"{ObjectId()}_{i + 1}_img_{img_index + 1}.{image_ext}")
            try:
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                print(f"Image saved at: {image_path}")  # Debugging line
                images.append(image_path)
            except Exception as e:
                print(f"Error saving image {img_index + 1} from page {i + 1}: {e}")
    return images


def parse_extracted_text(text):
    """
    Parses the OCR text to extract structured fields including educational qualifications.
    """
    patterns = {
        "name": r"Name \(Block Letters[^:]+:\s*(.+)",
        "permanent_address": r"Permanent Address:([\s\S]+?)\n",  # Match multiline
        "current_address": r"Current Address:([\s\S]+?)\n",
        "dob": r"Date of Birth: (\d{2}/\d{2}/\d{4})",
        "mobile": r"Mobile: (\d+)",
        "email": r"Email ID: (\S+@\S+)",
        # Educational Qualifications
        "educational_qualifications": r"(\d+)\s+(.+?)\s+(\d+)%?\s+(\d{4})"
    }

    data = {}
    for field, pattern in patterns.items():
        matches = re.findall(pattern, text) if field == "educational_qualifications" else re.search(pattern, text)
        if field == "educational_qualifications" and matches:
            data[field] = [{"school": m[1], "qualification": m[0], "percentage": m[2], "year": m[3]} for m in matches]
        else:
            data[field] = matches.group(1).strip() if matches else "N/A"

    # Ensure that educational_qualifications is always an array
    if "educational_qualifications" not in data:
        data["educational_qualifications"] = []

    return data


@app.route('/photos/<path:filename>')
def serve_photo(filename):
    return send_from_directory(app.config['PHOTO_FOLDER'], filename)


@app.route('/signatures/<path:filename>')
def serve_signature(filename):
    return send_from_directory(app.config['SIGNATURE_FOLDER'], filename)


@app.route('/upload', methods=['POST'])
def upload_files():
    """
    Endpoint for uploading and processing files.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    files = request.files.getlist('file')
    if not files:
        return jsonify({'error': 'No selected files'}), 400

    extracted_data = []

    for file in files:
        if file.filename == '':
            continue

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        try:
            text = extract_text_from_pdf(file_path)
            parsed_data = parse_extracted_text(text)

            # Extract images from PDF
            images = extract_images_from_pdf(file_path, app.config['PHOTO_FOLDER'])

            # Ensure the 4th photo is chosen if it exists, otherwise default to None
            if len(images) >= 4:
                parsed_data["photo"] = images[3]  # 4th photo (0-indexed)
            elif images:
                parsed_data["photo"] = images[0]  # Default to the first photo if fewer than 4 images
            else:
                parsed_data["photo"] = None

            # Extract signature (assume the last image is the signature)
            if images:
                signature_path = os.path.join(app.config['SIGNATURE_FOLDER'], f"{ObjectId()}_signature.jpg")
                signature_image = images[-1]  # Last image assumed to be the signature
                os.rename(signature_image, signature_path)
                parsed_data["signature"] = signature_path

            # Save to MongoDB
            result = collection.insert_one(parsed_data)
            parsed_data["_id"] = str(result.inserted_id)

            # Convert photo and signature to URLs
            if parsed_data.get("photo"):
                parsed_data["photo"] = f'http://127.0.0.1:5000/photos/{os.path.basename(parsed_data["photo"])}'
            if parsed_data.get("signature"):
                parsed_data["signature"] = f'http://127.0.0.1:5000/signatures/{os.path.basename(parsed_data["signature"])}'

            extracted_data.append(parsed_data)
        except Exception as e:
            print(f"Error processing file {file.filename}: {e}")

    return jsonify(extracted_data)


if __name__ == "__main__":
    app.run(debug=True)
