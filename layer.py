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
logging.basicConfig(level=logging.DEBUG)

class IPerformLayer(YowInterfaceLayer):
  SEND_MESSAGE = "org.openwhatsapp.yowsup.event.iperform.send_message"
  PROP_MESSAGES = "org.openwhatsapp.yowsup.prop.sendclient.queue"

  def __init__(self):
    super(IPerformLayer, self).__init__()
    YowInterfaceLayer.__init__(self)
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

  @EventCallback(SEND_MESSAGE)
  def onSendMessage(self, layerEvent):
    print "Got the message event."
    number = layerEvent.getArg("number")
    content = layerEvent.getArg("content")
    # --- trying to filter b/t personal number or group number
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

  @ProtocolEntityCallback("message")
  def onMessage(self, messageProtocolEntity):
    print "onMessage"
    # send receipt otherwise we keep receiving the same message over and over
        
    if True:
      receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom(), 'read', messageProtocolEntity.getParticipant())
      print "FROM " + messageProtocolEntity.getFrom()
            
      self.toLower(receipt)
    
    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
      print "onReceipt"
      ack = OutgoingAckProtocolEntity(entity.getId(), "receipt", entity.getType(), entity.getFrom())
      self.toLower(ack)

  
  SEND_IMAGE = "org.openwhatsapp.yowsup.event.iperform.send_image"

  @EventCallback(SEND_IMAGE)
  def onSendImage(self, layerEvent):
    number = layerEvent.getArg("number")
    path = layerEvent.getArg("path")
    caption = layerEvent.getArg("caption")
    self.media_send(number, path, RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE)

  def media_send(self, number, path, mediaType, caption = None):
    # if self.assertConnected():
    jid = self.aliasToJid(number)
    entity = RequestUploadIqProtocolEntity(mediaType, filePath=path)
    successFn = lambda successEntity, originalEntity: self.onRequestUploadResult(jid, mediaType, path, successEntity, originalEntity, caption)
    errorFn = lambda errorEntity, originalEntity: self.onRequestUploadError(jid, path, errorEntity, originalEntity)
    self._sendIq(entity, successFn, errorFn)

    self._sendIq(entity, successFn, errorFn)

  def doSendMedia(self, mediaType, filePath, url, to, ip = None, caption = None):
    if mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE:
      entity = ImageDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to, caption = caption)
    elif mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_AUDIO:
      entity = AudioDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to)
    elif mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_VIDEO:
      entity = VideoDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to, caption = caption)
    self.toLower(entity)

  GROUP_CREATE = "org.openwhatsapp.yowsup.event.iperform.group_create"
  @EventCallback(GROUP_CREATE)
  def onGroupsCreate(self, layerEvent):
    # if self.assertConnected():
    print "Created group."
    subject = layerEvent.getArg("group_name")
    jids = layerEvent.getArg("jids")
    jids = [self.aliasToJid(jid) for jid in jids.split(',')] if jids else []
    entity = CreateGroupsIqProtocolEntity(subject, participants=jids)
    self.toLower(entity)


  GROUP_INVITE = "org.openwhatsapp.yowsup.event.iperform.group_invite"
  @EventCallback(GROUP_INVITE)
  def onGroupInvite(self, layerEvent):
    print "Got the group invitation."
    # if self.assertConnected():
    group_jid = layerEvent.getArg("group_jid")
    jids = layerEvent.getArg("jids")
    jids = [self.aliasToJid(jid) for jid in jids.split(',')]
    entity = AddParticipantsIqProtocolEntity(self.aliasToJid(group_jid), jids)
    self.toLower(entity)

  # --- Callbacks
  
  def onRequestUploadResult(self, jid, mediaType, filePath, resultRequestUploadIqProtocolEntity, requestUploadIqProtocolEntity, caption = None):

    if resultRequestUploadIqProtocolEntity.isDuplicate():
      self.doSendMedia(mediaType, filePath, resultRequestUploadIqProtocolEntity.getUrl(), jid,
                       resultRequestUploadIqProtocolEntity.getIp(), caption)
    else:
      successFn = lambda filePath, jid, url: self.doSendMedia(mediaType, filePath, url, jid, resultRequestUploadIqProtocolEntity.getIp(), caption)
      mediaUploader = MediaUploader(jid, self.getOwnJid(), filePath,
                                    resultRequestUploadIqProtocolEntity.getUrl(),
                                    resultRequestUploadIqProtocolEntity.getResumeOffset(),
                                    successFn, self.onUploadError, self.onUploadProgress, async=False)
      mediaUploader.start()

  def onRequestUploadError(self, jid, path, errorRequestUploadIqProtocolEntity, requestUploadIqProtocolEntity):
    logger.error("Request upload for file %s for %s failed" % (path, jid))

  def onUploadError(self, filePath, jid, url):
    logger.error("Upload file %s to %s for %s failed!" % (filePath, url, jid))

  def onUploadProgress(self, filePath, jid, url, progress):
    sys.stdout.write("%s => %s, %d%% \r" % (os.path.basename(filePath), jid, progress))
    sys.stdout.flush()
