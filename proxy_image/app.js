var url = require('url');
var child_process = require('child_process');

var pty = require('pty.js');
var WebSocketServer = require('ws').Server;
var WebSocket = require('ws');

// Get the IP of the container host
child_process.exec("route -n | awk '/UG[ \t]/{print $2}'", {'shell': '/bin/bash'}, (error, stdout, stderr) => {
  var dockerHostIP = stdout.trim();
  console.log(`Docker host IP: ${dockerHostIP}`);

  // Create WebSocket server
  var wss = new WebSocketServer({ port: 10412 });

  // Register socket on connect handler
  wss.on('connection', function connection(ws) {
    console.log(`Connection from ${ws.upgradeReq.url}`);

    // check if the websocket URL is in expected format, if not, do nothing
    var url_parts = url.parse(ws.upgradeReq.url).pathname.split('/');

    if (url_parts.length > 1 && !isNaN(url_parts[1])) {
        // Get port of container to connect to
        var port = parseInt(url_parts[1]);

        // Open WebSocket to container
        var containerURL = `ws://${dockerHostIP}:${port}`;
        console.log(`Opening websocket to ${containerURL}`);
        var containerWebSocket = new WebSocket(containerURL);

        // When container WebSocket connects...
        containerWebSocket.on('open', function() {
          console.log(`Websocket ${containerURL} opened`);

          // Forward xterm -> container
          ws.on('message', function(message) {
            console.log('xterm -> container: ' + message);
            containerWebSocket.send(message);
          });

          // Forward container -> xterm
          containerWebSocket.on('message', function(message) {
            console.log('container -> xterm: ' + message);
            ws.send(message);
          });
        });
    } else {
        console.log(`Invalid URL received: ${ws.upgradeReq.url}`);
    }
  });
});
