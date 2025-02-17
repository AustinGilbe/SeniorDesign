require('dotenv').config({path: './.env'}); // Load environment variables
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

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`🚀 Server running on port ${PORT}`);
});
