import matplotlib.pyplot as plt 
import numpy as np

G = lambda a, w_0: lambda w: np.exp(-a * (w-w_0)**2)

def dispersion(signal, levels, width):
    signal_freq = np.fft.rfft(signal)
    analytic = np.zeros(len(signal), dtype=np.complex)
#    analytic[-len(signal_freq)+1:] = np.flip(signal_freq[1:], axis=0)
    analytic[-len(signal_freq)+1:] = signal_freq[1:]

    centers = np.linspace(len(analytic)//2, len(analytic), levels)
    w = np.arange(len(analytic))
    im = []
    for w_0 in centers:
        narrow_filter = G(1/width, w_0)(w) * analytic
        im.append(np.fft.ifft(narrow_filter)[width:-width])
        im[-1] = im[-1] / max(im[-1])
    im = np.array(im)
    plt.imshow(abs(im.T), aspect='auto', cmap='seismic')
#    labels = ['%d' % (centers[i]*100/len(analytic)) for i in range(levels)]
#    plt.xticks(range(levels), labels)
    plt.show()

signal = np.loadtxt('green_waveform-50s.txt') 
#signal = np.loadtxt('green_example.txt') 
levels = 100
dispersion(signal, levels, int(2*len(signal)/levels))

