#include <FastLED.h>

#define uS_TO_S_FACTOR 1000000ULL  /* Conversion factor for micro seconds to seconds */

#define relay_pin1 13

#define RX1 9
#define TX1 7

#define PIN_LED    21
#define NUM_LEDS   1

float res;
float cur;

CRGB leds[NUM_LEDS];

unsigned long timeout = 0;

void setup() {
  analogReadResolution(12);
  USBSerial.begin(115200);
  USBSerial.println();
  USBSerial.println("boot!");

  delay(1000);

  for (int i = 0; i < 1000; i++) {
    //int analogVolts = analogReadMilliVolts(5);
    cur = 0.0066 * analogReadMilliVolts(5);
    res = (0.1 * cur) + (0.9 * res);
    delay(1);  
  }


  // Start power to camera system
  pinMode(relay_pin1, OUTPUT);

  // Initiate RGB Led
  FastLED.addLeds<WS2812, PIN_LED, GRB>(leds, NUM_LEDS);

  // Connect serial -> wait for connection -> send "hello i exist"
  Serial1.begin(9600, SERIAL_8N1, RX1, TX1);
  leds[0] = CRGB::Red;
  FastLED.show();

  digitalWrite(relay_pin1, HIGH);

  Serial1.println("Voltage:"+String(res)+";");
  USBSerial.println("Voltage:"+String(res)+";");
  
  Serial1.println("Hello i exist");
  USBSerial.println("Hello i exist");

  leds[0] = CRGB::Green;
  FastLED.show();

  // Wait untill rpi sends sleep time



  while (timeout == 0){
    delay(1000);
    Serial1.println("Waiting for data");
    USBSerial.println("Waiting for data");
    timeout = Serial1.parseInt();
    timeout = USBSerial.parseInt();
  }

  Serial1.println((String)"Seconds untill wakeup: "+String(timeout));
  Serial1.println("Waiting 60 seconds first...");

  USBSerial.println((String)"Seconds untill wakeup: "+String(timeout));
  USBSerial.println("Waiting 60 seconds first...");

  leds[0] = CRGB::Blue;
  FastLED.show();

  //delay(1000);
  delay(1000);

  FastLED.clear();
  FastLED.show();

  digitalWrite(relay_pin1, LOW);

  esp_sleep_enable_timer_wakeup(timeout*uS_TO_S_FACTOR);
  esp_deep_sleep_start();
  // delay(timeout*1000);
}

void loop() {}