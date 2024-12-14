# Employee Data Onboarding System

This project automates the candidate onboarding process for HR teams by allowing them to upload scanned forms (images or PDFs). The system extracts relevant data from these forms using Optical Character Recognition (OCR) and stores the data in a MongoDB database.

## Features
- Upload scanned onboarding forms (images or PDFs)
- Automatic extraction of candidate information (name, email, phone, address, joining date)
- Store candidate data in MongoDB Atlas
- Search for candidates by name or email
- Preview extracted data before saving

## Tools and Technologies
- **Frontend**: React.js (for user interface)
- **Backend**: Node.js, Express (for handling server-side operations)
- **Database**: MongoDB Atlas (for storing candidate data)
- **OCR Model**: Tesseract.js (for optical character recognition to extract data from images/PDFs)
- **Other Libraries**: `node-fetch`, `pdf2image`, `axios`, etc.

## Setup and Installation

Follow these steps to set up the project on your local machine:

### 1. Clone the repository

git clone https://github.com/your-username/Employee-Data.git
cd Employee-Data


### 2. Install Dependencies
##Frontend (React):
Navigate to the frontend directory and install dependencies:
cd frontend
npm install


##Backend (Node.js and Express):
Navigate to the backend directory and install dependencies:
cd backend
npm install

3. Configure MongoDB Atlas
You need to set up a MongoDB Atlas cluster to store the candidate records.

Go to MongoDB Atlas and sign up/login.
Create a new cluster.
In the Database Access section, create a new user with readWrite permissions.
In the Network Access section, allow access from anywhere (0.0.0.0/0) or specify your IP.
Obtain the connection string for your MongoDB Atlas cluster.

4. Setup Environment Variables
Create a .env file in the backend folder with the following variables:

MONGO_URI=your_mongodb_atlas_connection_string
PORT=5000  # Change this to any port you'd like to run the server on
Replace your_mongodb_atlas_connection_string with the connection string obtained from MongoDB Atlas.

5. Run the Application
Start the Backend Server:
Navigate to the backend directory and run:
cd backend
python app.py
The backend server will start on the port specified in the .env file (default is 5000).

Start the Frontend Server:
Navigate to the frontend directory and run:

cd frontend
npm start
This will start the frontend React application, and you can access it in your browser at http://localhost:3000.

To check the aimodel functionality:
cd model
ocr-env\Scripts\activate
python aimodel.py
