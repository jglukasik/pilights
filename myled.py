# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.
#
# jglukasik - making some changes of my own to learn this api

import time

from neopixel import *


# LED strip configuration:
LED_COUNT      = 150      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)


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

# Main program logic follows:
if __name__ == '__main__':
  # Create NeoPixel object with appropriate configuration.
  strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
  # Intialize the library (must be called once before other functions).
  strip.begin()
  
  print 'Press Ctrl-C to quit.'
  while True:
    # colorWipe(strip, Color(255, 0, 0))  # Red wipe
    breathe();
