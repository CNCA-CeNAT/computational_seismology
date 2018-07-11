import pickle

with open('amplitudes-2016', 'rb') as data:
    events = pickle.load(data)
    for i in range(430//20 + 1):
        with open('amplitudes-' + chr(ord('a')+i), 'wb') as output:
            pickle.dump(events[20*i:20*(i+1)], output)
