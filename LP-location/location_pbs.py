#!/opt/intel/intelpython35/bin/python3

#PBS -N tremor_python
#PBS -q phi-n6h24
#PBS -l nodes=3:ppn=64
#PBS -l walltime=24:00:00 

import modules
import sys

modules.load('intelpython/3.5')

path = '/home/gmocornejos/computational_seismology/LP-location/'

exe = path + 'tremor_location_v2.py'
conf = path + 'location.conf'

try:
    configuration = sys.argv[1]
except IndexError:
    raise SystemExit('configuration no specified at command line')

modules.run('time mpirun python ' + exe + ' ' + conf + ' ' + sys.argv[1])


