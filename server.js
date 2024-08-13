const liveServer = require('live-server');

const params = {
    port: 8080, // Set the server port. Defaults to 8080.
    root: ".", // Set root directory that's being served. Defaults to cwd.
    open: false, // When false, it won't load your browser by default.
    ignore: 'node_modules', // Ignore changes in this directory
    file: "index.html", // When set, serve this file for every 404 (useful for single-page applications).
    wait: 1000, // Waits for all changes, before reloading. Defaults to 0 sec.
    logLevel: 2, // 0 = errors only, 1 = some, 2 = lots
    middleware: [function(req, res, next) { next(); }],
    watch: ['.'], // List of directories to watch
    noCssInject: true, // Disable CSS injection
    noBrowser: true, // Disable opening the browser
    noInline: true, // Disable inline scripting for live reload
};

liveServer.start(params);
