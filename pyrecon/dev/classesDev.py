from pyrecon.dev import handleXML as xml
class Section:
    '''Object representing a Section.'''
    # CONSTRUCTOR - Construct Section object from arguments
    def __init__(self, *args, **kwargs):
        '''First creates an empty Section. Next, processes *args and **kwargs to determine best method for populating data (more detail in processArguments().'''
        # Create empty Section
        self.attributes = None
        self.image = None
        self.contours = None
        # Process arguments to create populated Section
        self.processArguments(args, kwargs)

    def processArguments(self, args, kwargs): #===
        '''Populates data from the *args and **kwargs arguments. If a path to an XML file is given, it will take precedence and ignore other arguments. If all of the data is not present in the XML file, the other arguments will then be processed to locate the missing data. Any data not found will result in None for that data label.'''
        try: #===
            self.updateViaPath(args[0]) #=== only option for now
        
        except:
            print('Could not process arguments. Empty Section returned.')

    def updateViaPath(self, path):
        '''Update the sections data via supplied path to XML file'''
        self.attributes, self.image, self.contours = xml.process(path)

    def updateViaDictionary(self, dictionary):
        return

    def updateViaObject(self, object):
        return

    # MUTATORS - Change data in object

    # ACCESSORS - Make accessing data in object easier      
    def __len__(self):
        '''Return number of contours in Section object'''
        return len(self.contours)
    def __getitem__(self,x):
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
