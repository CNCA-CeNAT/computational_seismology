import math
import pickle
import numpy as np
import os
from mpi4py import MPI

# Minimun and maximum coordinates of the search area (m)
x_i = 521000
x_f = 531000
y_i = 1102000
y_f = 1110500
z_i = -6000
z_f = 3400
# Minimum and maximum trial source amplitudes:
A_i = 0.0001
A_f = 0.007
# Steps of the search:
dx = 100
dy = 100
dz = 100
dA = 0.0001
# Parameters
f    = 1.7
beta = 2300
Q    = 50
B    = (math.pi*f)/(Q*beta)

def locate_events(events, stations):
    locations = []
    for event in events:
        min_err = math.inf
        for x in range(x_i, x_f+dx, dx):
            for y in range(y_i, y_f+dy, dy):
                for z in range(z_i, z_f+dz, dz):
                    for A in np.arange(A_i, A_f+dA, dA):
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
    return locations


def main():

    path = os.path.expanduser('~/LP-location/body_waves/')

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    if rank == 0:
        size = comm.Get_size()
        with open(path + 'amplitudes', 'rb') as data:
            events = pickle.load(data)
            events = [e for e in events if list(e.values()).count(0) == 0]
        events = [events[i::size] for i in range(size)]

        stations = {}
        with open(path + 'stations_xyz.csv') as stations_f:
            stations_f.readline()
            for station in stations_f:
                station = station.split(',')
                stations[station[0]] = (float(station[1]), float(station[2]), float(station[3]))
    else:
        events   = None
        stations = None

    events   = comm.scatter(events, root=0)
    stations = comm.bcast(stations, root=0)

    locations = locate_events(events, stations)

    locations = comm.gather(locations, root=0)

    if rank == 0:
        locations = [item for sublist in locations for item in sublist]
        print(locations)
        with open('locations_output.csv', 'w') as output:
            for hypocenter in locations:
                output.write(';'.join([str(e) for e in hypocenter]) + '\n')
                            
if __name__ == '__main__':
    main()

