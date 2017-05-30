#!/usr/bin/env python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from subprocess import call

# This class will handles any incoming request from the browser

port_number = 8000

class S(BaseHTTPRequestHandler):
  
  def _set_headers(self):
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.end_headers()

  def do_GET(self):
    self._set_headers()
    
    # call(['yowsup-cli', 'demos', '-l13126840113:QMNc7MEoZWibWFDS436uFXgawCs=', '-s', '31628959809', 'why'])
    # ph_n = '31628959809'
    # msg_c = 'why'
    # message_send(self, ph_n, msg_c)
    
    self.wfile.write("<html><body><h1>&&</h1></body></html>")
    return

try:
  server = HTTPServer(('', port_number), S)
  print 'Started HTTP server on port', port_number
  server.serve_forever()

except KeyboardInterrupt:
  print '^C received, shutting down server'
  server.socket.close()
