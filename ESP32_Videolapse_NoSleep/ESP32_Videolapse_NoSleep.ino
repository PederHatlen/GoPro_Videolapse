#include <FastLED.h>

#define relay_pin 13

#define RX1       9
#define TX1       7

#define LED_PIN   21
#define LED_NUM   1

#define RPI_WAIT  60

CRGB leds[LED_NUM];

void setup() {
  /* Start power to camera system */
  pinMode(relay_pin, OUTPUT);

  /* Initiate RGB Led */
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, LED_NUM);

  /* Connect serial -> wait for connection -> send "hello i exist" */

  USBSerial.begin();
}

void loop() {
  Serial1.begin(9600, SERIAL_8N1, RX1, TX1);

  leds[0] = CRGB::Red;
  FastLED.show();

  digitalWrite(relay_pin, HIGH);

  /* Wait untill rpi sends sleep time */

  long start_millis = millis();

  long timeout = 0;

  while (Serial1.available() == 0){
    delay(1000);
    if ((millis() - start_millis) > 600000) timeout = 70;
  }

  USBSerial.println((String)"RaspberryPi has booted after "+String((millis()-start_millis)/1000)+" seconds");
  
  while (timeout == 0){
    delay(1000);
    Serial1.println("Waiting for data");
    USBSerial.println("Waiting for data");
    timeout = Serial1.parseInt();
    // timeout = USBSerial.parseInt();
    if ((millis() - start_millis) > 600000) timeout = 70;
  }

  long final_sleep = (timeout <= (RPI_WAIT+10))? 10:(timeout-RPI_WAIT);

  leds[0] = CRGB::Blue;
  FastLED.show();

  Serial1.println((String)"Seconds untill wakeup: "+String(final_sleep+60));
  USBSerial.println((String)"Seconds untill wakeup: "+String(final_sleep+60));

  /* Delay for 1 minute, ensure safe raspi shutdown */
  delay(RPI_WAIT * 1000);

  FastLED.clear(true);

  digitalWrite(relay_pin, LOW);

  delay(final_sleep * 1000);
}
