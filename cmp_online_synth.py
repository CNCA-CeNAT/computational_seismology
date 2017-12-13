#!/opt/intel/intelpython3/bin/python

import obspy
import obspy.clients.fdsn as fdsn
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

params    = {'event_time':obspy.UTCDateTime,
              'synths_directory':lambda path: path if len(os.listdir(path)) != 0 else None,
              'simulation_step':float,
              'low_pass_freq':float              
             }

def main():
    try:
        param_file = open(sys.argv[1])
    except IndexError:
        raise SystemExit('Must specify param_file')
    except OSError:
        raise SystemExit('Error opening file ' + sys.argv[1])

    ## Load parameters
    for line in param_file:
        if '#' in line:
            continue
        line = line.split('=')
        key = line[0].strip().replace(' ', '_')
        params[key] = params[key](line[1].strip())

    ## Load synthetic seismograms to synths stream
    stats_keys = ['network', 'station', 'channel', 'delta', 'starttime', 'endtime']
    synths = obspy.Stream()
    for f in os.listdir(params['synths_directory']):
        file_name = os.path.join(params['synths_directory'], f)
        if not os.path.isfile(file_name):
            continue
        s = np.loadtxt(file_name)[:,1]    
        s_stats = f.split('.')[:3] + [params['simulation_step'], params['event_time'], params['event_time'] + len(s) * params['simulation_step']]
        s_trace = obspy.Trace(s, {k:v for k,v in zip(stats_keys, s_stats)})
        synths.append(s_trace)

    ## Connect to IRIS service and request observed seismograms for every shynthetic
    client = fdsn.Client('IRIS')
    observed = obspy.Stream()
    not_found = []
    for s in synths:
        try:
            obs = client.get_waveforms(s.stats['network'], s.stats['station'], '*', '??' + s.stats['channel'][-1], s.stats['starttime'], s.stats['endtime'], attach_response=True)
            observed += obs
        except fdsn.header.FDSNException:
            print('No data for stream ' + str(s))
            not_found.append(s)
    for s in not_found:
        synths.remove(s)
    del not_found

    ## Resample synthethics to observed seismograms frequency
    synths.resample(observed[0].stats['sampling_rate'])

    ## Remove response from observed seismograms
    observed.remove_response(output='ACC', water_level=0)

    ## Low-pass filter synths and observed seismograms
    observed.filter('lowpass', freq=params['low_pass_freq'])
    synths.filter('lowpass', freq=params['low_pass_freq'])

    ## Plot seismograms
    time = np.arange(len(synths[0])) * synths[0].stats['delta']
    fig, ax = plt.subplots()
    for obs, synth in zip(observed, synths):
        if len(obs) != len(synth):
            continue
        ax.plot(time, obs.data, label='Observed')
        ax.plot(time, synth.data, label='Synthetic')
        title = obs.stats['network'] + '.' + obs.stats['station'] + '.' + obs.stats['channel']
        ax.set_title(title)
        ax.set_ylabel(r'Acceleration ($m/s^2$)')
        ax.set_xlabel(r'Time (s)')
        ax.legend()
        fig.tight_layout()
        fig.savefig(title + '.svg')
        ax.clear()

if __name__ == '__main__':
    main()
