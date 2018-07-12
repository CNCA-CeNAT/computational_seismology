import math
import pickle
import numpy as np
import os
import sys
from mpi4py import MPI

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


def loc_minimum_error(event, topography, stations):
    A_total     = (A_f - A_i) / dA
    z_total     = z_range / topography['cellsize']
    total_cells = topography['ncols'] * topography['nrows'] * A_total * z_total

    comm = MPI.COMM_WORLD
    num_ranks = comm.Get_size()
    rank      = comm.Get_rank()
    chunks    = total_cells // (num_ranks-1)
    if rank == num_ranks - 1:
        my_range = range(int(chunks*rank), int(chunks*rank + total_cells % (num_ranks-1)))
    else:
        my_range = range(int(chunks*rank), int(chunks*(rank+1)))

    # cell order: x, y, z, A
    x_quotient = topography['nrows'] * z_total * A_total
    y_quotient = z_total * A_total
    z_quotient = A_total

    min_err = math.inf
    for cell in my_range:
        x_index = cell // x_quotient
        y_index = (cell % x_quotient) // y_quotient
        z_index = ((cell % x_quotient) % y_quotient) // z_quotient
        A_index = ((cell % x_quotient) % y_quotient) %  z_quotient

        x = topography['xllcorner'] + x_index * topography['cellsize']
        y = topography['ylucorner'] - y_index * topography['cellsize']
        z = topography['data'][int(y_index), int(x_index)] - z_index * topography['cellsize']
        A = A_i + A_index * dA

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
            loc = [err_accum, event['event'], x, y, z, A, num_stations]
    A_obs = sum([math.pow(event[s_k], 2) for s_k in stations.keys() if not np.isnan(event[s_k])])
    loc[0] = 100.0 * math.sqrt(loc[0] / A_obs)
    return tuple(loc)


def main(events, topography, stations):
    comm = MPI.COMM_WORLD
    locations = []
    for event in events:
        loc = loc_minimum_error(event, topography, stations)
        loc = comm.reduce(loc, MPI.MIN)
        if comm.Get_rank() == 0:
                locations.append(loc)
                print(loc)
    if comm.Get_rank() == 0:
        with open(sys.argv[2] + '_output.csv', 'w') as output:
                output.write('error;event;x;y;z;amplitud;num_stations\n')
                for hypocenter in locations:
                    output.write(';'.join([str(e) for e in hypocenter]) + '\n')
        

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
    for f in ['dem', 'events', 'stations']:
        data_files[f] = path + conf_f.readline().strip().split()[-1]

    return data_files

def load_stations(station_file):
    stations = {}
    with open(station_file) as station_f:
        station_f.readline()
        for station in station_f:
            station = station.split(',')
            stations[station[0]] = tuple([float(s) for s in station[1:]])
    return stations

def load_topography(dem):
    topo_hdr_rows = 6
    with open(dem) as topo_f:
        topo = [topo_f.readline().strip().split() for r in range(topo_hdr_rows)]
        topo = {h[0]:int(float(h[-1])) for h in topo}
        topo['ylucorner'] = topo['yllcorner'] + (topo['nrows'] - 1) * topo['cellsize']
        topo['data'] = np.loadtxt(topo_f)
    return topo

if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    if comm.Get_rank() == 0:
        data_files = parse_configuration()
        stations   = load_stations(data_files['stations'])
        topography = load_topography(data_files['dem'])
        with open(data_files['events'], 'rb') as events_f:
            events = pickle.load(events_f)
    else:
        stations   = None
        topography = None
        events     = None

    stations   = comm.bcast(stations,   root=0)
    topography = comm.bcast(topography, root=0)
    events     = comm.bcast(events,     root=0)

    main(events, topography, stations)
