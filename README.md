# Framework para la simulación en paralelo de fenómenos sísmicos y volcánicos

## Pre-simulación

*order\_xyz.py* Toma un archivo xyz, tal como lo exporta QGIS y lo transforma al formato adecuado para simular con specfem3D.

*cmp_online_synth.py* un archivo de configuración con el path a un directorio que contiene los sismogramas sintéticos y los parámetros de la simulación. Se conecta con IRIS para obtener las formas de onda de los sismogramas observados, los pre-procesa y guarda un gráfico con ambos sismogramas, sintéticos y observados. 

*?\_stations* Lista de estaciones para cada red 
