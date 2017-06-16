from yowsup.layers.interface import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities import OutgoingAckProtocolEntity
from yowsup.layers.protocol_groups.protocolentities import *
from yowsup.layers.protocol_media.protocolentities import *
from yowsup.layers.protocol_media.mediauploader import MediaUploader
from yowsup.layers import YowLayerEvent, EventCallback

from yowsup.common.tools import Jid
from yowsup.common.optionalmodules import PILOptionalModule, AxolotlOptionalModule

import os
import sys
import logging
import time

logging.basicConfig(level=logging.DEBUG)

class IPerformLayer(YowInterfaceLayer):

  def __init__(self):
    super(IPerformLayer, self).__init__()
    YowInterfaceLayer.__init__(self)
    self.PROP_IDENTITY_AUTOTRUST = True
    self.connected = False
    self.jidAliases = {
      "": "@s.whatsapp.net"
      # "name": "xxx@s.whatsapp.net"
    }

  def aliasToJid(self, calias):
    for alias, ajid in self.jidAliases.items():
      if calias.lower() == alias.lower():
        return Jid.normalize(ajid)

    return Jid.normalize(calias)

  SEND_MESSAGE = "org.openwhatsapp.yowsup.event.iperform.send_message"
  PROP_MESSAGES = "org.openwhatsapp.yowsup.prop.sendclient.queue"
  SEND_IMAGE = "org.openwhatsapp.yowsup.event.iperform.send_image"
  GROUP_CREATE = "org.openwhatsapp.yowsup.event.iperform.group_create"
  GROUP_INVITE = "org.openwhatsapp.yowsup.event.iperform.group_invite"
  INIT_SESSION = "org.openwhatsapp.yowsup.event.iperform.init_session"

  @EventCallback(INIT_SESSION)
  def onInitSession(self, layerEvent):
    self.session = layerEvent.getArg("session")

  @EventCallback(SEND_MESSAGE)
  def onSendMessage(self, layerEvent):
    print "Got the message event."
    number = layerEvent.getArg("number")
    content = layerEvent.getArg("content")
    # --- trying to filter b/t personal number and group number
    for number in self.getProp(self.__class__.PROP_MESSAGES, []):
      phone, content = number
      if '@' in phone:
        messageEntity = TextMessageProtocolEntity(content, to = phone)
      elif '-' in phone:
        messageEntity = TextMessageProtocolEntity(content, to = "%s@g.us" % phone)
      else:
        messageEntity = TextMessageProtocolEntity(content, to = "%s@s.whatsapp.net" % phone)
    # ---
    outgoingMessage = TextMessageProtocolEntity(\
      content, to = Jid.normalize(number))
    self.toLower(outgoingMessage) 

  @EventCallback(SEND_IMAGE)
  def onSendImage(self, layerEvent):
    # if self.assertConnected():
    number = layerEvent.getArg("number")
    path = layerEvent.getArg("path")
    caption = layerEvent.getArg("caption")
    jid = self.aliasToJid(number)
    
    entity = RequestUploadIqProtocolEntity(RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE, filePath=path)
    successFn = lambda successEntity, originalEntity: self.onRequestUploadResult(jid, path, successEntity, originalEntity, caption)
    errorFn = lambda errorEntity, originalEntity: self.onRequestUploadError(jid, path, errorEntity, originalEntity)

    self._sendIq(entity, successFn, errorFn)

  @EventCallback(GROUP_CREATE)
  def onGroupsCreate(self, layerEvent):
    # if self.assertConnected():
    print "Created group."
    subject = layerEvent.getArg("group_name")
    jids = layerEvent.getArg("jids")
    jids = [self.aliasToJid(jid) for jid in jids.split(',')] if jids else []

    print "JIDS........................"
    print jids

    entity = CreateGroupsIqProtocolEntity(subject, participants=jids)
    self.toLower(entity)

  @EventCallback(GROUP_INVITE)
  def onGroupInvite(self, layerEvent):
    print "Got the group invitation."
    # if self.assertConnected():
    group_jid = layerEvent.getArg("group_jid")
    jids = layerEvent.getArg("jids")
    jids = [self.aliasToJid(jid) for jid in jids.split(',')]
    entity = AddParticipantsIqProtocolEntity(self.aliasToJid(group_jid), jids)
    self.toLower(entity)

  # ---
  @ProtocolEntityCallback("message")
  def onMessage(self, messageProtocolEntity):
    print "onMessage"

    # send receipt otherwise we keep receiving the same message over and over
    if True:
      receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom(), 'read', messageProtocolEntity.getParticipant())
      
      jid = messageProtocolEntity.getFrom()
      sender = jid.split("-")[0]
      print "Message from: "
      print sender

      if sender not in self.session.senders and jid not in self.session.sub2gid.values():
        if len(self.session.senders) % 5 == 0:
          # Create a new group - JBG
          self.session.group = "lavalab2-" + str(int(round(time.time())))
          entity = CreateGroupsIqProtocolEntity(self.session.group, participants=[self.aliasToJid(sender)])
          self.toLower(entity)
          # This will re-fetch subject to group id mappings, get new group id - JBG
          self.toLower(ListGroupsIqProtocolEntity())
        else:
          # Invite user to group - JBG
          gid = self.session.sub2gid[self.session.group]
          jids = [self.aliasToJid(sender)]
          entity = AddParticipantsIqProtocolEntity(self.aliasToJid(gid), jids)
          self.toLower(entity)
        self.session.senders.append(sender)   
      self.toLower(receipt)

  @ProtocolEntityCallback("receipt")
  def onReceipt(self, entity):
    print "onReceipt"
    ack = OutgoingAckProtocolEntity(entity.getId(), "receipt", entity.getType(), entity.getFrom())
    self.toLower(ack)

  @ProtocolEntityCallback("success")
  def onSuccess(self, entity):
    print('Connected with WhatsApp servers')
    self.toLower(ListGroupsIqProtocolEntity())

  @ProtocolEntityCallback("iq")
  def onIq(self, entity):
    #print(entity.getName())
    if isinstance(entity, ListGroupsResultIqProtocolEntity):
      self.onGroupListReceived(entity)
    elif isinstance(entity, ListParticipantsResultIqProtocolEntity):
      self.onGroupParticipantsReceived(entity)

  # --- Callbacks
  
  def onRequestUploadResult(self, jid, filePath, resultRequestUploadIqProtocolEntity, requestUploadIqProtocolEntity, caption = None):
    if requestUploadIqProtocolEntity.mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_AUDIO:
      doSendFn = self.doSendAudio
    else:
      doSendFn = self.doSendImage

    if resultRequestUploadIqProtocolEntity.isDuplicate():
      doSendFn(filePath, resultRequestUploadIqProtocolEntity.getUrl(), jid, resultRequestUploadIqProtocolEntity.getIp(), caption)
    else:
      successFn = lambda filePath, jid, url: doSendFn(filePath, url, jid, resultRequestUploadIqProtocolEntity.getIp(), caption)
      mediaUploader = MediaUploader(jid, self.getOwnJid(), filePath,
                                    resultRequestUploadIqProtocolEntity.getUrl(),
                                    resultRequestUploadIqProtocolEntity.getResumeOffset(),
                                    successFn, self.onUploadError, self.onUploadProgress, async=False)
      mediaUploader.start()

  def onRequestUploadError(self, jid, path, errorRequestUploadIqProtocolEntity, requestUploadIqProtocolEntity):
    print("Request upload for file %s for %s failed" % (path, jid))

  def onUploadError(self, filePath, jid, url):
    print("Upload file %s to %s for %s failed!" % (filePath, url, jid))

  def onUploadProgress(self, filePath, jid, url, progress):
    sys.stdout.write("%s => %s, %d%% \r" % (os.path.basename(filePath), jid, progress))
    sys.stdout.flush()

  def doSendImage(self, filePath, url, to, ip = None, caption = None):
    entity = ImageDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to, caption = caption)
    self.toLower(entity)
    print entity

  def onGroupListReceived(self, entity):
    for group in entity.getGroups():
      #print('Received group info with id %s (owner %s, subject %s)', group.getId(), group.getOwner(), group.getSubject())
      if group.getSubject() not in self.session.sub2gid:
        self.session.sub2gid[group.getSubject()] = group.getId()
      self.toLower(entity)

  def onGroupParticipantsReceived(self, entity):
    print('Received %d participants in group with id %s', len(entity.getParticipants()), entity.getFrom())

