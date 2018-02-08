import pandas as pd
from linecache import getline
import numpy as np
from math import pi, inf, sqrt, exp
import pickle
import unicodecsv as csv
import os.path

script_name = os.path.basename(__file__)
path_to_script = os.path.abspath(script_name)
path_to_data = path_to_script.replace(script_name,'data/')

# Minimum and maximum trial source amplitudes:
A_i = 0.0001
A_f = 0.007
dA = 0.0001
# Depth to be attained
z_range = 1000
# Parameters
f    = 3.571
beta = 2300
Q    = 50
B    = (pi*f)/(Q*beta)

# Read stations coordinates
read_sta = pd.read_csv(path_to_data+'stations_xyz.csv')
sta_xyz = read_sta.to_dict(orient='record')

# Read amplitudes data
data = pickle.load(open(path_to_data+'amplitudes','rb'))

for i in range(len(data)):
	A_obs_sq_sum = 0 
	l = list(data[i].values())
	for e in range(1,len(l)):
		if np.isnan(l[e]):
			pass
		else:
			A_obs_sq_sum += l[e]**2
	data[i]['A_obs_sq_sum'] = A_obs_sq_sum

# Read asc file with topographic grid 
source = path_to_data+'dem_100m.asc'
#source = path_to_data+'dem_10m.asc'

hdr = [getline(source,i) for i in range(1,7)]
values = [float(h.split(' ')[-1].strip()) for h in hdr]
cols,rows,x_0,y_0,cell,nd = values
cols = int(cols)
rows = int(rows)
arr = np.loadtxt(source,skiprows=6)

grid = []
for j in range(rows):
	for i in range(cols):
		point = {}
		point['x'] = x_0 + i*cell
		point['y'] = y_0 + rows*cell - cell -j*cell
		point['z'] = arr[j][i]
		grid.append(point)
		
locations = []

#for i in range(len(data)):
for i in range(1):
	min_err = inf
	location = {}
	location['event'] = data[i]['event']
	n_dz = int(z_range/cell)
	for j in range(n_dz):
		for point in grid:
			x = point['x']
			y = point['y']
			z = point['z'] - j*cell
			for A in np.arange(A_i,A_f+dA,dA):
				err_acum = 0
				for s in range(len(sta_xyz)):
					station = sta_xyz[s]['station']
					sta_x = sta_xyz[s]['x']
					sta_y = sta_xyz[s]['y']
					sta_z = sta_xyz[s]['z']
					if station in data[i]:
						if np.isnan(data[i][station]) or data[i][station] == 0:
							pass
						else:
							A_obs = data[i][station]
							r = sqrt((x-sta_x)**2 + (y-sta_y)**2 + (z-sta_z)**2)
							A_calc = A * exp(-B*r) / r
							err = (A_calc - A_obs)**2
							err_p = 100*sqrt(((A_calc - A_obs)**2)/(A_obs**2))
							err_acum += err
				Err = 100 * sqrt(err_acum/data[i]['A_obs_sq_sum'])
				if Err < min_err:
					min_err = Err
					min_x = x
					min_y = y
					min_z = z
					min_A = A
	location['x'] = min_x
	location['y'] = min_y
	location['z'] = min_z
	location['A'] = min_A
	location['Err'] = min_err
	locations.append(location)
	print("Event: %s, x = %s, y = %s, z = %s, A0 = %s, \
	Error rate(%%) = %s " % (data[i]['event'],min_x,
	min_y,min_z,min_A, round(min_err)))

toCSV = locations
keys = toCSV[0].keys()
with open(path_to_data+'locations.csv','wb') as output_file:
	dict_writer = csv.DictWriter(output_file,keys)
	dict_writer.writeheader()
	dict_writer.writerows(toCSV)