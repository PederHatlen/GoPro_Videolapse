#include <FastLED.h>

#define uS_TO_S_FACTOR 1000000  /* Conversion factor for micro seconds to seconds */

#define relay_pin1 13
#define relay_pin2 15

#define RX1 9
#define TX1 7

#define PIN_LED    21
#define NUM_LEDS   1

CRGB leds[NUM_LEDS];

void setup() {
  // Start power to camera system
  pinMode(relay_pin1, OUTPUT);
  pinMode(relay_pin2, OUTPUT);

  // Initiate RGB Led
  FastLED.addLeds<WS2812, PIN_LED, GRB>(leds, NUM_LEDS);

  // Connect serial -> wait for connection -> send "hello i exist"
  Serial1.begin(9600, SERIAL_8N1, RX1, TX1);
  leds[0] = CRGB::Red;
  FastLED.show();

  digitalWrite(relay_pin1, HIGH);
  digitalWrite(relay_pin2, HIGH);

  Serial1.println("Hello i exist");

  leds[0] = CRGB::Green;
  FastLED.show();

  // Wait untill rpi sends sleep time

  long timeout = 0;

  while (timeout == 0){
    delay(1000);
    Serial1.println("Waiting for data");
    timeout = Serial1.parseInt();
  }

  Serial1.println((String)"Seconds untill wakeup: "+String(timeout));
  Serial1.println("Waiting 60 seconds first...");

  leds[0] = CRGB::Blue;
  FastLED.show();

  delay(60000);

  FastLED.clear();
  FastLED.show();

  digitalWrite(relay_pin1, LOW);
  digitalWrite(relay_pin2, LOW);

  esp_sleep_enable_timer_wakeup(timeout*uS_TO_S_FACTOR);
  esp_deep_sleep_start();
  // delay(timeout*1000);
}

void loop() {}
