require('dotenv').config({ path: './.env' });
const express = require('express');
const cors = require('cors');
const connectDB = require('./config/db');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const app = express();

// Middleware
app.use(express.json());


app.use(cors());
  // Add this error handling middleware
  app.use((err, req, res, next) => {
    console.error('Server error:', err);
    res.status(500).json({ error: 'Internal server error' });
  });

// Connect to MongoDB
connectDB();

// Basic routes
app.get('/', (req, res) => res.send('Backend is running and connected to MongoDB!'));
app.get('/api/test', (req, res) => res.json({ message: "Backend API is working!" }));

// Configure paths - CORRECTED to include SeniorDesign
const UPLOADS_DIR = path.join(__dirname, '../../../SeniorDesign/frontend/public/uploads');
const CURRENT_DIR = path.join(UPLOADS_DIR, 'current');

// Debug: Log the paths to verify
console.log('Uploads Directory:', UPLOADS_DIR);
console.log('Current Directory:', CURRENT_DIR);

// Ensure directories exist at startup
[UPLOADS_DIR, CURRENT_DIR].forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        console.log(`Created directory: ${dir}`);
    }
});

// Configure multer storage
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, UPLOADS_DIR);
    },
    filename: (req, file, cb) => {
        const uniqueName = `${Date.now()}-${file.originalname}`;
        cb(null, uniqueName);
    }
});

const upload = multer({ storage });

app.post('/api/upload', upload.single('file'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ message: 'No file uploaded.' });
    }

    try {
        // Clear current directory
        fs.readdirSync(CURRENT_DIR).forEach(file => {
            const filePath = path.join(CURRENT_DIR, file);
            fs.unlinkSync(filePath);
            console.log('Removed previous current file:', filePath);

        });
        console.log('CURRENT:', CURRENT_DIR);

        // Get file extension and create new filename
        const fileExt = path.extname(req.file.originalname);
        const newFilename = `current${fileExt}`;
        console.log('CURRENT:', CURRENT_DIR);
        const currentDest = path.join(CURRENT_DIR, newFilename);

        // Rename the file directly (more efficient than copy+delete)
        fs.renameSync(req.file.path, currentDest);

        console.log('File moved and renamed to:', currentDest);

        res.json({
            message: 'File uploaded successfully!',
            currentPath: `/uploads/current/${newFilename}`,
            filename: newFilename
        });
    } catch (error) {
        console.error('File processing error:', error);
        res.status(500).json({ 
            message: 'Error processing file', 
            error: error.message 
        });
    }
});

// Simplified current filename endpoint
app.get('/api/current-filename', (req, res) => {
    try {
        const files = fs.readdirSync(CURRENT_DIR);
        const currentFile = files.find(file => file.startsWith('current.'));
        
        if (!currentFile) {
            return res.status(404).json({ error: 'No current file found' });
        }

        res.json({ filename: currentFile });
    } catch (err) {
        console.error('Error:', err);
        res.status(500).json({ error: 'Server error' });
    }
});

// Get current filename endpoint

const currentFolder = path.join(__dirname, '../../../SeniorDesign/frontend/public/uploads/current');

app.get('/api/current', (req, res) => {
  fs.readdir(currentFolder, (err, files) => {
    if (err) {
      console.error('❌ Failed to read current folder:', err);
      return res.status(500).json({ message: 'Failed to read current folder' });
    }

    const csvFiles = files.filter(file => file.endsWith('.csv'));
    if (csvFiles.length === 0) {
      return res.status(404).json({ message: 'No CSV files found in directory' });
    }

    const latestCSV = csvFiles[0]; // Just one expected
    res.json({ filename: latestCSV });
  });
});




const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`🚀 Server running on port ${PORT}`);
});
