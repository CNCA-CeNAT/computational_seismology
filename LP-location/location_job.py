#!/opt/intel/intelpython35/bin/python3

#PBS -N tremor_location
#PBS -q phi-n2h72
#PBS -l nodes=2:ppn=64
#PBS -l walltime=23:00:00 

import modules

modules.load('intelpython/3.5')

#modules.run('mpirun python location_mpi.py')
modules.run('mpirun python body_waves_topology/location_topo_mpi.py')


