const express = require('express');
const app = express();

// Test route
app.get('/', (req, res) => {
    res.send('Express server is running correctly!');
});

// Start the server
const port = 8080;
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
