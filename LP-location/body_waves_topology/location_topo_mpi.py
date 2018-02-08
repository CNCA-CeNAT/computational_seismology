import math
import pickle
import numpy as np
import os
from mpi4py import MPI

# Minimum and maximum trial source amplitudes:
A_i = 0.0001
A_f = 0.007
dA = 0.0001
# Depth to be attained
z_range = 2000
# Parameters
f    = 3.571
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
                y = topo_hdr['yllcorner'] + y_i * topo_hdr['cellsize']
                for dz in range(0, z_range, topo_hdr['cellsize']):
                    z = topography[x_i, y_i] - dz
                    for A in A_grid:
                        err_accum = 0
                        for s_k, s_v in stations.items():
                            r = math.sqrt(math.pow(x-s_v[0], 2) + math.pow(y-s_v[1], 2) + math.pow(z-s_v[2], 2))
                            A_calc = A * math.exp(-B*r) / r
                            err_accum += math.pow(A_calc - event[s_k], 2)
                        if err_accum < min_err:
                            min_err = err_accum
                            loc = [event['event'], x, y, z, A, err_accum]
        A_obs = sum([math.pow(event[s], 2) for s in stations.keys()])
        loc[-1] = 100.0 * math.sqrt(loc[-1] / A_obs)
        locations.append(loc)
        print(loc)
    return locations


def main():
    
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    path = os.path.expanduser('~/LP-location/body_waves_topology/')

    if rank == 0:
        size = comm.Get_size()
        with open(path + 'data/amplitudes', 'rb') as data:
            events = pickle.load(data)
            events = [e for e in events if sum(np.isnan([float(a) for a in e.values()])) == 0]
        events = [events[i::size] for i in range(size)]

        stations = {}
        with open(path + 'data/stations_xyz.csv') as stations_f:
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
    with open(path + 'data/dem_100m.asc') as topo_f:
        topo_hdr_rows = 6
        topo_hdr = [topo_f.readline().strip().split() for r in range(topo_hdr_rows)]
        topo_hdr = {h[0]:int(float(h[-1])) for h in topo_hdr}
        topography = np.loadtxt(topo_f)

    locations = locate_events(events, stations, topography, topo_hdr)

    locations = comm.gather(locations, root=0)

    if rank == 0:
        locations = [item for sublist in locations for item in sublist]
        print(locations)
        with open('locations_output.csv', 'w') as output:
            for hypocenter in locations:
                output.write(';'.join([str(e) for e in hypocenter]) + '\n')
 
if __name__ == '__main__':
    main()

