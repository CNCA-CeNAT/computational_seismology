import math
import pickle
import numpy as np
import os
import sys
import socket
from mpi4py import MPI

def main():

    comm_global = MPI.COMM_WORLD
    rank_global = comm_global.Get_rank()

    ip = int(socket.gethostbyname(socket.gethostname()).replace('.', ''))
    comm_fine_grained = comm_global.Split(ip)
    rank_fine_grained = comm_fine_grained.Get_rank()

    if rank_fine_grained == 0:
        comm_coarse_grained = comm_global.Split(rank_fine_grained)
        rank_coarse_grained = comm_coarse_grained.Get_rank()
    else:
        comm_global.Split(MPI.UNDEFINED)

    
if __name__ == '__main__':
    main()
