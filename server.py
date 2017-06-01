#!/usr/bin/env python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import urlparse, parse_qs

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

# --- (https://github.com/tgalal/yowsup/issues/671#issuecomment-77545896)
logging.basicConfig(level=logging.DEBUG)

port_number = 8000
number = "" # fill in with whatsapp registered number
pwd = "" # && password
stack = None

def send_message(number, content):
  global stack
  stack.broadcastEvent(YowLayerEvent(IPerformLayer.SEND_MESSAGE, number=number, content=content))

def send_image(number, path, caption=None):
  global stack
  stack.broadcastEvent(YowLayerEvent(IPerformLayer.SEND_IMAGE, number=number, path=path, caption=caption))

def group_create(group_name, jids):
  global stack
  stack.broadcastEvent(YowLayerEvent(IPerformLayer.GROUP_CREATE, group_name=group_name, jids=jids))

def group_invite(group_jid, jids):
  global stack
  stack.broadcastEvent(YowLayerEvent(IPerformLayer.GROUP_INVITE, group_jid=group_jid, jids=jids))

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
    
    # --- send text to number
    if self.path.startswith('/send-msg?'):
      query = parse_qs(urlparse(self.path).query)
      send_message(query['num'][0], query['msg'][0])
      # send_message('xxx', 'Hello from the web.')
      self.wfile.write('message sent')
    
    # --- send image to number
    elif self.path.startswith('/send-img?'):
      query = parse_qs(urlparse(self.path).query)
      send_image(query['group-num'][0], query['path'][0], query['caption'][0])
      # send_image('xxx-ttt/group-jid', 'path/to-file.ext', 'caption')
      self.wfile.write('message sent')
    
    # --- create and invite to group
    elif self.path.startswith ('/group-create?'):
      query = parse_qs(urlparse(self.path).query)
      group_create(query['group-name'][0], query['nums'][0])
      # group_create('subject', 'xxx,xxx,xxx')
      self.wfile.write('group made && invitation sent')
    
    # --- invite to group
    elif self.path.startswith('/group-invite?'):
      query = parse_qs(urlparse(self.path).query)
      group_invite(query['group-id'][0], query['nums'][0])
      # group_invite('xxx-ttt/group-jid', 'xxx,xxx,xxx')
      self.wfile.write('invitation sent')
    
    # --- send text to group
    elif self.path.startswith('/group-msg?'):
      query = parse_qs(urlparse(self.path).query)
      send_message(query['group-id'][0], query['msg'][0])
      # send_message('xxx-ttt/group-jid', 'msg')
      self.wfile.write('message to group sent')
    
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

