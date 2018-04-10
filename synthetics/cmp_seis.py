#!/opt/intel/intelpython3/bin/python

import obspy
import obspy.clients.fdsn as fdsn
import matplotlib.pyplot as plt
import numpy as np 
import sys

usage = 'Usage: $ %s seismograms1 [seismograms2/\'iris\'] sampling_rate lowpass_freq' % sys.argv[0]

def new_cmp(self, other):
    r_value = True
    for i in ['station', 'network', 'channel', 'starttime']:
        r_value = r_value and self.stats[i] == other.stats[i]
    return r_value

obspy.Trace.__eq__ = new_cmp

def retrieve_seismograms(stream):
    client = fdsn.Client('IRIS')
    observed = obspy.Stream()
    not_found = []
    for s in stream:
        try:
            obs = client.get_waveforms(s.stats['network'], s.stats['station'], '*', '??' + s.stats['channel'][-1], s.stats['starttime'], s.stats['endtime'], attach_response=True)
            observed += obs
        except fdsn.header.FDSNException:
            print('No data for stream ' + str(s))
            not_found.append(s)
    for s in not_found:
        stream.remove(s)
    observed.remove_response(output='ACC', water_level=0)
    return observed
        
params = {'seis1':str,
          'seis2':str,
          'lowpass freq':float,
          'sampling rate':float
          }


def main():
    try:
        with open(sys.argv[1]) as param_file:
            for line in param_file:
                if line.strip()[0] == '#':
                    continue
                line = line.split('=')
                key = line[0].strip()
                if key in params.keys():
                    params[key] = params[key](line[1].strip())
    except IndexError:
        raise SystemExit('Must specify param_file')
    except FileNotFoundError as e:
        raise SystemExit(e)

    try:
        seis1 = obspy.read(params['seis1'])
        if params['seis2'] == 'iris':
            seis2 = retrieve_seismograms(seis1)
        else:
            seis2 = obspy.read(params['seis2'])
            tmp1 = []
            tmp2 = []
            for s1 in seis1:
                if s1 in seis2:
                    tmp1.append(s1)
            for s2 in seis2:
                if s2 in seis1:
                    tmp2.append(s2)
            seis1 = obspy.Stream(tmp1)
            seis2 = obspy.Stream(tmp2)
            del tmp1
            del tmp2

    except FileNotFoundError as e:
        raise SystemExit(str(e))

    seis1.resample(params['sampling rate'])
    seis2.resample(params['sampling rate'])

    seis1.filter('lowpass', freq=params['lowpass freq'])
    seis2.filter('lowpass', freq=params['lowpass freq'])

    start = max([s.stats['starttime'] for s in seis1] + [s.stats['starttime'] for s in seis2])
    end   = min([s.stats['endtime'] for s in seis1] + [s.stats['endtime'] for s in seis2])

    seis1.trim(start, end, fill_value=0)
    seis2.trim(start, end, fill_value=0)

    fig, ax = plt.subplots()
    time = np.arange(len(seis1[0])) / params['sampling rate']
    for s1, s2 in zip(seis1, seis2):
        ax.plot(time, s1.data, label='Synthetic')
        ax.plot(time, s2.data, label='Reference')
        title = '.'.join([s1.stats[k] for k in ['network', 'station', 'channel']])
        ax.set_title(title)
        ax.set_ylabel(r'Acceleration ($m/s^2$)')
        ax.set_xlabel(r'Time (s)')
        ax.legend()
        fig.tight_layout()
        fig.savefig(title + '.png')
        ax.clear()
 
if __name__ == '__main__':
    main()
