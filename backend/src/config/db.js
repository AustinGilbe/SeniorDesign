const mongoose = require('mongoose');
require('dotenv').config({ path: '../.env' });  // Ensure .env is loaded

// Debugging - Print variables to ensure they load correctly
console.log("🔍 Debugging DB_USER:", process.env.DB_USER);
console.log("🔍 Debugging DB_PASS:", process.env.DB_PASS);
console.log("🔍 Debugging DB_NAME:", process.env.DB_NAME);


// Construct the connection string dynamically
const MONGO_URI = `mongodb+srv://${process.env.DB_USER}:${process.env.DB_PASS}@cluster0.bpgck.mongodb.net/${process.env.DB_NAME}?retryWrites=true&w=majority`;

const connectDB = async () => {
    try {
        const conn = await mongoose.connect(MONGO_URI);
        console.log(`✅ MongoDB Connected: ${conn.connection.host}`);
    } catch (error) {
        console.error(`❌ MongoDB Connection Error: ${error.message}`);
        process.exit(1);
    }
};

module.exports = connectDB;
