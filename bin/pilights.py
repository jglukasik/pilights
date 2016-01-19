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
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

# Messaging queue for main input thread to communicate with led painter
mq = Queue()
runners = []
connections = []
tail_length = 91

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

# Advance each of the runner dots on the strip forward one step
def led_step(strip, runners, brightness, tail, color, fire_effect):
  (r,g,b) = map(int, color)
  if fire_effect:
    (r,g,b) = map(lambda x: x - random.randint(0,150), (255,135,40))
    (r,g,b) = map(lambda x: 0 if x < 0 else x, (r,g,b))
    # print r, ' ', g, ' ', b
    color = (r,g,b)
  for i in range(strip.numPixels()):
    strip.setPixelColorRGB(i,r,g,b)
  for r in runners:
    if r[0] >= 0:
      strip.setPixelColorRGB(*r)
  strip.setBrightness(brightness)
  if not tail:
    for i in range(tail_length):
      strip.setPixelColorRGB(i,0,0,0)
  strip.show()
  last_runner = runners[-1:]
  for r in runners:
    r[0] = r[0] + 1
    if r[0] > strip.numPixels():
      runners.remove(r)

def painter():

  wait_ms = 70
  dot_chance = 0.0
  streak_chance = 0.0
  streak_length = 20
  brightness = 100
  tail = False
  color = (255,255,255)
  fire_effect = False
  run = True

  message = {}
  while True:
    if run:
      if random.random() < streak_chance and (not runners or runners[-1][0] > 0):
        if random.random() < 0.5:
          mq.put('{"message":"fire"}')
        else:
          mq.put('{"message":"ice"}')
      elif random.random() < dot_chance and (not runners or runners[-1][0] > 0):
        runners.append([0,random.randint(0,255),random.randint(0,255),random.randint(0,255)])
      led_step(strip, runners, brightness, tail, color, fire_effect)
      if fire_effect:
        time.sleep(random.randint(400,700)/1000.0)
      else:
        time.sleep(wait_ms/1000.0)

    if not mq.empty():
      try:
        message = mq.get()
        message = json.loads(message)
      except:
        pass

    if 'message' in message:
      if message['message'] == "stop":
        run = False
      elif message['message'] == "pause":
        print "pausing"
        run = not run
      elif message['message'] == "start" or message['message'] == "on" or message['message'] == "play":
        run = True
      elif message['message'] == "off":
        run = False
        strip.setBrightness(0)
        strip.show()
      elif message['message'] == "tail":
        tail = not tail
      elif message['message'] == "fire_effect":
        fire_effect = not fire_effect
      elif message['message'] == "fire":
        g = range(0,256,256/streak_length)
        for x in range(0, streak_length):
          runners.append([-x, 255, g[x], 0])
      elif message['message'] == "ice":
        g = range(0,256,256/streak_length)
        for x in range(0, streak_length):
          runners.append([-x, 0, g[x], 255])
      elif message['message'] == "quit":
        strip.setBrightness(0)
        strip.show()
        return
    
    if 'message' in message:
        print 'Got message: ', message
    if 'wait_input' in message:
        wait_ms = float(message['wait_input'])
    if 'dot_chance' in message:
        dot_chance = float(message['dot_chance'])
    if 'streak_chance' in message:
        streak_chance = float(message['streak_chance'])
    if 'streak_length' in message:
        streak_length = int(message['streak_length'])
    if 'brightness' in message:
        brightness = int(message['brightness'])
    if 'color' in  message:
        color = message['color']

    message = {}

if __name__ == '__main__':

  parser = argparse.ArgumentParser(description="Flash some LEDs")
  parser.add_argument( '-q', action='store_true', dest='quiet_websockets')
  parser.add_argument( '-d', action='store_true', dest='dry_run')
  args = parser.parse_args()

  # Create and initialize NeoPixel object
  strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
  strip.begin()

  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)

  p = threading.Thread(target=painter)
  p.daemon = True
  p.start()

  print "Welcome to piLights"
  print ""

  if not args.quiet_websockets:

    print "Using websockets..."
    srv = make_server('192.168.1.120', 9000, server_class=WSGIServer,
                      handler_class=WebSocketWSGIRequestHandler,
                      app=WebSocketWSGIApplication(handler_cls=PiWebSocket))
    srv.initialize_websockets_manager()
    s = threading.Thread(target=lambda: srv.serve_forever())
    s.daemon = True
    s.start()
    print "Websocket started."


  thing = ''
  while thing != 'quit':
    thing = raw_input('Send message: ')
    mq.put(thing)
    for c in connections:
      try:
        print "Sending message..."
        c.send(thing)
      except:
        print "Connection missing, removing..."
        connections.remove(c)


  print 'Closing painter...'
  while p.isAlive():
    pass

  print 'Goodbye!'

