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
    cells_per_core =  cells_total / size

    accum = 0
    split = []
    while accum < cells_total:
        y = accum // topo_hdr['ncols']
        x = accum % topo_hdr['ncols']
        split.append((int(y), int(x)))
        accum += cells_per_core
    split_range = [(si, sf) for si, sf in zip(split[:-1], split[1:])]
    split_range.append((split[-1], (topo_hdr['nrows'], topo_hdr['ncols'])))

    return split_range


#    ((yi, xi),(yf, xf)) = comm.scatter(split, root=0) 
# Cambiar split para que envíe el la posición inicial y final, las coordenadas las obtengo con // y %. 
def loc_minimum_error(event, stations, split, )
#   Casi que igual a locate_events en location_topo_mpi.py    


def locate_events(comm, events, stations, topo_hdr, topo):
    if comm.Get_rank() == 0:
        split = split_topography(topo_hdr, comm.Get_size())
    else:
        split = None
    split = comm.scatter(split, root=0) 
    loc = loc_minimum_error()
#   if comm.Get_rank() == 0:    
#       loc =  comm.reduce(loc, MPI.MIN)
#       locations.append(loc)
#   return locations

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

    local_events = locate_events(comm_fine, events, stations, topo_hdr, topography)
#   terminar parecido a location_topo_mpi.py
#   locations = comm_coarse
#   if comm_coarse == 0:
#       locations.gather(

if __name__ == '__main__':
    main()
