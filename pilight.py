# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.  #
# jglukasik - making some changes of my own to learn this api

import argparse
import random
import signal
import sys
import threading
import time
import urlparse

from wsgiref.simple_server import make_server
from Queue import Queue
from neopixel import *


# LED strip configuration:
LED_COUNT      = 150      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

# Messaging queue for main input thread to communicate with led painter
mq = Queue()

# from http://stackoverflow.com/questions/214359/converting-hex-color-to-rgb-and-vice-versa
def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

# Handle ctrl-c
def signal_handler(signal, frame):
  print('Exiting...')
  sys.exit(0)

def painter():
  # Create and initialize NeoPixel object
  strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
  strip.begin()

  runners = []
  wait_ms = 100
  new_chance = 0.2
  streak_length = 50
  run = True
  message = ''
  while True:
    if run:
      for i in range(strip.numPixels()):
        strip.setPixelColorRGB(i,100,100,100)
      for r in runners:
        if r[0] >= 0:
          strip.setPixelColorRGB(*r)
      strip.setBrightness(60)
      strip.show()
      time.sleep(wait_ms/1000.0)
      last_runner = runners[-1:]
      if random.random() < new_chance and (not runners or runners[-1][0] > 0):
        runners.append([0,random.randint(0,255),random.randint(0,255),random.randint(0,255)])
      for r in runners:
        r[0] = r[0] + 1
        if r[0] > strip.numPixels():
          runners.remove(r)

    if not mq.empty():
      message = mq.get()

    if message == "stop":
      run = False
    elif message == "start" or message == "on":
      run = True
    elif message == "off":
      run = False
      strip.setBrightness(0)
      strip.show()
    elif message == "fire":
      g = range(0,256,256/streak_length)
      for x in range(0, streak_length):
        runners.append([-x, 255, g[x], 0])
    elif message == "quit":
      return
    
    message = ''

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
       </body>
       ''' % {'msg': msg}]

if __name__ == '__main__':

  parser = argparse.ArgumentParser(description="Flash some LEDs")
  parser.add_argument( '-s', action='store_true', dest='use_server')
  args = parser.parse_args()

  signal.signal(signal.SIGINT, signal_handler)

  t = threading.Thread(target=painter)
  t.daemon = True
  t.start()
  
  print "Welcome to piLights"
  print ""

  if args.use_server:
    print "Starting web server..."
    srv = make_server('192.168.1.20', 80, server)
    srv.serve_forever()

  thing = ''
  while t.isAlive():
    thing = raw_input('Send message: ')
    mq.put(thing)

  print 'Closing painter...'
  while t.isAlive():
    pass

  print 'Goodbye!'

