#!/opt/intel/intelpython35/bin/python3

#PBS -N ruido_microsismico
#PBS -q phi-n1h72
#PBS -l nodes=1:ppn=1
#PBS -l walltime=20:00:00

import modules
modules.load('intelpython/3.5')

modules.run('ipython /home/gmocornejos/ruido_microsismico/local_fetch.py')
