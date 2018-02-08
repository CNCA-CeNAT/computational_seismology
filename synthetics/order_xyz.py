import sys 
import numpy as np
import pandas as pd

X = 0
Y = 1
MIN_X = 0
MAX_X = 1
MIN_Y = 2
MAX_Y = 3

def find_corners(data):
    x_min =  float('inf')
    x_max = -float('inf')
    y_min =  float('inf')
    y_max = -float('inf')
    for d in data:
        if d[X] < x_min:
            x_min = d[X]
        if d[X] > x_max:
            x_max = d[X]
        if d[Y] < y_min:
            y_min = d[Y]
        if d[Y] > y_max:
            y_max = d[Y]
    return [x_min, x_max, y_min, y_max]

def main():
    try:
        f = open(sys.argv[1])
    except (IndexError, OSError):
        print("Usage: %s file.xyz [out]" % sys.argv[0])
        sys.exit(0)
    data = pd.read_csv(f, delimiter=" ").values
    f.close()

    corners = find_corners(data)
    same_x = []
    same_y = []
    for point in data:
        if point[X] == corners[MIN_X]:
            same_x.append(point[Y])
        if point[Y] == corners[MIN_Y]:
            same_y.append(point[X])
    same_x.sort()
    same_y.sort()
    res_x = same_x[1] - same_x[0]
    res_y = same_y[1] - same_y[0]

    nx = int((corners[MAX_X] - corners[MIN_X]) / res_x + 1)
    ny = int((corners[MAX_Y] - corners[MIN_Y]) / res_y + 1)

    new_grid = np.zeros((nx, ny), dtype=np.int64)
    for point in data:
        x = int((point[0] - corners[MIN_X]) / res_x)
        y = int((point[1] - corners[MIN_Y]) / res_y)
        new_grid[x, y] = point[2]

    try:
        out = open(sys.argv[2], "w")
    except (IndexError, OSError):
        out = sys.stdout

    print("Lat_min, long_min: (%f, %f)" % (corners[MIN_X], corners[MIN_Y]), file=out)
    print("Lat_max, long_max: (%f, %f)" % (corners[MAX_X], corners[MAX_Y]), file=out)
    print("Number of elements (%d, %d)" % (ny, nx), file=out)
    print("Resolution (%f, %f)" % (res_x, res_y), file=out)
    for x in range(nx):
        for y in range(ny):
            print(new_grid[x, y], file=out)
    out.close()
            
if __name__ == '__main__':
    main()
