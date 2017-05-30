#!/usr/bin/env python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from layer import IPerformLayer

from yowsup.stacks import  YowStackBuilder
from yowsup.layers.auth import AuthError
from yowsup.layers import YowLayerEvent
from yowsup.layers.network import YowNetworkLayer

import sys
import datetime
import os
import logging
import traceback
import threading
import multiprocessing

# This class will handles any incoming request from the browser

port_number = 8000
number = "13126840113"
pwd = "" # Put the password here - JBG
stack = None

def send_message(number, content):
  global stack
  stack.broadcastEvent(YowLayerEvent(IPerformLayer.SEND_MESSAGE, number=number, content=content))

def start_whatsapp():
  stackBuilder = YowStackBuilder()
  global stack
  stack = stackBuilder\
    .pushDefaultLayers(True)\
    .push(IPerformLayer)\
    .build()

  credentials = (number, pwd)
  stack.setCredentials(credentials)
  stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))

  try:
    print("Looping...")
    stack.loop()
  except AuthError as e:
    print("Authentication Error: %s" % e.message)

class S(BaseHTTPRequestHandler):

  def _set_headers(self):
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.end_headers()

  def do_GET(self):
    self._set_headers()
    send_message('31611751966', 'Hello from the web.')
    self.wfile.write("done.")
    return

if __name__ == "__main__":

  t = threading.Thread(target=start_whatsapp)
  t.daemon = True
  t.start()

  try:
    server = HTTPServer(('', port_number), S)
    print 'Started HTTP server on port', port_number
    server.serve_forever()

  except KeyboardInterrupt:
    print '^C received, shutting down server'
    server.socket.close()

