import os, re, math
import numpy as np
import pyrecon.dev.handleXML as xml
from shapely.geometry import Polygon, LineString, box, LinearRing
from skimage import transform as tf
from collections import OrderedDict

class Contour:
    def __init__(self, *args, **kwargs):
        self.attributes = {
            'name':None,
            'comment':None,
            'hidden':None,
            'closed':None,
            'simplified':None,
            'mode':None,
            'border':None,
            'fill':None,
            'points':None
        }
        self.image = None
        self.transform = None
        self.shape = None
        self.processArguments(args, kwargs)
# MUTATORS
    def processArguments(self, args, kwargs):
        # 1) ARGS
        for arg in args:
            try:
                self.update(arg)
            except:
                print('Could not process Contour arg: '+str(arg))
        # 2) KWARGS
        for kwarg in kwargs:
            try:
                self.update(kwarg)
            except:
                print('Could not process Contour kwarg: '+str(kwarg))
    def update(self, *args): #=== Kwargs eventually
        for arg in args:
            # Dictionary
            if type(arg) == type({}):
                for key in arg:
                    # Dict:attributes
                    if key in self.attributes:
                        self.attributes[key] = arg[key]
                    elif arg[key].__class__.__name__ == 'Transform':
                        self.transform = arg[key]
                    elif arg[key].__class__.__name__ == 'Image':
                        self.image = arg[key]
            # Transform
            elif arg.__class__.__name__ == 'Transform':
                self.transform = arg
            # Image
            elif arg.__class__.__name__ == 'Image':
                self.image = arg
        if self.shape != None:
            self.popshape()

    def popshape(self): #===
        '''Adds polygon object (shapely) to self._shape'''
        # Closed trace
        if self.attributes['closed'] == True:
            # If image contour, multiply pts by mag before inverting transform
            if self.attributes['name'].lower() == 'domain1':
                mag = self.img.mag
                xvals = [pt[0]*mag for pt in self.attributes['points']]
                yvals = [pt[1]*mag for pt in self.attributes['points']]
                pts = zip(xvals,yvals)
            else:
                if len(self.points) < 3:
                    return None
                pts = self.points
            self._shape = Polygon( self.transform.worldpts(pts) )
        # Open trace
        elif self.closed == False and len(self.points)>1:
            self._shape = LineString( self.transform.worldpts(self.points) )
        else:
            print('\nInvalid shape characteristics: '+self.name)
            print('Quit for debug')
            quit() # for dbugging    

# ACCESSORS
    def __eq__(self, other):    
        '''Allows use of == between multiple contours.'''
        return (self.attributes == other.attributes && self.transform == other.transform)
    def __ne__(self, other):
        '''Allows use of != between multiple contours.'''
        return (self.attributes != other.attributes && self.transfrom != other.transform)
# Merge tool functions
    def box(self):
        '''Returns bounding box of shape (shapely) library'''
        if self.shape != None:
            minx, miny, maxx, maxy = self.shape.bounds
            return box(minx, miny, maxx, maxy)
        else:
            print('NoneType for shape: '+self.name)
    def overlaps(self, other, threshold=(1+2**(-17))):
        '''Return 0 if no overlap.
        For closed traces: return 1 if AoU/AoI < threshold, return AoU/AoI if not < threshold
        For open traces: return 0 if # pts differs or distance between parallel pts > threshold
                         return 1 otherwise'''
        if self._shape == None:self.popshape()
        if other._shape == None:other.popshape()
        # Check bounding box
        if (not self.box().intersects(other.box()) and
            not self.box().touches(other.box()) ):
            return 0
        # Check if both same type of contour
        if self.closed != other.closed:
            return 0
        # Closed contours
        if self.closed:
            AoU = self._shape.union( other._shape ).area
            AoI = self._shape.intersection( other._shape ).area
            if AoI == 0:
                return 0
            elif AoU/AoI > threshold:
                return AoU/AoI # Returns actual value, not 0 or 1
            elif AoU/AoI < threshold:
                return 1
        # Open contours
        if not self.closed:
            if len( self.points ) != len( other.points ):
                return 0
            def distance(pt0, pt1):
                return math.sqrt( (pt0[0] - pt1[0])**2 + (pt0[1] - pt1[1])**2 )
            # Lists of world coords to compare
            a = self.transform.worldpts(self.points)
            b = other.transform.worldpts(other.points)
            distlist = [distance(a[i],b[i]) for i in range(len(self.points))] 
            for elem in distlist:
                if elem > threshold:
                    return 0
        return 1
# Curation tool functions
    def getLength(self):
        '''Returns the sum of all line segments in the contour object'''
        length = 0
        for index in range( len(self.points) ):
            if index+1 >= len(self.points): # stop when outside index range
                break
            pt = self.points[index]
            nextPt = self.points[index+1]
            length += (((nextPt[0]-pt[0])**2)+((nextPt[1]-pt[1])**2))**(0.5)
        if self.closed: # If closed object, add distance between 1st and last pt too
            length += (((self.points[0][0]-self.points[-1][0])**2)+((self.points[0][1]-self.points[-1][1])**2))**(0.5)
        return length #=== sqrt is taxing computation; reimplement with 1 sqrt at end?
    def getStartEndCount(self, series):
        '''Returns the start, end, and count values for this contour in given series. Determined by self.name only'''
        return series.getStartEndCount(self.name)
    def getVolume(self, series):
        return series.getVolume(self.name)
    def getSurfaceArea(self, series):
        return series.getSurfaceArea(self.name)
    def getFlatArea(self, series):
        return series.getFlatArea(self.name)
    def isReverse(self):
        '''Returns true if contour is a reverse trace (negative area)'''
        self.popshape()
        if self.closed:
            ring = LinearRing(self._shape.exterior.coords) # convert polygon to ring
            return not ring.is_ccw # For some reason, the opposite is true (image vs biological coordinate system?)
        else:
            return False



class Image:
    def __init__(self, *args, **kwargs):
        self.attributes = {
            'src':None,
            'mag':None,
            'contrast':None, 
            'brightness':None,
            'red':None,
            'green':None,
            'blue':None
        }
        self.transform = None
        self.processArguments(args, kwargs)

# MUTATORS
    def processArguments(self, args, kwargs):
        # 1) ARGS
        for arg in args:
            try:
                self.update(arg)
            except:
                print('Could not process Image arg: '+str(arg))
        # 2) KWARGS
        for kwarg in kwargs:
            try:
                self.update(kwarg)
            except:
                print('Could not process Image kwarg: '+str(kwarg))   
    def update(self, *args): #=== **kwargs eventually
        '''Changes Section data from arguments.'''
        for arg in args:
            # Dictionary  
            if type(arg) == type({}):
                for key in arg:
                    # Dict:Attribute
                    if key in self.attributes:
                        self.attributes[key] = arg[key]
                    # Dict:Transform
                    elif arg[key].__class__.__name__ == 'Transform':
                        self.transform = arg[key]
            # Transform object
            elif arg.__class__.__name__ == 'Transform':
                self.transform = arg

# ACCESSORS
    def __eq__(self, other):
        return (self.transform == other.transform or
                self.src == other.src)
    def __ne__(self, other):
        return (self.transform != other.transform or
                self.src != other.src)   

class Section:
    '''Object representing a Section.'''
    # CONSTRUCTOR
    def __init__(self, *args, **kwargs):
        '''First creates an empty Section. Next, processes *args and **kwargs to determine best method for populating data (more detail in processArguments().'''
        # Create empty Section
        self.attributes = {
            'index':None,
            'thickness':None,
            'alignLocked':None
        }
        self.image = None
        self.contours = None
        
        # Process arguments to update Section data
        self.processArguments(args, kwargs)
    
    # MUTATORS - Change data
    def processArguments(self, args, kwargs):
        '''Populates data from the *args and **kwargs arguments via self.update.'''
        # 1) ARGS
        for arg in args:
            try:
                self.update(arg)
            except:
                print('Could not process Section arg: '+str(arg))

        # 2) KWARGS #===
        for kwarg in kwargs:
            try:
                self.update(kwarg)
            except:
                print('Could not process Section kwarg: '+str(kwarg))
    def update(self, *args): #=== **kwargs eventually, need a way to choose overwrite or append to contours
        '''Changes Section data from arguments. Assesses type of argument then determines where to place it.'''
        for arg in args: # Assess type
            # Dictionary argument
            if type(arg) == type({}):
                for key in arg:
                    # Dict:Attribute
                    if key in self.attributes:
                        self.attributes[key] = arg[key]
                    # Dict:List
                    elif type(arg[key]) == type([]):
                        for item in arg[key]:
                            if item.__class__.__name__ == 'Image':
                                self.image = item
                            elif item.__class__.__name__ == 'Contour':
                                if self.contours == None:
                                    self.contours == []
                                self.contours.append(item)
                    # Dict:Image
                    elif arg[key].__class__.__name__ == 'Image':
                        self.image = arg[key]
                    # Dict:Contour
                    elif arg[key].__class__.__name__ == 'Contour':
                        if self.contours == None:
                            self.contours == []
                        self.contours.append(arg[key])
            
            # String argument
            elif type(arg) == type(''): # Possible path to XML?
                self.update(*xml.process(arg))
            
            # Contour argument
            elif arg.__class__.__name__ == 'Contour':
                if self.contours == None:
                    self.contours = []
                self.contours.append(arg)
            
            # Image argument
            elif arg.__class__.__name__ == 'Image':
                self.image = arg
            
            # List argument
            elif type(arg) == type([]):
                for item in arg:
                    if item.__class__.__name__ == 'Contour':
                        if self.contours == None:
                            self.contours = []
                        self.contours.append(item)
                    elif item.__class__.__name__ == 'Image':
                        self.image = item

    # ACCESSORS - Make accessing data in object easier      
    def __len__(self):
        '''Return number of contours in Section object'''
        return len(self.contours)
    def __getitem__(self,x): #=== test this!
        '''Return <x> associated with Section object'''
        if type(x) == type(''): # If string
            try: #... return attribute of name 'x'
                return self.attributes[x]
            except:
                try: #... return contour with name 'x'
                    return self.contours[x] #=== should be name, not index
                except:
                    print ('Unable to find '+x+ ' (str)')
        elif type(x) == type(int(0)):
            try: #... return xth index in contours
                return self.contours[x]
            except:
                print ('Unable to find '+x+' (int)')
    def __eq__(self, other):
        '''Allows use of == between multiple objects'''
        return self.output() == other.output()
    def __ne__(self, other):
        '''Allows use of != between multiple objects'''
        return self.output() != other.output()

#class Series:

class Transform:
    def __init__(self, *args, **kwargs):
        self.attributes = {
            'dim':None,
            'xcoef':None,
            'ycoef':None
        }
        self._tform = None # skimage.transform._geometric.AffineTransform
        self.processArguments(args, kwargs)

    # MUTATORS
    def processArguments(self, args, kwargs):
        # 1) ARGS
        for arg in args:
            try:
                self.update(arg)
            except:
                print('Could not process Transform arg: '+str(arg))
        # 2) KWARGS
        for kwarg in kwargs:
            try:
                self.update(kwarg)
            except:
                print('Could not process Transform kwarg: '+str(kwarg))

    def update(self, *args): #=== Kwargs eventually
        for arg in args:
            # Dictionary
            if type(arg) == type({}):
                for key in arg:
                    if key in self.attributes:
                        self.attributes[key] = arg[key]
                # Recreate self._tform everytime attributes is updated
                self._tform = self.tform()
            # self._tform (skimage.transform._geometric.AffineTransform)
            elif arg.__class__.__name__ == 'AffineTransform':
                self._tform = arg

    # ACCESSORS
    def __eq__(self, other):
        return self.output() == other.output()
    def __ne__(self, other):
        return self.output() != other.output()
    def worldpts(self, points):
        '''Returns inverse points'''
        newpts = self._tform.inverse(np.asarray(points))
        return list(map(tuple,newpts))
    def isAffine(self):
        '''Returns true if the transform is affine i.e. if a[3,4,5] and b[3,4,5] are 0'''
        xcheck = self.xcoef[3:6]
        ycheck = self.ycoef[3:6]
        for elem in xcheck:
            if elem != 0:
                return False
        for elem in ycheck:
            if elem != 0:
                return False
        return True
    
    # MUTATORS             
    def tform(self):
        '''Creates self._tform variable which represents the transform'''
        xcoef = self.attributes['xcoef']
        ycoef = self.attributes['ycoef']
        dim = self.attributes['dim']
        if xcoef == None or ycoef == None or dim == None:
            return None
        a = xcoef
        b = ycoef
        # Affine transform
        if dim in range(0,4):
            if dim == 0: 
                tmatrix = np.array( [1,0,0,0,1,0,0,0,1] ).reshape((3,3))
            elif dim == 1:
                tmatrix = np.array( [1,0,a[0],0,1,b[0],0,0,1] ).reshape((3,3))
            elif dim == 2: # Special case, swap b[1] and b[2] (look at original Reconstruct code: nform.cpp)
                tmatrix = np.array( [a[1],0,a[0],0,b[1],b[0],0,0,1] ).reshape((3,3))
            elif dim == 3:
                tmatrix = np.array( [a[1],a[2],a[0],b[1],b[2],b[0],0,0,1] ).reshape((3,3))
            return tf.AffineTransform(tmatrix)
        # Polynomial transform
        elif dim in range(4,7):
            tmatrix = np.array( [a[0],a[1],a[2],a[4],a[3],a[5],b[0],b[1],b[2],b[4],b[3],b[5]] ).reshape((2,6))
            # create matrix of coefficients 
            tforward = tf.PolynomialTransform(tmatrix)
            def getrevt(pts): # pts are a np.array
                newpts = [] # list of final estimates of (x,y)
                for i in range( len(pts) ):
                    # (u,v) for which we want (x,y)
                    u, v = pts[i,0], pts[i,1] # input pts
                    # initial guess of (x,y)
                    x0, y0 = 0.0, 0.0
                    # get forward tform of initial guess
                    uv0 = tforward(np.array([x0,y0]).reshape([1, 2]))[0]
                    u0 = uv0[0]
                    v0 = uv0[1]
                    e = 1.0 # reduce error to this limit 
                    epsilon = 5e-10
                    i = 0
                    while e > epsilon and i < 100: #=== 10 -> 100
                        i+=1
                        # compute Jacobian
                        l = a[1] + a[3]*y0 + 2.0*a[4]*x0
                        m = a[2] + a[3]*x0 + 2.0*a[5]*y0
                        n = b[1] + b[3]*y0 + 2.0*b[4]*x0
                        o = b[2] + b[3]*x0 + 2.0*b[5]*y0
                        p = l*o - m*n # determinant for inverse
                        if abs(p) > epsilon:
                            # increment x0,y0 by inverse of Jacobian
                            x0 = x0 + ((o*(u-u0) - m*(v-v0))/p)
                            y0 = y0 + ((l*(v-v0) - n*(u-u0))/p)
                        else:
                            # try Jacobian transpose instead
                            x0 = x0 + (l*(u-u0) + n*(v-v0))        
                            y0 = y0 + (m*(u-u0) + o*(v-v0))
                        # get forward tform of current guess       
                        uv0 = tforward(np.array([x0,y0]).reshape([1, 2]))[0]
                        u0 = uv0[0]
                        v0 = uv0[1]
                        # compute closeness to goal
                        e = abs(u-u0) + abs(v-v0)
                    # append final estimate of (x,y) to newpts list
                    newpts.append((x0,y0))     
                newpts = np.asarray(newpts)           
                return newpts
            tforward.inverse = getrevt
            return tforward

#class ZContour