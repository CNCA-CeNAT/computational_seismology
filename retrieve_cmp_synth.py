#!/opt/intel/intelpython3/bin/python

import obspy
import obspy.clients.fdsn as fdsn
import numpy as np
import matplotlib.pyplot as plt
import os
import sys


def print_usage_exit():
    print('Usage: %s conf_file' % sys.argv[0])
    raise SystemExit

def parse_float(line, para_name):
    try:
        parameter = float(line.split('=')[1])
        return parameter
    except (ValueError, IndexError):
        raise SystemExit('Error parsing %s parameter' % para_name)

def main():
    try:
        param_file = open(sys.argv[1])
    except IndexError:
        print('Wrong number of parameters')
        print_usage_exit()
    except OSError:
        print('Error opening file %s' % sys.argv[1])
        print_usage_exit()

    for line in param_file:
        if '#' in line:
            continue
        elif 'event time' in line:
            try:
                time = line.split('=')[1].strip()
                event_time = obspy.core.UTCDateTime(time)
            except IndexError:
                raise SystemExit('Error parsing event time')
            except (TypeError,ValueError) as e:
                raise SystemExit('Event time parameter has wrong format: ' + str(e))
        elif 'simulation step' in line:
            simulation_step = parse_float(line, 'simulation step')
        elif 'low-pass freq' in line:
            low_pass_freq = parse_float(line, 'low-pass freq')
        elif 'prefix time' in line:
            prefix_time = parse_float(line, 'time padding prefix') * 60
        elif 'sufix time' in line:
            sufix_time = parse_float(line, 'time padding sufix') * 60
        elif 'synths directory' in line:
            try:
                path = line.split('=')[1].strip()
                files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            except (IndexError, FileNotFoundError):
                raise SystemExit('Error opening directory %s' % path)

    try:
        event_time
        files
        simulation_step
        low_pass_freq
        prefix_time
        sufix_time
    except NameError as e:
        raise SystemExit("Undefined parameter: " + str(e))

    if len(files) == 0:
        print('Directory %s is empty' % path, file=sys.stderr)
        sys.exit(1)

    ## Load synthetic seismograms to synths stream
    stats_keys = ['network', 'station', 'channel', 'delta', 'sampling_rate', 'starttime', 'endtime']
    synths = obspy.Stream()
    for f in files:
        s = np.loadtxt(os.path.join(path, f))
        s_stats = f.split('.')[:3] + [simulation_step, 1/simulation_step, event_time + s[0,0], event_time + s[-1,0]]
        s_trace = obspy.Trace(s[:,1], {k:v for k,v in zip(stats_keys, s_stats)})
        synths.append(s_trace)

    ## Connect to IRIS service and request observed seismogram for every synthethic in synths
    client = fdsn.Client('IRIS')
    observed = obspy.Stream()
    to_remove = []
    for s in synths:
        try:
            obs = client.get_waveforms(s.stats['network'], s.stats['station'], '*', '??' + s.stats['channel'][-1], s.stats['starttime'], s.stats['endtime'], attach_response=True)
            observed += obs
        except fdsn.header.FDSNException:
            print('No data for stream ' + str(s))
            to_remove.append(s)
            continue
    for s in to_remove:
        synths.remove(s)

    ## Resample synthetics seismograms to frequency of observed seismograms
    synths.resample(observed[0].stats['sampling_rate'])

    ## Remove trend, tapper, intrument response and sensitivity from
    ## observed seismograms

if __name__ == '__main__':
    main()
