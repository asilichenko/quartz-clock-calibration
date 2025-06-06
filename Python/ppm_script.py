# MIT License
#
# Copyright (c) 2025 Oleksii Sylichenko
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time
from datetime import datetime
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import serial

COM_PORT = "COM5"
BAUD_RATE = 9600

ALPHA = 0.1

LEGEND_LOC = 'upper left'

is_running: bool = True


def main():
    ser: serial.Serial = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)

    timer_start: Optional[float] = None

    received_start: Optional[datetime] = None
    received_prev: Optional[datetime] = None

    print('Actual Time\tMeasured Time\tDelta\tEMA\tPPM')

    actual_time_arr = []
    delta_arr = []
    delta_ema_arr = []

    delta_ema: Optional[float] = None

    while is_running:
        if ser.inWaiting() <= 0:
            continue

        response: str = ser.readline().decode().strip()
        if len('01.01.2000 00:00:00') != len(response):
            print(f'> {response}')  # to check invalid response
            continue

        timer_curr: float = time.perf_counter()
        received_time_curr: datetime = datetime.strptime(response, '%d.%m.%Y %H:%M:%S')

        if received_prev is None:
            # Start the timer only when time starts being received
            timer_start = timer_curr
            received_start = received_time_curr

            received_prev = received_start
            continue

        if received_prev == received_time_curr:  # Avoid duplications
            continue
        received_prev = received_time_curr

        actual_time: float = timer_curr - timer_start
        measured_time = int((received_time_curr - received_start).total_seconds())
        delta: float = measured_time - actual_time

        delta_ema = delta if delta_ema is None else ALPHA * delta + (1 - ALPHA) * delta_ema

        actual_time_arr.append(actual_time)
        delta_arr.append(delta)
        delta_ema_arr.append(delta_ema)

        ppm, coefs = regression(actual_time_arr, delta_ema_arr)

        update_plot(actual_time_arr, delta_arr, delta_ema_arr, ppm, coefs)

        print(f'{actual_time}\t{measured_time}\t{delta}\t{delta_ema}\t{ppm}')


def regression(x_data, y_data):
    if len(x_data) < 2:
        coefs = None
        ppm = None
    else:
        coefs = np.polyfit(x_data, y_data, 1)
        ppm = coefs[0] * 1e6
    return ppm, coefs


def update_plot(actual_time_arr, delta_raw_arr, delta_ema_arr, ppm, coeffs):
    global is_running
    is_running = plt.fignum_exists(fig.number)
    if not is_running:
        return

    fig_delta_raw.set_xdata(actual_time_arr)
    fig_delta_raw.set_ydata(delta_raw_arr)

    fig_delta_ema.set_xdata(actual_time_arr)
    fig_delta_ema.set_ydata(delta_ema_arr)

    if coeffs is not None:
        pmm_polynomial = np.poly1d(coeffs)
        x_data = np.array((actual_time_arr[0], actual_time_arr[-1]))
        y_data = pmm_polynomial(x_data)
        fig_pmm.set_xdata(x_data)
        fig_pmm.set_ydata(y_data)
        fig_pmm.set_label(f'{ppm:+.1f}ppm')

    ax.legend(loc='upper left')
    ax.relim()  # Recompute the data limits
    ax.autoscale_view()

    fig.canvas.draw()
    fig.canvas.flush_events()


def millis_per_hour(ppm: float) -> None:
    print(f'{ppm * 3.6} ms/h')


def seconds_per_day(ppm: float) -> None:
    print(f'{ppm * 86_400 / 1e6} s/d')


if __name__ == '__main__':
    plt.ion()  # Enable interactive mode.
    fig, ax = plt.subplots()
    ax.set_xlabel('Actual Time, s')

    fig_delta_raw, = ax.plot([], [], '--', color='gray', linewidth='0.5', label='Delta RAW')
    fig_delta_ema, = ax.plot([], [], color='red', linewidth='0.5', label='Delta EMA')
    fig_pmm, = ax.plot([], [], color='blue', label='PPM')

    ax.legend(loc=LEGEND_LOC)
    plt.tight_layout()

    main()
