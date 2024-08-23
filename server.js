const express = require('express');
const cors = require('cors');
const liveServer = require('live-server');

const app = express();

// Enable CORS for all routes
app.use(cors({
    origin: 'http://localhost:3000'  // Allow requests from React app
}));

// Middleware to parse JSON request bodies
app.use(express.json());

// Example API route
app.post('/search', (req, res) => {
    const query = req.body.query;
    res.json({ message: `You searched for: ${query}` });
});

// Start the Express server on port 5000
const apiPort = 5000;
app.listen(apiPort, () => {
    console.log(`API server running on http://127.0.0.1:${apiPort}`);
});

// Parameters for live-server to serve static files on port 8080
const params = {
    port: 8080, // Port for serving static files
    root: ".", // Serve files from the current directory
    open: false, // Don't auto-open the browser
    ignore: 'node_modules', // Ignore changes in node_modules
    file: "index.html", // Serve index.html for any 404s (SPA routing)
    wait: 1000, // Wait before reloading
    logLevel: 2, // Log level
    middleware: [function(req, res, next) { next(); }], // Custom middleware
    watch: ['.'], // Watch all files in the current directory for changes
    noCssInject: true, // Disable CSS injection for live reload
    noBrowser: true, // Don't open the browser on start
    noInline: true, // Disable inline scripting for live reload
};

// Start live-server to serve static files
liveServer.start(params);
