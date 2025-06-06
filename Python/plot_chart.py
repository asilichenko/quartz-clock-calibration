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


import matplotlib.pyplot as plt
import numpy as np

PADDING = 0.05

ALPHA = 0.1

BARE = 'bare'

TRIAL_5_1_5 = '5.1+(_5/20)'
TRIAL_5_1_20 = '5.1+(5/_20)'
GROUP_5_1 = '5.1+(5/20)'

TRIAL_10_5 = '10+(_5/20)'
TRIAL_10_20 = '10+(5/_20)'
GROUP_10 = f'10+(5/20)'

TRIAL_22_5 = '22+(_5/20)'
TRIAL_22_20 = '22+(5/_20)'
GROUP_22 = '22+(5/20)'

# Lines

RAW = 'raw'
EMA = 'ema'
POLY = 'poly'

COLOR_PALETTE = {
    BARE: {RAW: '#1E90FF', EMA: '#87CEEB', POLY: '#104E8B'},

    TRIAL_5_1_5: {RAW: '#FF4500', EMA: '#FF8C69', POLY: '#8B2500'},
    TRIAL_5_1_20: {RAW: '#32CD32', EMA: '#90EE90', POLY: '#228B22'},
    GROUP_5_1: '#FF6347',

    TRIAL_10_5: {RAW: '#FF1493', EMA: '#FF69B4', POLY: '#8B008B'},
    TRIAL_10_20: {RAW: '#FFD700', EMA: '#FFEC8B', POLY: '#8B7500'},
    GROUP_10: '#FF82AB',

    TRIAL_22_5: {RAW: '#00CED1', EMA: '#48D1CC', POLY: '#00868B'},
    TRIAL_22_20: {RAW: '#9400D3', EMA: '#C71585', POLY: '#4B0082'},
    GROUP_22: '#6A5ACD'
}


def read_csv(file_path, delimiter=';', skiprows=1) -> tuple:
    """
    Read a CSV file into two numpy arrays (assuming two columns).

    Args:
        file_path (str): Path to the CSV file.
        delimiter (str): Delimiter used in the CSV file (default: comma).
        skiprows (int): Number of rows to skip (e.g., 1 for header).

    Returns:
        tuple: Two numpy arrays (first column, second column).
    """
    try:
        # Load CSV data into a numpy array
        data = np.loadtxt(file_path, delimiter=delimiter, skiprows=skiprows)

        # Check if the CSV has at least two columns
        if data.shape[1] < 2:
            raise ValueError("CSV file must have at least two columns")

        # Split into two arrays (first and second columns)
        array1 = data[:, 0]  # First column
        array2 = data[:, 1]  # Second column

        return array1, array2

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return None, None
    except ValueError as e:
        print(f"Error: {str(e)}")
        return None, None
    except Exception as e:
        print(f"Error reading CSV: {str(e)}")
        return None, None


def plot_data(plot, file_name: str, label: str, colors):
    actual_time_arr, measured_time_arr = read_csv(file_name)

    delta_arr = measured_time_arr - actual_time_arr
    delta_ema_arr = np.zeros(shape=len(actual_time_arr))
    for i in range(delta_arr.shape[0]):
        delta = delta_arr[i]
        delta_ema_arr[i] = delta if 0 == i else ALPHA * delta + (1 - ALPHA) * delta_ema_arr[i - 1]

    coefficients = np.polyfit(actual_time_arr, delta_ema_arr, 1)
    polynomial = np.poly1d(coefficients)

    reg_x = [min(actual_time_arr), max(actual_time_arr)]
    regression_line = polynomial(reg_x)

    plot.plot(actual_time_arr, delta_arr, label=f'{label}: RAW', color=colors[RAW])
    plot.plot(actual_time_arr, delta_ema_arr, label=f'{label}: EMA', color=colors[EMA])
    plot.plot(reg_x, regression_line, label=f'{label}: {coefficients[0] * 1e6:+.1f}ppm', color=colors[POLY])

    return polynomial


def draw_area(plot, x_common, polynomial1, polynomial2, label, color):
    y1 = polynomial1(x_common)
    y2 = polynomial2(x_common)
    plot.fill_between(x=x_common, y1=y1, y2=y2, alpha=0.3, label=label, color=color)

    ppm1 = polynomial1.coefficients[0] * 1e6
    ppm2 = polynomial2.coefficients[0] * 1e6

    plot.set_title(f'{label}: {ppm1:+.1f}/{ppm2:+.1f}ppm')


def plot_group(plot, x_common,
               file_name_5: str, file_name_20,
               label_5: str, label_20: str, label_group):
    polynomial1 = plot_data(plot, file_name_5, label_5, COLOR_PALETTE[label_5])
    polynomial2 = plot_data(plot, file_name_20, label_20, COLOR_PALETTE[label_20])
    draw_area(plot, x_common, polynomial1, polynomial2, label_group, COLOR_PALETTE[label_group])

    y = [
        polynomial1(x_common[0]),
        polynomial1(x_common[1]),
        polynomial2(x_common[0]),
        polynomial2(x_common[1]),
    ]
    set_ylim(y, plot)


def set_ylim(y, plot):
    y_min = np.min(y)
    y_max = np.max(y)

    y_range = y_max - y_min
    y_upp = y_max + y_range * PADDING
    y_low = y_min - y_range * PADDING

    plot.set_ylim(y_low, y_upp)


def plot_bare(plot, x_common):
    polynomial0 = plot_data(plot, 'resources/bare.csv', 'Bare', COLOR_PALETTE[BARE])
    y = polynomial0(x_common)
    set_ylim(y, plot)

    ppm = polynomial0.coeffs[0] * 1e6
    plot.set_title(f'Bare: {ppm:+.1f}ppm')


def main():
    fig, axs = plt.subplots(2, 2, figsize=(10, 6))  # 2x2 = 4 charts

    x_common = [0, 600]

    plot_bare(axs[0, 0], x_common)

    plot_group(plot=axs[0, 1], x_common=x_common,
               file_name_5='resources/5.1+(_5-20).csv',
               file_name_20='resources/5.1+(5-_20).csv',
               label_5=TRIAL_5_1_5, label_20=TRIAL_5_1_20, label_group=GROUP_5_1)

    plot_group(plot=axs[1, 0], x_common=x_common,
               file_name_5='resources/10+(_5-20).csv',
               file_name_20='resources/10+(5-_20).csv',
               label_group=GROUP_10, label_5=TRIAL_10_5, label_20=TRIAL_10_20)

    plot_group(plot=axs[1, 1], x_common=x_common,
               file_name_5='resources/22+(_5-20).csv',
               file_name_20='resources/22+(5-_20).csv',
               label_group=GROUP_22, label_5=TRIAL_22_5, label_20=TRIAL_22_20)

    for ax in axs.flat:
        ax.set_xlim(x_common)
        ax.axhline(y=0, color='gray', linewidth=3)
        ax.grid(True)

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()
