# Calibrate Quartz Clock with Arduino

In this article, I’ll show how to measure the accuracy of a quartz-based electronic clock using Arduino and a Python script, and how to correct its timing drift using just two capacitors.

I’m working with a DS1302 real-time clock (RTC) module for Arduino. While this module is easy to use and widely available, it's also known for its poor timekeeping accuracy and long-term instability. If precision is important for your project, it’s generally better to use a more reliable RTC module such as the DS3231. However, in this article, we’ll focus on how to compensate for the DS1302’s inaccuracy through calibration techniques.

The DS1302 module I’m using suffers from a substantial positive time drift, meaning it consistently runs fast. The following table summarizes the observed deviations during testing:

- time was set as: 05.11 13:47 — 0
- time check 1: 28.11 22:00 — +3m
- time check 2: 27.03 06:00 — +18m

Based on the collected data, we can estimate the time interval required for the DS1302 to drift by one second. This allows us to quantify the module’s inaccuracy and use that value for calibration purposes.

Passed time intervals (actual time):

- "28.11 22:00" - "05.11 13:47" = 23 days, 8:13:00 = 2'016'780 s
- "27.03 06:00" - "05.11 13:47" = 141 days, 16:13:00 = 12'240'780 s

Let’s calculate how much time it takes for the DS1302 to drift by 1 second:

- 2'016'780 s / (3m * 60s) = 11'204.3 s/s = 3:06:44
- 12'240'780 s / (18m * 60s) = 11'334.05 s/s = 3:08:54

To express time drift in a standardized way, we’ll use the unit ppm (parts per million). In the context of clock accuracy, 1 ppm corresponds to a drift of 1 microsecond per second, or 1 second every 1,000,000 seconds (which is approximately 11.6 days).

For example, a clock running at +20 ppm will gain 20 seconds over the course of 1,000,000 seconds. This unit provides a convenient way to quantify and compare the accuracy of different RTC modules.

```
time_delta = measured_time - actual_time
drift = time_delta / actual_time
ppm = drift * 1_000_000

ppm_1 = (3 * 60) / 2_016_780 * 1e6 = +89.25
ppm_2 = (18 * 60) / 12'240'780 * 1e6 = +88.23
```

🧭 Typical PPM values for clocks
![Typical PPM values for clocks](https://github.com/user-attachments/assets/8e9ff73e-6792-4aed-aa3e-3b1f9d939681)

Fortunately, our module is running fast — and that’s the easier type of drift to correct. To slow it down, we’ll need at least a pair of capacitors: one fixed and one trimmer (variable) capacitor. The variable capacitor should have a tuning range of 5–20 pF.

The value of the fixed capacitor will need to be determined experimentally. At such low capacitance levels, many factors — including PCB layout, stray capacitance, and even proximity to other components — can influence the results. That’s why it’s best to prepare a few capacitor values for testing: 5 pF, 10 pF, and 22 pF.
Article content

![Time drift compensation circuit](https://github.com/user-attachments/assets/7d82d748-b065-4cba-ba04-96ef79ae2b4a)

These two capacitors are considered to be connected in series with each other, and in parallel with the crystal. Together, they increase the load capacitance seen by the crystal, which causes the oscillator to run more slowly — effectively compensating for the positive drift.

## Software development

To perform accurate and efficient ppm measurements, we’ll use a Python + Arduino setup. Arduino will read the current time from the DS1302 module and send it over the serial port. On the other end, a Python script running on the computer will read the timestamps from the serial port and compare them with the system clock to calculate the drift.

### Arduino sketch

The Arduino sketch continuously reads the current time in a loop, and whenever the time changes (i.e., a new second begins), it immediately sends the updated timestamp over the serial port.

```
void loop() {
  static String prevTime = rtc.getTimeStr();

  String timeStr = rtc.getTimeStr();
  if (prevTime.equals(timeStr)) return;
  prevTime = timeStr;
  
  String dateStr = rtc.getDateStr();
  Serial.println(dateStr + " " + timeStr);
}
```

This ensures that the PC receives each new second as soon as it occurs, enabling precise measurement of the drift relative to the system clock.

### Python script

On the receiving side, we open the serial port and continuously poll it in a loop until new data becomes available. Once data is received, we parse it as a timestamp (date and time) reported by the RTC. Then, we calculate how much actual time has passed on the computer since the previous reading — using it as the reference to evaluate the drift.

```
import time
from datetime import datetime
from typing import Optional

import serial

COM_PORT = "COM5"
BAUD_RATE = 9600


def main():
  ser: serial.Serial = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)

  timer_start: Optional[float] = None

  received_start: Optional[datetime] = None
  received_prev: Optional[datetime] = None

  while True:
    if ser.inWaiting() <= 0:
      continue

    response: str = ser.readline().decode().strip()
    if len('01.01.2000 00:00:00') != len(response):
      print(f'> {response}')  # to check invalid response
      continue

    received_time_curr: datetime = datetime.strptime(response,
                                                     '%d.%m.%Y %H:%M:%S')

    if received_prev is None:
      # Start the timer only when time starts being received
      timer_start = time.perf_counter()
      received_start = received_time_curr
      received_prev = received_time_curr
      continue

    if received_prev == received_time_curr:  # Avoid duplications
      continue
    received_prev: datetime = received_time_curr

    timer_curr: float = time.perf_counter()

    measured_time: int = int((received_time_curr - received_start)
                             .total_seconds())
    actual_time: float = timer_curr - timer_start

    delta = measured_time - actual_time
    drift = delta / actual_time
    ppm = drift * 1e6

    millis_per_hour = ppm * 3.6
    seconds_per_day = ppm * 86_400 / 1e6

    print(f'{measured_time = }')
    print(f'{actual_time = }')
    print(f'{ppm = }')
    print(f'{millis_per_hour = }')
    print(f'{seconds_per_day = }')
    print()
```

In this script, the total ppm drift is printed after each reading — calculated as the average ppm since the beginning of the measurement. In the early iterations, this value may fluctuate significantly, but over time the variation will decrease, converging to a more stable and accurate estimate:

```
measured_time = 1
actual_time = 0.9952034800000003
ppm = 4819.637487601779
millis_per_hour = 17350.694955366405
seconds_per_day = 416.4166789287937

...

measured_time = 1300
actual_time = 1299.883166282
ppm = 89.88016848785497
millis_per_hour = 323.5686065562779
seconds_per_day = 7.76564655735067
```

![Measurement graph for bare crystal](https://github.com/user-attachments/assets/7b946e0c-a165-4c9b-9540-fb5dafecf765)

From the diagrams above, we can draw several conclusions:

1. The total time deviation follows a linear trend, and the slope of this line represents the rate at which the RTC clock drifts from the actual system time.
2. The calculated average ppm value fluctuates significantly at the beginning of the measurement and gradually converges to a stable value over time.

As we know from linear algebra, a straight line can be described by the equation: `a * x + b`, where `a` is the slope. In our case, this slope directly corresponds to the drift rate of the clock.

The accuracy of average ppm calculation depends heavily on the measurement duration — short measurements cause large fluctuations and unreliable results. In contrast, estimating ppm from the slope of the drift graph provides a stable and accurate value much faster, as it is less affected by short-term noise.

To reduce the impact of random fluctuations and make the time drift graph smoother — without affecting its slope — we apply the EMA (Exponential Moving Average) algorithm:

```
EMA = value, if t = 0
EMA = alpha * value + (1 - alpha) * EMA, if t > 0
```

```
import numpy as np

alpha = 0.1
ema_arr = []

...

delta: float = measured_time - actual_time

if not ema_arr:
  ema = delta
else:
  ema = alpha * delta + (1 - alpha) * ema_arr[-1]

ema_arr.append(ema)

...

coefficients = np.polyfit(actual_time_arr, ema_arr, 1)
drift = coefficients[0]
ppm = drift * 1e6
```

![Bare crystal +85.4ppm](https://github.com/user-attachments/assets/a31e2b21-ca78-4889-93b0-3eac3d4adaff)

Thus, the +85.4 ppm measured over a 300-second interval is in good agreement with the long-term value of +89.25 ppm obtained over 23 days, differing by only ±3.85 ppm — an acceptable margin for practical applications.

## Choosing the Fixed Capacitor

At this stage, our primary goal is to determine the optimal value of the fixed capacitor. To achieve this, we conduct a series of experiments: in each test, we connect a different fixed capacitor and measure the resulting ppm drift at both extremes of the trimmer capacitor’s range.

The measured values are recorded in the following table.

![Experimental measured ppm values](https://github.com/user-attachments/assets/b364ee15-bb02-40c6-8920-6870e2944d74)

Our objective here is to determine the fixed capacitor value for which the ppm range (achieved by adjusting the trimmer) is most symmetric around 0 ppm. This maximizes the chances of tuning the oscillator as close to real time as possible.

![Measured PPM Spread Across Different Load Capacitances](https://github.com/user-attachments/assets/1f4d0d3f-4f3a-40b3-b04c-d336bd0e8979)

Therefore, based on the results, the fixed capacitor with a capacitance of 10 pF is the most appropriate for our application.

![+86ppm compensation circuit](https://github.com/user-attachments/assets/a1b55c8f-4e88-461a-b9be-bfd811f11f20)

Striving to achieve exactly 0 ppm is pointless, as consumer-grade clocks are significantly affected by temperature fluctuations. Even if you manage to reach 0 ppm now, changes in temperature will inevitably cause the ppm to drift over time. Therefore, it is perfectly sufficient to keep the drift within ±10 ppm.

![Final result](https://github.com/user-attachments/assets/2f8e8572-639b-44ce-838a-f6b7fa36d5aa)

## Estimating the Approximate Capacitance

Since typical consumer-grade devices cannot measure capacitance in the picofarad range, we can use a substitution-based method, as discussed in this article, to estimate the approximate value of an unmarked capacitor. 

To do this, we connect one known capacitor with a value in the tens of picofarads (because when two capacitors are connected in series, the total capacitance is always less than the smallest of the two), and then we sequentially test a few capacitors of known values as the second component. For each combination, we measure the clock's ppm deviation — thus obtaining reference points.

Next, we replace the second capacitor with the unmarked one and again measure the ppm drift. Based on the result, we can estimate between which two known nominal values the unknown capacitor's value lies.

For example, in this article, we measured the ppm deviation using three known capacitor values — 5.1 pF, 10 pF, and 22 pF — with the trimmer set to 20 pF. The results were:

- 5.1 pF → −1.4 ppm
- 10 pF → −21.1 ppm
- 22 pF → −47.3 ppm

When testing the unknown capacitor, we got −40.7 ppm. This value falls between the results of the 10 pF and 22 pF capacitors and is much closer to the latter. Given the standard capacitor E-series — 10, 12, 15, 18, 22 — we can reasonably assume the unmarked capacitor has a nominal value of approximately 18 pF. 

## References

- Arduino sketch: [DS1302_send_time.ino](Arduino/DS1302_send_time/DS1302_send_time.ino)
- Poll time and calc ppm: [ppm_script.py](Python/ppm_script.py)
- Draw diagram for data: [plot_chart.py](Python/plot_chart.py)
