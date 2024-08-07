const liveServer = require('live-server');

const params = {
    port: 8080, // Set the server port. Defaults to 8080.
    root: ".", // Set root directory that's being served. Defaults to cwd.
    open: false, // When false, it won't load your browser by default.
    file: "index.html", // When set, serve this file for every 404 (useful for single-page applications).
    wait: 1000, // Waits for all changes, before reloading. Defaults to 0 sec.
    logLevel: 2, // 0 = errors only, 1 = some, 2 = lots
    middleware: [
        function(req, res, next) {
            // Custom middleware to remove live reload script
            if (req.url.endsWith('.html')) {
                let body = '';
                res.on('data', chunk => {
                    body += chunk;
                });
                res.on('end', () => {
                    body = body.replace(/<script[^>]*>[^<]*live reload[^<]*<\/script>/gi, '');
                    res.setHeader('Content-Length', Buffer.byteLength(body));
                    res.end(body);
                });
            } else {
                next();
            }
        }
    ]
};

liveServer.start(params);
