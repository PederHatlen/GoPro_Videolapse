#include <FastLED.h>

#define relay_pin 13

#define RX1       9
#define TX1       7

#define LED_PIN   21
#define LED_NUM   1

#define RPI_WAIT  60

#define SECOND 1000

CRGB leds[LED_NUM];

void setup() {
  pinMode(relay_pin, OUTPUT);

  /* Initiate RGB Led */
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, LED_NUM);

  USBSerial.begin();
}

void loop() {
  /* Connect serial -> wait for connection -> send "hello i exist" */
  Serial1.begin(9600, SERIAL_8N1, RX1, TX1);

  /* Start LED */
  leds[0] = CRGB::Red;
  FastLED.show();

  /* Start power to camera system */
  digitalWrite(relay_pin, HIGH);

  long start_millis = millis();
  long timeout = 0;

  /* Wait for connection to serial */
  while (Serial1.available() == 0){
    delay(1000);
    if ((millis() - start_millis) > 600000) timeout = 70;
  }

  USBSerial.println((String)"RaspberryPi has booted after "+String((millis()-start_millis)/SECOND)+" seconds");

  String serial_buffer;
  
  /* Wait untill rpi sends sleep time */
  while (timeout == 0){
    delay(SECOND);
    // Serial1.println("Waiting for data");
    if (Serial1.available() > 0) {
      /* Atempt better data transfer (doesn't really work when getting trash over serial)*/
      USBSerial.println("Data incoming");
      for(int i = 0; i < Serial1.available(); i++){
        char c = Serial1.read();
        serial_buffer += c;
        USBSerial.println(c);
      }
      /* Finding start and end strings of message */
      int index_start = serial_buffer.indexOf("Sleep for ");
      int index_end = serial_buffer.indexOf(" seconds");

      USBSerial.println(serial_buffer.substring(index_start+10, index_end));
      
      if(index_start >= 0 && index_end >= 0){
        timeout = serial_buffer.substring(index_start+10, index_end).toInt();
      }
    }

    // timeout = Serial1.parseInt();

    // timeout = USBSerial.parseInt();
    if ((millis() - start_millis) > (600 * SECOND)) timeout = 70;
  }

  long final_sleep = (timeout <= (RPI_WAIT+10))? 10:(timeout-RPI_WAIT);

  leds[0] = CRGB::Blue;
  FastLED.show();

  Serial1.println((String)"Seconds untill wakeup: "+String(final_sleep+RPI_WAIT));
  USBSerial.println((String)"Seconds untill wakeup: "+String(final_sleep+RPI_WAIT) + ", Got "+String(timeout)+" from RPI");

  /* Delay for 1 minute, ensure safe raspi shutdown */
  delay(RPI_WAIT * SECOND);

  FastLED.clear(true);

  digitalWrite(relay_pin, LOW);

  const int delay_chunk = 10;

  // serial_buffer = "";

  for(int i = 0; i <= floor(final_sleep/delay_chunk); i++){
    // if (USBSerial.available() > 0) {
    //   for(int i = 0; i < USBSerial.available(); i++){serial_buffer += USBSerial.read();}
    //   if(serial_buffer.indexOf("Force the system to start") >= 0){
    //     USBSerial.println("Starting by request from USB");
    //     return;
    //   }
    // }

    USBSerial.println((String)String(final_sleep-(delay_chunk*i)) + " seconds left untill wakeup");
    delay(delay_chunk * SECOND);
  }

  // USBSerial.println((String)String(final_sleep%delay_chunk) + " seconds left untill wakeup");

  delay((final_sleep%delay_chunk) * SECOND);
}
