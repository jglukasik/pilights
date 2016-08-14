#!/usr/bin/env python
import argparse
import random
import signal
import sys
import threading
import time
import urlparse
import json
import os

from neopixel import *
from Queue import Queue
from wsgiref.simple_server import make_server
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication

# LED strip configuration:
LED_COUNT      = 450      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 240     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

# Messaging queue for main input thread to communicate with led painter
mq = Queue()
connections = []

class PiWebSocket(WebSocket):
  def received_message(self, message):
    print message
    mq.put(str(message))
  def handshake_ok(self):
    print "Handshake ok"
  def opened(self):
    print "Opening, adding to connections"
    connections.append(self)
  def closed(self, code, reason=None):
    print "Closed down", code, reason

# Handle ctrl-c
def signal_handler(signal, frame):
  print('Exiting pilights...')
  #os.remove('/var/run/pilights.pid')
  srv.server_close()
  sys.exit(0)

def paint_the(feature):
  for i in range(feature["start"], feature["stop"]):
    strip.setPixelColorRGB(i,int(feature["r"]),int(feature["g"]),int(feature["b"]))
  strip.show()

if __name__ == '__main__':

  parser = argparse.ArgumentParser(description="Flash some LEDs")

  # Create and initialize NeoPixel object
  strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
  strip.begin()

  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)

  print "Welcome to piLights"
  print ""

  print "Starting websocket..."
  srv = make_server('192.168.1.234', 9000, server_class=WSGIServer,
                    handler_class=WebSocketWSGIRequestHandler,
                    app=WebSocketWSGIApplication(handler_cls=PiWebSocket))
  srv.initialize_websockets_manager()
  s = threading.Thread(target=lambda: srv.serve_forever())
  s.start()
  print "Websocket started."

  with open('room.json') as room_file:
    room = json.load(room_file)

  for feature in room["features"]:
    paint_the(feature)

  while True:
    if not mq.empty():
      try:
        feature = json.loads(mq.get())
        paint_the(feature)
      except:
        pass
