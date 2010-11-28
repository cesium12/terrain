#!/usr/bin/python
import random
import numpy
import sys
import re
import viewer
from terrain import World

def real(fname='world.pgm'):
    'real-world heightmap -- file=world.pgm'
    data = map(int, re.sub(r'#.*\n', ' ', open(fname).read()).split()[1:])
    return (numpy.reshape(data[3:], (data[1], data[0])) + 1.9375) / float(data[2]) * 8 - 0.01

def flat(height=1):
    'finite plain of uniform height -- height=1'
    return World(WIDTH, HEIGHT).fill(float(height))

def sine(var=5, mean=2, scale=5):
    '2d sine wave -- var=5 mean=2 scale=5'
    return numpy.fromfunction(lambda i, j: numpy.sin(i / float(scale)) * numpy.sin(j / float(scale)) * float(var) + float(mean), (WIDTH, HEIGHT))

def noise(var=5, mean=5, interval=1, degree=1):
    'interpolated random noise -- var=5 mean=5 interval=1 degree=1'
    return World(WIDTH, HEIGHT).fill(0).noise(float(var), float(mean), int(interval), int(degree))

def layer(var=10, mean=0, decay=0.5):
    'layered 1/f random noise -- var=10 mean=0 decay=0.5'
    world = World(WIDTH, HEIGHT).fill(float(mean))
    var = float(var)
    decay = float(decay)
    interval = min(WIDTH, HEIGHT) / 2
    while interval:
        world.noise(var, 0, interval, 1)
        interval /= 2
        var *= decay
    return world

def vorstrict(npoints=10, valley=0):
    'simple voronoi diagram using 1NN -- npoints=10 valley=0'
    return World(WIDTH, HEIGHT).fill(0).vorstrict(int(npoints), float(valley))

def voronoi(npoints=10, shift=1, valley=3, rand=2):
    'voronoi diagram -- npoints=10 shift=1 valley=3 rand=2'
    return World(WIDTH, HEIGHT).fill(1).voronoi(int(npoints), float(shift), float(valley), float(rand))

def dsquare(var=0.01, mean=5, corner=5, horizf=20):
    'diamond-square algorithm -- var=0.01 mean=5 corner=5 horizf=20'
    return World(WIDTH, HEIGHT).dsquare(float(var), float(mean), float(corner), float(horizf))

def dsqvor(var=0.01, mean=5, corner=5, horizf=20, npoints=10, shift=1, valley=3, rand=1):
    'diamond-square plus voronoi -- see above'
    return World(WIDTH, HEIGHT).dsquare(float(var), float(mean), float(corner), float(horizf)).voronoi(int(npoints), float(shift), float(valley), float(rand))

def thermal(var=0.01, mean=5, corner=5, horizf=20, npoints=10, shift=1, valley=3, rand=1, iters=10, talus=3):
    '    plus thermal erosion -- iters=10 talus=3'
    return World(WIDTH, HEIGHT).dsquare(float(var), float(mean), float(corner), float(horizf)).voronoi(int(npoints), float(shift), float(valley), float(rand)).thermal(int(iters), float(talus))

def hydraulic(var=0.01, mean=5, corner=5, horizf=20, npoints=10, shift=1, valley=3, rand=1, iters=10, rain=0.1, evap=0.5):
    '    plus hydraulic erosion -- iters=10 rain=0.1 evap=0.5'
    return World(WIDTH, HEIGHT).dsquare(float(var), float(mean), float(corner), float(horizf)).voronoi(int(npoints), float(shift), float(valley), float(rand)).hydraulic(int(iters), float(rain), float(evap))

def erosion(var=0.01, mean=5, corner=5, horizf=20, npoints=10, shift=1, valley=3, rand=1, iters=10, talus=2):
    '    plus hybrid erosion -- iters=10 talus=2'
    return World(WIDTH, HEIGHT).dsquare(float(var), float(mean), float(corner), float(horizf)).voronoi(int(npoints), float(shift), float(valley), float(rand)).erosion(int(iters), float(talus))

EXLIST = [ real, flat, sine, noise, layer, vorstrict, voronoi, dsquare, dsqvor, thermal, hydraulic, erosion ]
EXAMPLES = {}
for i, fn in enumerate(EXLIST):
    EXLIST[i] = (str(i), fn.__name__) + tuple(fn.__doc__.split(' -- ', 1)) + (fn,)
    EXAMPLES[str(i)] = EXAMPLES[fn.__name__] = EXLIST[i]
COLUMNS = zip([ '%*s |', '%*s:', '%-*s |', '%*s' ], [ max( len(x[i]) for x in EXLIST ) for i in range(4) ])

if __name__ == '__main__':
    WIDTH = HEIGHT = 96
    FILTER = lambda x: x
    random.seed(8392913713)
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--rand':
            random.seed()
        elif sys.argv[i] == '--low':
            FILTER = World.lowpass
        elif sys.argv[i].startswith('--blur'):
            try:
                arg = float(sys.argv[i].split('=', 1)[1])
            except Exception:
                arg = 1.5
            FILTER = lambda x: x.blur(width=arg)
        elif sys.argv[i].startswith('--size'):
            try:
                arg = int(sys.argv[i].split('=', 1)[1])
            except Exception:
                arg = 256
            WIDTH = HEIGHT = arg
        else:
            i += 1
            continue
        del sys.argv[i]
    try:
        ex = EXAMPLES[sys.argv[1]][-1]
    except Exception:
        for data in EXLIST:
            for (fmt, wid), dat in zip(COLUMNS, data):
                print fmt % (wid, dat),
            print
        print '--rand         : randomize'
        print '--low          : low-pass filter'
        print '--blur[=width] : gaussian blur'
        print '--size[=width] : world size'
    else:
        args = []
        kwargs = {}
        for a in sys.argv[2:]:
            if '=' in a:
                kwargs.update([ a.split('=', 1) ])
            else:
                args.append(a)
        world = ex(*args, **kwargs)
        if isinstance(world, World):
            world = FILTER(world).heightmap
        viewer.show(world)
