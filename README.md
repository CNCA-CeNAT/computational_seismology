# Framework para la simulación en paralelo de fenómenos sísmicos y volcánicos

## Pre-simulación

*order\_xyz.py* Toma un archivo xyz, tal como lo exporta QGIS y lo transforma al formato adecuado para simular con specfem3D.

*cmp_synth* Toma una colección de sismogramas, empacados en un .mseed y los compara con los sismogramas sintéticos contenidos en un directorio. Los nombres de los sismogramas sintéticos y observados deben coincidir. 
