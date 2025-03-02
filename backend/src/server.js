require('dotenv').config({ path: './.env' }); // Load environment variables
const express = require('express');
const cors = require('cors');
const connectDB = require('./config/db'); // MongoDB connection

const app = express();

// Middleware
app.use(express.json());
app.use(cors());

// Connect to MongoDB
connectDB();

app.get('/', (req, res) => {
    res.send('Backend is running and connected to MongoDB!');
});

app.get('/api/test', (req, res) => {
    res.json({ message: "Backend API is working!" });
});

// New POST endpoint to handle messages from the frontend
app.post('/api/messages', (req, res) => {
    const { text } = req.body;
    console.log('Received text:', text);
    
    // Optionally, save the text to MongoDB here

    res.json({ message: 'Message received successfully', text });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`🚀 Server running on port ${PORT}`);
});
