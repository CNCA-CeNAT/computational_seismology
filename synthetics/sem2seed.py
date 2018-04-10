#!/opt/intel/intelpython3/bin/python

import obspy
import numpy as np
import os
import sys

params = {'event time':obspy.UTCDateTime,
              'directory':str,
              'simulation step':float,
              'low pass freq':float,
              'output name':str
             }

def main():
    # Load parameters
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
    except FileNotFoundError:
        raise SystemExit('Error opening file ' + sys.arv[1])

    # Load synthetic seismograms to synths stream
    stats_keys = ['network', 'station', 'channel', 'delta', 'starttime', 'endtime']
    synths = obspy.Stream()
    for f in os.listdir(params['directory']):
        file_name = os.path.join(params['directory'], f)
        if not os.path.isfile(file_name):
            continue
        s = np.loadtxt(file_name)[:,1]
        network, station, channel = f.split('.')[:3]
        s_stats = [network, station, channel[-1], params['simulation step'], params['event time'], params['event time'] + len(s)*params['simulation step']]
        s_trace = obspy.Trace(s, {k:v for k,v in zip(stats_keys, s_stats)})
        synths.append(s_trace)
    synths.write(params['output name'], format='MSEED')

if __name__ == '__main__':
    main()
