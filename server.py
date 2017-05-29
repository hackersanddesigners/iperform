#!/usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class S(BaseHTTPRequestHandler):
  def _set_headers(self):
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.end_headers()

  def do_GET(self):
    self._set_headers()
    self.wfile.write("<html><body><h1>&&</h1></body></html>")

  def do_HEAD(self):
    self._set_headers()

  def do_POST(self):
    # does not do anything with posted data
    self._set_headers()
    self.wfile.write("<html><body><h1>pp</h1></body></html>")

def run(server_class=HTTPServer, handler_class=S, port=8000):
  server_address = ('', port)
  httpd = server_class(server_address, handler_class)
  print 'starting httpd'
  httpd.serve_forever()

if __name__ == '__main__':
  from sys import argv

  if len(argv) == 2:
    run(port=int(argv[1]))
  else:
    run()
