const express = require('express');
const multer = require('multer');
const bodyParser = require('body-parser');
const path = require('path');
const app = express();

// Set up storage for uploaded files
const storage = multer.diskStorage({
    destination: './uploads/',
    filename: function (req, file, cb) {
        cb(null, 'protein_' + Date.now() + path.extname(file.originalname));
    }
});

const upload = multer({ storage: storage });

// Middleware
app.use(bodyParser.json());
app.use(express.static('public')); // Assuming your HTML file is in 'public' folder

// Handle file upload
app.post('/upload', upload.single('file'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: 'No file uploaded.' });
    }

    // Return the file path to the client
    res.json({
        message: 'File uploaded successfully!',
        filepath: req.file.path
    });
});

// Handle grid generation
app.post('/grid', (req, res) => {
    const { filepath, mode, residues } = req.body;

    if (!filepath || !mode) {
        return res.status(400).json({ error: 'File path and mode are required.' });
    }

    // Perform your grid generation logic here
    // For demonstration, we'll just return a success message

    console.log('Generating grid with the following parameters:');
    console.log('File Path:', filepath);
    console.log('Mode:', mode);
    console.log('Residues:', residues);

    // Simulate grid generation
    setTimeout(() => {
        res.json({ message: 'Grid generated successfully!' });
    }, 1000);
});

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
