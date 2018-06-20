import math
import pickle
#import numpy as np
#import os
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

# for every event:
#     search my space, depending on rank # 
#     reduce min operation
def main(events, topography, stations):
#    for event in events:
    print("Llegué hasta aquí!")
        
        

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

# Read conf file
# Load amplitudes, broadcast
# Load stations,   broadcast
# Load dem,        broadcast
if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    if comm.Get_rank() == 0:
        data_files = parse_configura()
        stations   = load_stations(data_files['stations'])
        topography = load_topography(data_files['dem'])
        with open(data_files['events'], 'rb') as events_f:
            events = pickle.load(events_f)
    else:
        stations   = None
        topography = None
        events     = None

    stations   = comm.bcast(stations, root=0)
    topography = comm.bcast(topography, root=0)
    events     = comm.bcast(events)

    main(events, topography, stations)
