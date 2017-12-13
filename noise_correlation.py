#!/opt/intel/intelpython3/bin/python

import obspy
import obspy.clients.fdsn as fdsn

start = obspy.UTCDateTime("20150101")
end = start + 86400 # January 2nd

client = fdsn.Client('IRIS')
vtla = client.get_waveforms('OV', 'VTLA', "*", "??Z", start, end, attach_response=True)
for s in vtla:
    s.stats['sampling_rate'] = 100.0 
vtla.merge(fill_value='interpolate')
vtla.remove_response(output='ACC', water_level=0) 
vtla_ = vtla.copy()
vtla_.filter('bandpass', freqmin=1/150, freqmax=1/3) 
vtla.plot()
# vtun

