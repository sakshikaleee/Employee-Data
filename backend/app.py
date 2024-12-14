import os
from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import re
from pymongo import MongoClient
import sys
sys.path.append(r'D:\enzigma\model')  # Add the directory containing aimodel.py

import aimodel  

app = Flask(__name__)

# MongoDB Atlas Configuration
MONGO_URI = "mongodb+srv://sakshikale:HQ7iGpLoPRbiXLDH@dataextraction.8mzff.mongodb.net/"  # Replace with your MongoDB Atlas URI
client = MongoClient(MONGO_URI)
db = client['enzigma']  # Create/use the 'enzigma' database
collection = db['candidate_info']  # Create/use the 'candidate_info' collection

# Folder to store uploaded PDFs
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to extract text from PDF (using PyMuPDF)
def extract_text_from_pdf(pdf_path):
    extracted_text = ""
    
    # Open the PDF using PyMuPDF
    doc = fitz.open(pdf_path)
    
    # Loop through each page
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)  # Load the page
        extracted_text += page.get_text("text")  # Extract text from the page
        
    return extracted_text

# API endpoint for uploading multiple PDFs and extracting data
@app.route('/upload', methods=['POST'])
def upload_files():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    files = request.files.getlist('file')  # Get multiple files
    if not files:
        return jsonify({'error': 'No selected files'}), 400

    extracted_data = []

    for file in files:
        if file.filename == '':
            continue  # Skip empty file names

        # Save the uploaded file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Extract text from the uploaded PDF using the AI model
        extracted_text = extract_text_from_pdf(file_path)

        # Extract structured data using the AI model (aimodel.py)
        data = aimodel.clean_and_extract_data(extracted_text)  # Using the AI model for data extraction
        extracted_data.append(data)

        # Store the extracted data in MongoDB
        collection.insert_one(data)  # Save each candidate's data to MongoDB

    # Return the extracted data for all uploaded files as JSON
    return jsonify(extracted_data)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
