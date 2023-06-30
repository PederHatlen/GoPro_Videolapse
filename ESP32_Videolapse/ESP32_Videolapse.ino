#include <FastLED.h>

#define uS_TO_S_FACTOR 1000000  /* Conversion factor for micro seconds to seconds */
#define relay_pin 13

CRGB leds[1];

void setup() {
  // Start power to camera system
  pinMode(relay_pin, OUTPUT);
  digitalWrite(relay_pin, HIGH);

  // Initiate RGB Led
  FastLED.addLeds<WS2812, 21, GRB>(leds, 1);
  FastLED.showColor(CRGB::Red);

  // Connect serial -> wait for connection -> send "hello i exist"
  USBSerial.begin(9600);

  while (!USBSerial || USBSerial.available() <= 0) {}
  USBSerial.println("Hello i exist");

  FastLED.showColor(CRGB::Green);

  // Wait untill rpi sends sleep time

  long timeout = 0;

  while (timeout == 0){
    delay(500);
    timeout = USBSerial.parseInt();
  }

  USBSerial.println((String)"Seconds untill wakeup: "+String(timeout));
  esp_sleep_enable_timer_wakeup(timeout*uS_TO_S_FACTOR);

  FastLED.clear();
  FastLED.show();

  digitalWrite(relay_pin, LOW);

  esp_deep_sleep_start();
}

void loop() {}
