const express = require('express');
const multer = require('multer');
const path = require('path');
const mongoose = require('mongoose');
const dotenv = require('dotenv');
const pdfParse = require('pdf-parse');
const cors = require('cors');  // Import CORS package
const fs = require('fs');  // To check and create 'uploads' folder

// Load environment variables
dotenv.config();

// Initialize Express app
const app = express();
const port = process.env.PORT || 5000;

// Enable CORS for all origins
app.use(cors());

// Middleware to parse JSON bodies
app.use(express.json());

// Set up file storage configuration using Multer (using memory storage for PDF processing)
const storage = multer.memoryStorage(); // Use memory storage to get file buffer directly

const upload = multer({
  storage,
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB limit for file size
  },
  fileFilter: (req, file, cb) => {
    const fileTypes = /pdf|jpeg|png/;
    const extname = fileTypes.test(path.extname(file.originalname).toLowerCase());
    const mimeType = fileTypes.test(file.mimetype);
    if (extname && mimeType) {
      return cb(null, true);
    } else {
      cb('Error: Only PDF, PNG, JPEG files are allowed!');
    }
  }
});

// MongoDB schema for storing form data
const formSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true },
  otherData: { type: String, required: true },
});

const Form = mongoose.model('Form', formSchema);

// POST endpoint to upload PDFs
app.post('/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).send({ message: 'No file uploaded' });
  }

  // Extract data from PDF using pdf-parse
  const pdfBuffer = req.file.buffer;

  pdfParse(pdfBuffer).then((data) => {
    // Example: Extract name and email from the PDF text (you can modify based on the structure of your forms)
    const extractedText = data.text;
    let name, email;

    // Adjust the regex based on how data is formatted in your PDF
    try {
      name = extractedText.match(/Name:\s*(\w+\s*\w*)/)[1];
      email = extractedText.match(/Email:\s*(\S+@\S+\.\S+)/)[1];
    } catch (error) {
      return res.status(400).send({ message: 'Error extracting name or email' });
    }

    // Create a new form record in the database
    const newForm = new Form({
      name: name,
      email: email,
      otherData: extractedText, // You can store additional extracted data here
    });

    newForm.save()
      .then((form) => {
        res.status(200).json({ message: 'File uploaded and data saved', form });
      })
      .catch((err) => {
        res.status(500).send({ message: 'Error saving data', error: err });
      });
  }).catch((err) => {
    res.status(500).send({ message: 'Error parsing PDF', error: err });
  });
});

// Endpoint to retrieve all records
app.get('/forms', (req, res) => {
  Form.find()
    .then((forms) => {
      res.status(200).json(forms);
    })
    .catch((err) => {
      res.status(500).send({ message: 'Error fetching forms', error: err });
    });
});

// Check if uploads directory exists, create it if not
if (!fs.existsSync('uploads')) {
  fs.mkdirSync('uploads');
}

// Start the server
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
