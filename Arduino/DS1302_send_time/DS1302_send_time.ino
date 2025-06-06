/*
  MIT License

  Copyright (c) 2025 Oleksii Sylichenko

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.
*/

#include <DS1302.h>

const int CLK_PIN = 2;
const int DAT_PIN = 3;
const int RST_PIN = 4;

DS1302 rtc(RST_PIN, DAT_PIN, CLK_PIN);

void setup() {
  Serial.begin(9600);
  while (!Serial);
}

void loop() {
  static String prevTime = rtc.getTimeStr();

  String timeStr = rtc.getTimeStr();
  if (prevTime.equals(timeStr)) return;
  prevTime = timeStr;

  String dateStr = rtc.getDateStr();
  Serial.println(dateStr + " " + timeStr);
}
