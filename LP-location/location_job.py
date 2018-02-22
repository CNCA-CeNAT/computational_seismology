#!/opt/intel/intelpython35/bin/python3

#PBS -N tremor_location
#PBS -q phi-n2h72
#PBS -l nodes=2:ppn=64
#PBS -l walltime=23:00:00 

import modules
import sys

modules.load('intelpython/3.5')

exe = '/home/gmocornejos/computational_seismology/LP-location/body_waves_topology/location_topo_mpi.py'

conf = '/home/gmocornejos/computational_seismology/LP-location/body_waves_topology/location.conf'

try:
    configuration = sys.argv[1]
except IndexError:
    raise SystemExit('configuration no specified at command line')

modules.run('mpirun python ' + exe + ' ' + conf + ' ' + sys.argv[1])


