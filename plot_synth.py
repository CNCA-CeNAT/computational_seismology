#!/usr/bin/python3

import sys
import matplotlib.pyplot as plt 
import numpy as np

sufix1 = 'ENZ'
sufix2 = 'dva'

def main():
    try:
        prefix = sys.argv[1]
    except IndexError:
        print('$./' + sys.argv[0] + 'prefix')
        sys.exit(0)

    files = []
    for s1 in sufix1:
        for s2 in sufix2:
            name = prefix + s1 + '.sem' + s2
            files.append(name)
  
    x_labels = ['Aceleración', 'Velocidad', 'Desplazamiento']
    for f, n in zip(files, range(len(files))):
        seismogram = np.loadtxt(f).T
        plt.subplot(3, 3, n+1)
        plt.plot(seismogram[0], seismogram[1])
        if n % 3 == 0:
            plt.ylabel('Componente ' + sufix1[n//3])
        if 9 - (n+1) < 3:
            plt.xlabel(x_labels[9-(n+1)])

    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()
