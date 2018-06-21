import math
import pickle
import numpy as np
import os
import sys
import socket
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


def create_communicators():
    comm_global = MPI.COMM_WORLD

    ip = int(socket.gethostbyname(socket.gethostname()).replace('.', ''))
    comm_fine_grained = comm_global.Split(ip)

    comm_coarse_grained = None
    color = 0
    if comm_fine_grained.Get_rank() == color:
        comm_coarse_grained = comm_global.Split(color)
    else:
        comm_global.Split(MPI.UNDEFINED)

    return comm_global, comm_fine_grained, comm_coarse_grained

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
        topo_hdr = [topo_f.readline().strip().split() for r in range(topo_hdr_rows)]
        topo_hdr = {h[0]:int(float(h[-1])) for h in topo_hdr}
        topo_hdr['ylucorner'] = topo_hdr['yllcorner'] + (topo_hdr['nrows'] - 1) * topo_hdr['cellsize']
        topography = np.loadtxt(topo_f)
    return topo_hdr, topography

def split_topography(topo_hdr, size):
    cells_total = topo_hdr['ncols'] * topo_hdr['nrows']
    cells_per_core =  cells_total // size

    accum = 0
    split = []
    while accum < cells_total:
        split.append((accum, accum+cells_per_core))
        accum += cells_per_core
    split[-1] = (split[-1][0], cells_total)

    return split

def loc_minimum_error(event, stations, topo_hdr, topography, split):
    A_grid = np.arange(A_i, A_f+dA, dA)
    z_grid = np.arange(0, z_range, topo_hdr['cellsize'])
    min_err = math.inf

    y_i = split[0] // topo_hdr['ncols'] 
    y   = topo_hdr['ylucorner'] - y_i * topo_hdr['cellsize']
    for cell in range(split[0], split[1]):
        x_i = cell % topo_hdr['ncols']
        x   = topo_hdr['xllcorner'] + x_i * topo_hdr['cellsize']
        if x_i == 0:
            y_i = cell // topo_hdr['ncols']
            y   = topo_hdr['ylucorner'] - y_i * topo_hdr['cellsize']
        for dz in z_grid:
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
                    loc = [err_accum, event['event'], x, y, z, A, num_stations]
    A_obs = sum([math.pow(event[s_k], 2) for s_k in stations.keys() if not np.isnan(event[s_k])])
    loc[0] = 100.0 * math.sqrt(loc[0] / A_obs)
    return tuple(loc)


def locate_events(comm, events, stations, topo_hdr, topo):
    if comm.Get_rank() == 0:
        split = split_topography(topo_hdr, comm.Get_size())
    else:
        split = None
    split = comm.scatter(split, root=0) 
    
    locations = []
    for event in events:
        loc = loc_minimum_error(event, stations, topo_hdr, topo, split)
        loc = comm.reduce(loc, MPI.MIN)
        if comm.Get_rank() == 0:
            locations.append(loc)
    return locations

def main():
    comm_global, comm_fine, comm_coarse = create_communicators()
    data_files = parse_configuration()
    stations = load_stations(data_files['stations'])
    topo_hdr, topography = load_topography(data_files['dem'])

    if comm_coarse != None:
        if comm_coarse.Get_rank() == 0:
            size = comm_coarse.Get_size()
            with open(data_files['events'], 'rb') as events_f:
                events = pickle.load(events_f)
            events = [events[i::size] for i in range(size)]
        else:
            events = None
        events = comm_coarse.scatter(events, root=0)
    else:
        events = None
    events = comm_fine.bcast(events, root=0)

    delegated_events = locate_events(comm_fine, events, stations, topo_hdr, topography)

    if comm_coarse != None:
        locations = comm_coarse.gather(delegated_events, root=0)

    if comm_global.Get_rank() == 0:
        locations = [item for sublist in locations for item in sublist]
        print(locations)
        with open(sys.argv[2] + '_output.csv', 'w') as output:
            output.write('error;event;x;y;z;amplitud;num_stations\n')
            for hypocenter in locations:
                output.write(';'.join([str(e) for e in hypocenter]) + '\n')
        
if __name__ == '__main__':
    main()
