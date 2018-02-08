import pandas as pd
import numpy as np
from math import pi, inf, sqrt, exp
import pickle
#import unicodecsv as csv

# Read stations coordinates
read_sta = pd.read_csv('stations_xyz.csv')
sta_xyz = read_sta.to_dict(orient='record')

# Read amplitudes data
data = pickle.load(open('amplitudes','rb'))

# Minimun and maximum coordinates of the search area (m)
x_i = 521000
x_f = 531000
y_i = 1102000
y_f = 1110500
z_i = 2000
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
B    = (pi*f)/(Q*beta)

for i in range(len(data)):
	A_obs_sq_sum = 0 
	l = list(data[i].values())
	for e in range(1,len(l)):
		if np.isnan(l[e]):
			pass
		else:
			A_obs_sq_sum += l[e]**2
	data[i]['A_obs_sq_sum'] = A_obs_sq_sum

errs_stations = []
err_points_all_events = {}
locations = []

#for i in range(len(data)):
for i in range(50):
	print('event %d' % i)
	errs_sta = {}
	errs_sta['event'] = data[i]['event']
	
	location = {}
	location['event'] = data[i]['event']
	
	min_err = inf
	err_points_all_events[data[i]['event']] = []
	for x in range(x_i,x_f+dx,dx):
		point = {}
		for y in range(y_i,y_f+dy,dy):
			for z in range(z_i,z_f+dz,dz):
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
								r = sqrt((x - sta_x)**2 + (y - sta_y)**2 + (z - sta_z)**2)
								A_calc = A * exp(-B*r) / r
								err = (A_calc - A_obs)**2
								err_p = 100*sqrt(((A_calc - A_obs)**2)/(A_obs**2))
								err_acum += err
								errs_sta[station] = err_p
					Err = 100 * sqrt(err_acum/data[i]['A_obs_sq_sum'])
					err_points_all_events[data[i]['event']].append({'x':x,'y':y,'z':z,'A':round(A,3),'Err':Err})
					if Err < min_err:
						min_err = Err
						min_x = x
						min_y = y
						min_z = z
						min_A = A
						min_errs_sta = errs_sta
	errs_stations.append(min_errs_sta)
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
with open('locations.csv','wb') as output_file:
	dict_writer = csv.DictWriter(output_file,keys)
	dict_writer.writeheader()
	dict_writer.writerows(toCSV)

with open('err_points','wb') as f:
	pickle.dump(err_points_all_events, f)

with open('locations','wb') as f:
	pickle.dump(data, f)
	
with open('min_errs_stations','wb') as f:
	pickle.dump(errs_stations, f)
