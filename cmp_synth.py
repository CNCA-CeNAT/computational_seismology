#!/opt/intel/intelpython3/bin/python

import matplotlib.pyplot as plt
import numpy as np
import obspy 
import sys
import os
import re

Trillium_seimometer_response = {
    'poles':[-272+218j, -272-218j, 56.5+0j, -0.1111-0.1111j, -0.0000+0.1111j],
    'zeros':[0j, 0j, 51.5+0j],
    'gain' :133310,
    'sensitivity':1500
}

def match_streams(stream, files):
    file_name = stream.stats['network'] + '.' + stream.stats['station'] + '.[A-Z]+' + stream.stats['channel'][-1] + '.sema'
    for f in files:
        if re.search(file_name, f):
            return f
    return None

def print_usage_exit():
    print('Usage: %s observed_seismograms.mseed path_to_synths synth_step corner_freq' % sys.argv[0])
    sys.exit(1)


def main():
    try:
        recorded = obspy.read(sys.argv[1])
        directory = sys.argv[2]
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        synth_step  = float(sys.argv[3])
        corner_freq = float(sys.argv[4])
    except OSError:
        print("Error openning file or directory")
        print_usage_exit()
    except IndexError:
        print('Wrong number of arguments')
        print_usage_exit()
    except ValueError:
        print('Check synth_step or corner_freq format')
        print_usage_exit()

    # Match all observed seismograms with a synthetic one in "directory"
    synths   = []
    observed = []
    for stream in recorded:
        synth_file = match_streams(stream, files)
        if not synth_file:
            print('Stream %s has no match in directory %s' % (stream.stats['network'] + '.' + stream.stats['station'] + '.' + stream.stats['channel'],  directory))
        else:
            observed.append(stream)
            synth_data = np.loadtxt(os.path.join(directory, synth_file))
            synth = obspy.Trace(synth_data[:,1])
            synth.stats['delta'] = synth_step 
            synths.append(synth)
    del recorded

    # Resample synthetics to frequency of observed seimograms
    new_delta = observed[0].stats['delta']
    for synth in synths:
        synth.resample(1/new_delta)

    # Remove the trend and taper observed seismograms
    # Remove instrument response and sensivity
    for stream in observed:
        stream.detrend(type='linear')
        stream.simulate(paz_remove=Trillium_seimometer_response, remove_sensitivity=True, water_level=0, taper_fraction=0.05)
    
    # Low-pass filter
    for obs, synth in zip(observed, synths):
        obs.filter('lowpass', freq=corner_freq)
        obs.data = obs.data / np.max(obs.data)
        synth.filter('lowpass', freq=corner_freq)
        synth.data = synth.data / np.max(synth.data)

    # Synchronize seismograms using correlation
    synch_index = []
    for obs, synth in zip(observed, synths):
        synch_index.append(np.argmax(np.correlate(obs, synth)))
    
    # Plot seimograms
    time = new_delta * np.arange(len(synths[0]))
    for obs, synth, i in zip(observed, synths, synch_index):
        fig, ax = plt.subplots()
        try:
            ax.plot(time, obs.data[i:i+len(time)], label="Observed")
        except:
            print("Error ploting stream " + str(obs))
            continue
        title = obs.stats['network'] + '.' + obs.stats['station'] + '.' + obs.stats['channel']
        ax.plot(time, synth.data, label="Synthetic")
        ax.set_title(title)
        ax.set_ylabel(r'Acceleration ($m/s^2$)')
        ax.set_xlabel('Time (s)')
        ax.legend()
        fig.tight_layout()
        fig.savefig(title + '.png')

if __name__ == '__main__':
    main()
