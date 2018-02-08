import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import time
import obspy 
import numpy as np

import sys
import threading

# Global constants
path1 = '/home/gmocornejos/ruido_microsismico/data/Turrialba-Calle_Vargas_%d.tar.mseed'
path2 = '/home/gmocornejos/ruido_microsismico/data/Turrialba-Crater_central_%d.tar.mseed'
sr          = 100            # sampling rate
period      = 50
green_len   = period*sr        # half green function
inv = obspy.read_inventory('/home/gmocornejos/ruido_microsismico/microseismic-all_stations.dataless')

# Global variables
num_of_days = 29


def moving_average(signal, N):
    cumsum = np.cumsum(abs(signal))
    weights = (cumsum[N:] - cumsum[:-N]) / float(N)
    return weights 

def spectral_whitening(signal, N):
    signal_freq = np.fft.rfft(signal)
    freq_weights = moving_average(abs(signal_freq), N)
    signal_white = signal_freq[N//2:-N//2] / freq_weights
    return np.fft.irfft(signal_white)

def preprocess_and_clean(stream, inv, sr, freq_min, freq_max, freq_seis):
    # set all traces to same sampling rate
    for trace in stream:
        trace.stats['sampling_rate'] = sr
    stream.merge(fill_value=0)
    t = stream[0].stats['starttime']
    stream.trim(t, t+86400, pad=True, fill_value=0)

    # Remove instrumen response
    stream.detrend(type='linear')
    stream.remove_response(inventory=inv, output='DISP', water_level=0)

    # get moving average from seismic band
    N = int(0.5/freq_min * sr)
    seismic_band = stream.copy()
    seismic_band.filter('lowpass', freq=freq_seis)
    weights = moving_average(seismic_band[0].data, N)

    # filter and temporal whitening 
    stream.filter('bandpass', freqmin=freq_min, freqmax=freq_max)
    signal = stream[0].data[N//2:-N//2] / weights
    
    return spectral_whitening(signal, N)[sr:-sr]


def stack_a_day(green, day_mutex, green_mutex):
    global num_of_days

    # do-while construction
    while(True):
        day_mutex.acquire()
        current_day = num_of_days
        num_of_days -= 1
        day_mutex.release()
        if current_day < 0:
            break
        signal1 = preprocess_and_clean(obspy.read(path1 % current_day), inv, sr, 1/150, 1/7, 0.11)
        signal2 = preprocess_and_clean(obspy.read(path2 % current_day), inv, sr, 1/150, 1/7, 0.11)
        partial_green = np.correlate(signal1, signal2[green_len:-green_len])
        green_mutex.acquire()
        green += partial_green
        green_mutex.release()

def main():
    day_mutex   = threading.Lock()
    green_mutex = threading.Lock()
    green       = np.zeros(2*green_len+1)

    num_cores = 32

    threads = [threading.Thread(target=stack_a_day, args=(green, day_mutex, green_mutex)) for c in range(num_cores)]

    start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    end = time.time()

    t = np.linspace(-period, period, 2*green_len+1)
    fig, ax = plt.subplots()
    ax.plot(t, green)
    ax.spines['left'].set_position('center')
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.set_xlabel('Time (s)')
    fig.savefig('Green_function-50s.png')

    np.savetxt('green_waveform-50s.txt', green)

    print('Elapsed time %f' % (end-start))

if __name__ == '__main__':
    main()

