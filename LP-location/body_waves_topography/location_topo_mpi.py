import math
import pickle
import numpy as np
import os
from mpi4py import MPI
import sys

# Minimum and maximum trial source amplitudes:
A_i = 0.0
A_f = 0.007
dA  = 0.0001
# Depth to be attained
z_range = 2000
# Parameters
f    = 2
beta = 2300
Q    = 50
B    = (math.pi*f)/(Q*beta)

def locate_events(events, stations, topography, topo_hdr):
    locations = []
    A_grid = np.arange(A_i, A_f+dA, dA)
    for event in events:
        min_err = math.inf
        for x_i in range(topo_hdr['ncols']):
            x = topo_hdr['xllcorner'] + x_i * topo_hdr['cellsize']
            for y_i in range(topo_hdr['nrows']):
                y = topo_hdr['ylucorner'] - y_i * topo_hdr['cellsize']
                for dz in range(0, z_range, topo_hdr['cellsize']):
                    z = topography[y_i, x_i] - dz
                    for A in A_grid:
                        err_accum = 0
                        for s_k, s_v in stations.items():
                            if np.isnan(event[s_k]):
                                continue
                            r = math.sqrt(math.pow(x-s_v[0], 2) + math.pow(y-s_v[1], 2) + math.pow(z-s_v[2], 2))
                            A_calc = A * math.exp(-B*r) / r
                            err_accum += math.pow(A_calc - event[s_k], 2)
                        if err_accum < min_err:
                            min_err = err_accum
                            num_stations = len(stations) - sum([np.isnan(event[s_k]) for s_k in stations.keys()])
                            loc = [event['event'], x, y, z, A, num_stations, err_accum]
        A_obs = sum([math.pow(event[s], 2) for s in stations.keys() if not np.isnan(event[s])])
        loc[-1] = 100.0 * math.sqrt(loc[-1] / A_obs)
        locations.append(loc)
        print(loc)
    return locations

def parse_configuration():
    usage = '\n$ ./%s conf_file configuration' % sys.argv[0]

    try:
        conf_f = open(sys.argv[1])
    except IndexError:
        raise SystemExit('conf file not given' + usage)
    except FileNotFoundError:
        raise SystemExit('%s file not found' % sys.argv[1] + usage)

    for line in conf_f:
        try:
            if sys.argv[2] ==  line.strip():
                break
        except IndexError:
            raise SystemExit('conf not specified' + usage)
    else:
        raise SystemExit('%s don\'t match any configuration' % sys.argv[2])
    data_files = {}
    path = os.path.expanduser(conf_f.readline().strip().split()[-1])
    for f in ['dem', 'amplitudes', 'stations']:
        data_files[f] = path + conf_f.readline().strip().split()[-1]

    return data_files

def main():
    
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    data_files = parse_configuration()

    if rank == 0:
        size = comm.Get_size()
        with open(data_files['amplitudes'], 'rb') as data:
            events = pickle.load(data)
        events = [events[i::size] for i in range(size)]

        stations = {}
        with open(data_files['stations']) as stations_f:
            stations_f.readline()
            for station in stations_f:
                station = station.split(',')
                stations[station[0]] = (float(station[1]), float(station[2]), float(station[3]))

    else:
        events   = None
        stations = None

    events   = comm.scatter(events, root=0)
    stations = comm.bcast(stations, root=0)

    # load topography header
    with open(data_files['dem']) as topo_f:
        topo_hdr_rows = 6
        topo_hdr = [topo_f.readline().strip().split() for r in range(topo_hdr_rows)]
        topo_hdr = {h[0]:int(float(h[-1])) for h in topo_hdr}
        topo_hdr['ylucorner'] = topo_hdr['yllcorner'] + (topo_hdr['nrows'] - 1) * topo_hdr['cellsize']
        topography = np.loadtxt(topo_f)

    locations = locate_events(events, stations, topography, topo_hdr)

    locations = comm.gather(locations, root=0)

    if rank == 0:
        locations = [item for sublist in locations for item in sublist]
        print(locations)
        with open(sys.argv[2] + '_output.csv', 'w') as output:
            output.write('event;x;y;z;amplitud;num_stations;error\n')
            for hypocenter in locations:
                output.write(';'.join([str(e) for e in hypocenter]) + '\n')
 
if __name__ == '__main__':
    main()

