import random
import numpy
import scipy.signal
import math

class World:
    def __init__(self, width, height):
        self.heightmap = numpy.zeros((width, height))
        self.fill(float('nan'))
        self.xmax = width
        self.ymax = height
    
    def fill(self, height):
        self.heightmap.fill(height)
        return self
    
    def noise(self, var, mean, interval, degree):
        xpoints = range(0, self.xmax, interval)
        ypoints = range(0, self.ymax, interval)
        data = numpy.zeros(self.heightmap.shape)
        for i in range(len(xpoints)):
            for j in range(len(ypoints)):
                data[i,j] = random.gauss(mean, var)
        if degree == 1:
            for i in range(len(xpoints)):
                data[i,:] = numpy.interp(range(self.ymax), xpoints, data[i,:len(xpoints)])
            for j in range(self.ymax):
                data[:,j] = numpy.interp(range(self.xmax), ypoints, data[:len(ypoints),j])
        else:
            for i in range(len(xpoints)):
                data[i,:] = numpy.polyval(numpy.polyfit(xpoints, data[i,:len(xpoints)], degree), range(self.ymax))
            for j in range(self.ymax):
                data[:,j] = numpy.polyval(numpy.polyfit(ypoints, data[:len(ypoints),j], degree), range(self.xmax))
        self.heightmap += data
        return self
    
    def dsquare(self, var, mean, corner, horizf):
        if var:
            def err(vert, horiz):
                return vert + (vert + horiz * horizf) * random.triangular(-var, var, 0)
        else:
            def err(vert, horiz):
                return vert
        
        def seth(x, y, height):
            if numpy.isnan(self.heightmap[x,y]):
                self.heightmap[x,y] = height
        def geth(point):
            if numpy.isnan(self.heightmap[point]):
                self.heightmap[point] = random.uniform(-corner, corner) + mean
            return self.heightmap[point]
        
        def dsq(width, height, left, top):
            if width <= 1 and height <= 1:
                return
            xmid = width / 2
            ymid = height / 2
            corners = map(geth, [ (left, top), (left + width, top), (left + width, top + height), (left, top + height) ])
            if width <= 1:
                seth(        left, ymid + top, err((corners[0] + corners[3]) / 2, height))
                seth(width + left, ymid + top, err((corners[1] + corners[2]) / 2, height))
                dsq(width,          ymid, left,        top)
                dsq(width, height - ymid, left, ymid + top)
            elif height <= 1:
                seth(xmid + left,          top, err((corners[0] + corners[1]) / 2,  width))
                seth(xmid + left, height + top, err((corners[2] + corners[3]) / 2,  width))
                dsq(        xmid, height,        left, top)
                dsq(width - xmid, height, xmid + left, top)
            else:
                center = err((corners[0] + corners[1] + corners[2] + corners[3]) / 4, (height + width) / 2)
                seth(        left,   ymid + top, err((corners[0] + corners[3] + center) / 3, height))
                seth(width + left,   ymid + top, err((corners[1] + corners[2] + center) / 3, height))
                seth( xmid + left,          top, err((corners[0] + corners[1] + center) / 3,  width))
                seth( xmid + left, height + top, err((corners[2] + corners[3] + center) / 3,  width))
                seth( xmid + left,   ymid + top, center)
                dsq(        xmid,          ymid,        left,        top)
                dsq(        xmid, height - ymid,        left, ymid + top)
                dsq(width - xmid, height - ymid, xmid + left, ymid + top)
                dsq(width - xmid,          ymid, xmid + left,        top)
        
        dsq(self.xmax - 1, self.ymax - 1, 0, 0)
        return self
    
    def vorstrict(self, npoints, valley):
        points = [ ( random.randrange(self.xmax), random.randrange(self.ymax) ) for i in range(npoints) ]
        def distances(i, j):
            for x, y in points:
                yield (x - i) * (x - i) + (y - j) * (y - j)
        for i in range(self.xmax):
            for j in range(self.ymax):
                dists = sorted(distances(i, j))
                self.heightmap[i,j] += max(0, math.sqrt(dists[0]) - valley)
        return self
    
    def voronoi(self, npoints, shift, valley, rand):
        points = [ ( random.randrange(self.xmax), random.randrange(self.ymax),
                     random.triangular(-rand, rand, 0) if rand else 1 ) for i in range(npoints) ]
        def distances(i, j):
            i += random.gauss(0, shift)
            j += random.gauss(0, shift)
            for x, y, w in points:
                yield (x - i) * (x - i) + (y - j) * (y - j), w
        for i in range(self.xmax):
            for j in range(self.ymax):
                dists = sorted(distances(i, j))
                self.heightmap[i,j] += max(0, math.sqrt(dists[1][0]) - math.sqrt(dists[0][0]) - valley) * dists[0][1]
        return self
    
    def neighbors(self, i, j):
        if i > 0:
            if j > 0:
                yield (i - 1, j - 1)
            if j < self.ymax - 1:
                yield (i - 1, j + 1)
        if i < self.xmax - 1:
            if j > 0:
                yield (i + 1, j - 1)
            if j < self.ymax - 1:
                yield (i + 1, j + 1)
    
    def thermal(self, iters, talus):
        for t in range(iters):
            new = numpy.copy(self.heightmap)
            for i in range(self.xmax):
                for j in range(self.ymax):
                    ldiff, lowest = max( (self.heightmap[i,j] - self.heightmap[n], n) for n in self.neighbors(i, j) )
                    if ldiff > talus:
                        new[i,j] -= ldiff / 2
                        new[lowest] += ldiff / 2
            self.heightmap = new
        return self
    
    def hydraulic(self, iters, rain, evap):
        water = numpy.zeros(self.heightmap.shape)
        dwater = numpy.zeros(self.heightmap.shape)
        for t in range(iters):
            water += rain
            self.heightmap -= rain
            dwater.fill(0)
            for i in range(self.xmax):
                for j in range(self.ymax):
                    diffs = [ ((self.heightmap[i,j] + water[i,j]) - (self.heightmap[n] + water[n]), n) for n in self.neighbors(i, j) ]
                    positive = [ (d, n) for (d, n) in diffs if d > 0 ]
                    if not positive:
                        continue
                    total = sum( d for (d, n) in positive )
                    delta = min(water[i,j], total / len(positive))
                    for d, n in positive:
                        d *= delta / total
                        dwater[i,j] -= d
                        dwater[n] += d
            water += dwater
            self.heightmap += water * evap
            water *= 1 - evap
        return self
    
    def erosion(self, iters, talus):
        for t in range(iters):
            new = numpy.copy(self.heightmap)
            for i in range(self.xmax):
                for j in range(self.ymax):
                    ldiff, lowest = max( (self.heightmap[i,j] - self.heightmap[n], n) for n in self.neighbors(i, j) )
                    if 0 < ldiff <= talus:
                        new[i,j] -= ldiff / 2
                        new[lowest] += ldiff / 2
            self.heightmap = new
        return self
    
    def lowpass(self):
        new = numpy.copy(self.heightmap)
        for i in range(1, self.xmax - 1):
            for j in range(1, self.ymax - 1):
                new[i,j] = (self.heightmap[i-1,j] + self.heightmap[i,j+1] + self.heightmap[i+1,j] + self.heightmap[i,j-1] + self.heightmap[i,j]) / 5
        self.heightmap = new
        return self
    
    def blur(self, width=5, stddev=1):
        gauss = scipy.signal.gaussian(width, stddev)
        self.heightmap = scipy.signal.sepfir2d(self.heightmap, gauss, gauss) / (gauss.sum() * gauss.sum())
        return self
