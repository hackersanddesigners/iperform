#!/usr/bin/env python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from subprocess import call

from yowsup.demos.cli.cli import Cli, clicmd
from yowsup.demos.cli.layer import YowsupCliLayer
from yowsup.layers.interface import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.auth import YowAuthenticationProtocolLayer
from yowsup.layers import YowLayerEvent, EventCallback
from yowsup.layers.network import YowNetworkLayer
import sys
from yowsup.common import YowConstants
import datetime
import os
import logging
from yowsup.layers.protocol_groups.protocolentities      import *
from yowsup.layers.protocol_presence.protocolentities    import *
from yowsup.layers.protocol_messages.protocolentities    import *
from yowsup.layers.protocol_ib.protocolentities          import *
from yowsup.layers.protocol_iq.protocolentities          import *
from yowsup.layers.protocol_contacts.protocolentities    import *
from yowsup.layers.protocol_chatstate.protocolentities   import *
from yowsup.layers.protocol_privacy.protocolentities     import *
from yowsup.layers.protocol_media.protocolentities       import *
from yowsup.layers.protocol_media.mediauploader import MediaUploader
from yowsup.layers.protocol_profiles.protocolentities    import *
from yowsup.common.tools import Jid
from yowsup.common.optionalmodules import PILOptionalModule, AxolotlOptionalModule

# This class will handles any incoming request from the browser

port_number = 8000

class S(BaseHTTPRequestHandler, Cli, YowInterfaceLayer):

  def __init__(self):
    super(YowsupCliLayer, self).__init__()
    YowInterfaceLayer.__init__(self)
    self.accountDelWarnings = 0
    self.connected = False
    self.username = None
    self.sendReceipts = True
    self.sendRead = True
    self.disconnectAction = self.__class__.DISCONNECT_ACTION_PROMPT
    self.credentials = None

    #add aliases to make it user to use commands. for example you can then do:
    # /message send foobar "HI"
    # and then it will get automaticlaly mapped to foobar's jid
    self.jidAliases = {
      # "NAME": "PHONE@s.whatsapp.net"
    }
  
  def setCredentials(self, username, password):
    self.getLayerInterface(YowAuthenticationProtocolLayer).setCredentials(username, password)

    return "%s@s.whatsapp.net" % username

  def assertConnected(self):
    if self.connected:
      return True
    else:
      self.output("Not connected", tag = "Error", prompt = False)
      return False

  # ---

  def _set_headers(self):
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.end_headers()

  @clicmd("Send message to a friend")
  def message_send(self, number, content):
    if self.assertConnected():
      outgoingMessage = TextMessageProtocolEntity(content.encode("utf-8") if sys.version_info >= (3,0) else content, to = self.aliasToJid(number))
      self.toLower(outgoingMessage)
  
  def do_GET(self, message_send=message_send):
    self._set_headers()
    
    # call(['yowsup-cli', 'demos', '-l13126840113:QMNc7MEoZWibWFDS436uFXgawCs=', '-s', '31628959809', 'why'])
    ph_n = '31628959809'
    msg_c = 'why'
    message_send(self, ph_n, msg_c)
    
    self.wfile.write("<html><body><h1>&&</h1></body></html>")
    return

try:
  server = HTTPServer(('', port_number), S)
  print 'Started HTTP server on port', port_number
  server.serve_forever()

except KeyboardInterrupt:
  print '^C received, shutting down server'
  server.socket.close()
