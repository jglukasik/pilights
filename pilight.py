import argparse
import random
import signal
import sys
import threading
import time
import urlparse
import json

from Queue import Queue
from wsgiref.simple_server import make_server
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication

# LED strip configuration:
LED_COUNT      = 150      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

# Messaging queue for main input thread to communicate with led painter
mq = Queue()
runners = []
connections = []

class PiWebSocket(WebSocket):
  def received_message(self, message):
    print message
    mq.put(str(message))
  def opened(self):
    connections.append(self)

class dummy_strip:
  def setBrightness(self, brightness):
    return
  def numPixels(self):
    return LED_COUNT
  def setPixelColorRGB(self,n,r,g,b):
    return
  def show(self):
    return

# from http://stackoverflow.com/questions/214359/converting-hex-color-to-rgb-and-vice-versa
def hex_to_rgb(value):
  value = value.lstrip('#')
  lv = len(value)
  return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

# Handle ctrl-c
def signal_handler(signal, frame):
  print('Exiting...')
  sys.exit(0)

# Advance each of the runner dots on the strip forward one step
def led_step(strip, runners):
  for i in range(strip.numPixels()):
    strip.setPixelColorRGB(i,100,100,100)
  for r in runners:
    if r[0] >= 0:
      strip.setPixelColorRGB(*r)
  strip.setBrightness(60)
  strip.show()
  last_runner = runners[-1:]
  for r in runners:
    r[0] = r[0] + 1
    if r[0] > strip.numPixels():
      runners.remove(r)

def painter():

  wait_ms = 70
  new_chance = 0.0
  streak_chance = 0.0
  streak_length = 20
  run = True

  message = {}
  while True:
    if run:
      if random.random() < streak_chance:
        if random.random() < 0.5:
          mq.put('{"message":"fire"}')
        else:
          mq.put('{"message":"ice"}')
      elif random.random() < new_chance and (not runners or runners[-1][0] > 0):
        runners.append([0,random.randint(0,255),random.randint(0,255),random.randint(0,255)])
      time.sleep(wait_ms/1000.0)
      led_step(strip, runners)

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
    
    if 'wait_input' in message:
        wait_ms = message['wait_ms']
    if 'new_change' in message:
        new_chance = message['new_chance']
    if 'streak_chance' in message:
        streak_chance = message['streak_chance']
    if 'streak_length' in message:
        streak_length = message['streak_length']

    message = {}

def server(environ, start_response):
    path = environ.get('PATH_INFO', '').lstrip('/')
    params = urlparse.parse_qs(environ.get('QUERY_STRING', ''))
    msg = "intentionally left blank"

    if path:
      msg = path
      mq.put(msg)

    if 'msg' in params:
      msg = params['msg'][0]
      mq.put(msg)

    start_response('200 OK', [('Content-Type', 'text/html')])
    return ['''
       <body style="font-size:xx-large">
       <a href="http://pi.jgl.me/start" style="color:green">start</a>
       <br>
       <a href="http://pi.jgl.me/stop" style="color:yellow">stop</a>
       <br>
       <a href="http://pi.jgl.me/off" style="color:red">off</a>
       <br>
       <br>
       <br>
       <a href="http://pi.jgl.me/fire" style="color:orange">fire</a>
       <br>
       <a href="http://pi.jgl.me/ice" style="color:blue">ice</a>
       </body>
       ''' % {'msg': msg}]

if __name__ == '__main__':

  parser = argparse.ArgumentParser(description="Flash some LEDs")
  parser.add_argument( '-w', action='store_true', dest='use_websockets')
  parser.add_argument( '-s', action='store_true', dest='use_server')
  parser.add_argument( '-d', action='store_true', dest='dry_run')
  args = parser.parse_args()

  if args.dry_run:
    strip = dummy_strip()
  else:
    from neopixel import *

    # Create and initialize NeoPixel object
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    strip.begin()

  signal.signal(signal.SIGINT, signal_handler)

  p = threading.Thread(target=painter)
  p.daemon = True
  p.start()

  print "Welcome to piLights"
  print ""

  if args.use_server:
    print "Starting web server..."
    srv = make_server('192.168.1.20', 80, server)
    s = threading.Thread(target=lambda: srv.serve_forever())
    s.daemon = True
    s.start()

  if args.use_websockets:
      print "Using websockets..."
      srv = make_server('192.168.1.120', 9000, server_class=WSGIServer,
                        handler_class=WebSocketWSGIRequestHandler,
                        app=WebSocketWSGIApplication(handler_cls=PiWebSocket))
      srv.initialize_websockets_manager()
      s = threading.Thread(target=lambda: srv.serve_forever())
      s.daemon = True
      s.start()


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

