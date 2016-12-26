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
  wss.on('connection', function connection(xtermWebSocket) {
    console.log(`Got connection from ${xtermWebSocket.upgradeReq.url}`);

    // Get port of container to connect to
    var port = parseInt(url.parse(xtermWebSocket.upgradeReq.url).pathname.split('/')[1]);

    // Open WebSocket to container
    console.log(`Connecting to container port ${port}`);
    var containerWebSocket = new WebSocket(`ws://${dockerHostIP}:${port}`);

    // When container WebSocket connects...
    containerWebSocket.on('open', function() {

      // Forward xterm -> container
      xtermWebSocket.on('message', function(message) {
        containerWebSocket.send(message);
      });

      // Forward container -> xterm
      containerWebSocket.on('message', function(message) {
        xtermWebSocket.send(message);
      });
    });
  });
});
