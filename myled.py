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


mq = Queue()

# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=5):
  """Wipe color across display a pixel at a time."""
  for i in range(strip.numPixels()):
    for j in range(strip.numPixels()-i):
      if (j-1) >= 0: strip.setPixelColor(j-1, Color(0,0,0))
      strip.setPixelColor(j, wheel(((i * 256 / strip.numPixels())) & 255))
      strip.show()
      time.sleep(wait_ms/1000.0)

def wheel(pos):
	"""Generate rainbow colors across 0-255 positions."""
	if pos < 85:
		return Color(pos * 3, 255 - pos * 3, 0)
	elif pos < 170:
		pos -= 85
		return Color(255 - pos * 3, 0, pos * 3)
	else:
		pos -= 170
		return Color(0, pos * 3, 255 - pos * 3)


def breathe(wait_ms=300):
  for i in range(190, 256):
    for j in range(140, strip.numPixels()):
      strip.setPixelColorRGB(j,255,255,255)
    strip.setBrightness(i)
    strip.show()
    time.sleep(wait_ms/1000.0)

def on():
  for j in range(0, strip.numPixels()):
    strip.setPixelColorRGB(j,255,255,255)
  strip.setBrightness(60)
  strip.show()

def off():
  strip.setBrightness(0)
  strip.show()

def bright_loop(wait_ms=100, new_chance=0.2):
  runners = []
  while(1):
    for i in range(strip.numPixels()):
      strip.setPixelColorRGB(i,100,100,100)
    for r in runners:
      strip.setPixelColorRGB(*r)
    strip.setBrightness(60)
    strip.show()
    time.sleep(wait_ms/1000.0)
    if random.random() < new_chance:
      runners.append([0,random.randint(0,255),random.randint(0,255),random.randint(0,255)])
    for r in runners:
      r[0] = r[0] + 1
      if r[0] > strip.numPixels():
        runners.remove(r)

def signal_handler(signal, frame):
  print('Exiting...')
  sys.exit(0)

def worker():
  runners = []
  wait_ms = 100
  new_chance = 0.2
  run = True
  message = ''
  while True:
    if run:
      for i in range(strip.numPixels()):
        strip.setPixelColorRGB(i,100,100,100)
      for r in runners:
        strip.setPixelColorRGB(*r)
      strip.setBrightness(60)
      strip.show()
      time.sleep(wait_ms/1000.0)
      if random.random() < new_chance:
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

    message = ''

def hello_world(environ, start_response):
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

# Main program logic follows:
if __name__ == '__main__':
  # Create and initialize NeoPixel object
  strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
  strip.begin()

  parser = argparse.ArgumentParser(description="Flash some LEDs")
  parser.add_argument( "-p"
                     ,  "--pattern"
                     , help="select LED pattern"
                     , default="on"
                     )
  args = parser.parse_args()

  patterns = {  "on" : on
            ,  "off" : off
            , "loop" : bright_loop
            }

  # patterns[args.pattern]()

  signal.signal(signal.SIGINT, signal_handler)

  t = threading.Thread(target=worker)
  t.daemon = True
  t.start()
  
  print "Yo the loop is running"
  print ""

  print "Starting web server..."
  srv = make_server('192.168.1.20', 80, hello_world)
  srv.serve_forever()

  while True:
    thing = raw_input('Press some goddamn keys: ')
    mq.put(thing)
