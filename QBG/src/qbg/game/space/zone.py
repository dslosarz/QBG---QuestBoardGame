from log4py import Logger
from qbg.game.space.tile import Tile
from qbg.game.space.connector import Connector
from qbg.game.space.grid import Grid
from qbg.game.space.direction import Direction
import copy
from qbg.renders.asciirender import AsciiRender


class ZoneConnectorException(Exception):
    pass

class ZoneTypeException(Exception):
    pass

'''
Zone in dungeon
'''
class Zone(Grid):

    def __init__(self,tileFunctionLoader):
        
        '''
        Logger
        '''
        self.log = Logger().get_instance(self.__class__.__name__)
        
        '''
        Init super
        '''
        super(Zone,self).__init__()
        
        '''
        Tile loader able to convert tile CODE
        '''
        self.tileFunctionLoader = tileFunctionLoader
        
        '''
        Name of zone
        '''
        self.name = ''
        
        '''
        Type of this zone, type is define in data filename <type>.<class>.<parser>
        '''
        self.objectType = ''
        
        '''
        Subtype of this zone
        '''
        self.subType = None
        
        '''
        Is this zone can be duplicate in dungeon
        '''
        self.unique = False
        
        '''
        List of connectors for this zone
        '''
        self.connectors = {}
        
        self.zoneDealer = None
                   
        

    def connectTile(self):
        for y in range(0,self.sizeY-1):
            for x in range(0,self.sizeX-1):
                    self.getTile(x,y).addTileNeighborAt(self.getTile(x+1, y),'east')
                    self.getTile(x,y).addTileNeighborAt(self.getTile(x, y+1),'south')
            self.getTile(self.sizeX-1,y).addTileNeighborAt(self.getTile(self.sizeX-1, y+1),'south')
        for x in range(0,self.sizeX-1):
            self.getTile(x,self.sizeY-1).addTileNeighborAt(self.getTile(x+1, self.sizeY-1),'east')    
                
        ##self.checkTileConnection()
        
    def checkTileConnection(self):
        self.log.debug('check tile for '+self.name+'('+str(self.sizeX)+','+str(self.sizeY)+')')
        checkTile = {}
        checkTile[0] = 0
        checkTile[1] = 0
        checkTile[2] = 0
        checkTile[3] = 0
        checkTile[4] = 0
        
        for tile in self.tiles:
            count = tile.countNeighbor()
            checkTile[count] = checkTile[count] +1

        corner = 4
        border = (self.sizeX * 2) + ((self.sizeY - 2) * 2) - corner
        center = (self.sizeX * self.sizeY) - border - corner
       
        if checkTile[0] != 0:
            raise Exception('Some tiles has not connected')
        if checkTile[1] != 0:
            raise Exception('Some tiles has not correctly connected')
        if checkTile[2] != corner:
            raise Exception('Corner are not correctly connected')
        if checkTile[3] !=  border :
            raise Exception('Border are not correctly connected '+ str(checkTile[3]) +' instead of '+ str(border))
        if checkTile[4] != center:
            raise Exception('Center are not correctly connected'+ str(checkTile[4]) +' instead of '+ str(center))
                   
    def addTile(self,tileDefinition):
        newTile = Tile()
        newTile.zone = self
        newTile.setFunctions(self.tileFunctionLoader.getTileFunctionFromDefinition(tileDefinition))
        self.tiles.append(newTile)
        self.log.debug(self.name +' have ' +str(len(self.tiles))+ ' tiles')
        
    def addLine(self,lineDefinition):
        self.log.debug('tiles definition elements for '+self.name+' : ' + str(len(lineDefinition)))
        for tileDefinition in lineDefinition:
            self.addTile(tileDefinition)
            if self.sizeY == None:
                self.sizeX += 1
    
    def setDefinition(self,definition): 
        self.sizeX = 0
        self.sizeY = None
        self.log.debug(str(len(definition)) + ' line definition')
        for lineDefinition in definition:
            self.addLine(lineDefinition)
            if self.sizeY == None:
                self.sizeY = 0
            self.sizeY+= 1
        self.connectTile()       
             

    def setDict(self,dictData):
            self.log.debug(str(dictData))
            self.objectType = dictData['objectType']
            self.name = dictData['name']
            self.setDefinition(dictData['definition'])
            self.subType = dictData['subType']
            self.unique = dictData['unique']  
            self.createConnector()
    '''
    Check all tiles in zone and extract connector from tiles with IO function. Connector is only 2 contiguous tiles with IO.
    '''    
    def createConnector(self):
        self.connectors = {}
        
        io1 = False
        io2 = False
        checkNext = False        
        #north detection        
        for i in range(0,self.sizeX):
            tileIndex = i
            self.log.debug('north check tile index : '+str(tileIndex))    
            detectTile = self.tiles[i]
            if detectTile.hasFunction('IO') and not io1:
                io1 = True
                checkNext = True
            elif detectTile.hasFunction('IO') and io1 and checkNext:
                io2 = True
            else:
                io1 = False
                io2 = False
                checkNext = False 
                    
            if io1 and io2:
                connector = Connector(self)
                connector.position2Y = 0 
                connector.position2X = tileIndex % self.sizeX
                connector.position1Y = connector.position2Y
                connector.position1X = connector.position2X - 1
                connector.direction = 'north'
                self.connectors['north'] = connector
                
                self.log.debug('north detected:'+str(connector))
            
        
        io1 = False
        io2 = False 
        checkNext = False        
        #south detection        
        for i in range(0,self.sizeX):
            tileIndex = i + ( self.sizeY * self.sizeX ) - self.sizeX
            self.log.debug('south check tile index : '+ str(tileIndex))
            detectTile = self.tiles[tileIndex]

            if detectTile.hasFunction('IO') and not io1:
                io1 = True
                checkNext = True
            elif detectTile.hasFunction('IO') and io1 and checkNext:
                io2 = True
            else:
                io1 = False
                io2 = False
                checkNext = False 

            if io1 and io2:
                connector = Connector(self)
                connector.position2Y = self.sizeY - 1 
                connector.position2X = i % self.sizeX
                connector.position1Y = connector.position2Y
                connector.position1X = connector.position2X - 1
                connector.direction = 'south'
                self.connectors['south'] = connector
                self.log.debug('south detected:'+str(connector))    
            
        
        io1 = False
        io2 = False  
        checkNext = False       
        #west detection        
        for i in range(0,self.sizeY):
            tileIndex = i * self.sizeX
            self.log.debug('west check tile index : '+str(tileIndex)) 
            detectTile = self.tiles[tileIndex]
            if detectTile.hasFunction('IO') and not io1:
                io1 = True
                checkNext = True
            elif detectTile.hasFunction('IO') and io1 and checkNext:
                io2 = True
            else:
                io1 = False
                io2 = False
                checkNext = False 
                    
            if io1 and io2:
                connector = Connector(self)
                connector.position2Y = tileIndex / self.sizeX 
                connector.position2X = 0
                connector.position1Y = connector.position2Y - 1 
                connector.position1X = connector.position2X
                connector.direction = 'west'
                self.connectors['west'] = connector
                self.log.debug('west detected:'+str(connector))
                         
        io1 = False
        io2 = False  
        checkNext = False       
        #east detection        
        for i in range(0,self.sizeY):
            tileIndex = (i * self.sizeX) + self.sizeX - 1
            self.log.debug('east check tile index : '+str(tileIndex) )
            detectTile = self.tiles[tileIndex]
            if detectTile.hasFunction('IO') and not io1:
                io1 = True
                checkNext = True
            elif detectTile.hasFunction('IO') and io1 and checkNext:
                io2 = True
            else:
                io1 = False
                io2 = False
                checkNext = False 

            if io1 and io2:
                connector = Connector(self)
                connector.position2Y = tileIndex / self.sizeX 
                connector.position2X = self.sizeX - 1
                connector.position1Y = connector.position2Y - 1 
                connector.position1X = connector.position2X
                connector.direction = 'east'
                self.connectors['east'] = connector
                self.log.debug('east detected:'+str(connector))
        
    
    '''
    lock compatible connector
    '''        
    def lockConnector(self,direction):
        self.log.debug('available connectors '+str(self.getFreeConnectors()))    
        if not direction in self.connectors:
            raise Exception('Connector '+direction + ' not exist')
        if not self.connectors[direction]:
            raise Exception('Connector '+direction + ' already connected')
        self.connectors[direction].locked = True
        self.log.debug('lock direction '+direction+' rest : ' +str(self.getFreeConnectors()))     
    
    '''
    Lock connector for direction
    '''
    def lockCompatibleConnector(self,direction,zoneDealer):
        self.log.debug('Lock connector')
        
        self.lockConnector(Direction.directionCompatibility[direction])
        
        countFreeConnector = len(self.getFreeConnectors())
        if zoneDealer != None:
            
            split = zoneDealer.split(countFreeConnector)
            
            index = 0
            for connector in self.getFreeConnectors():
                connector.zoneDealer = split[index]
                index = index+1
        
                
    
    
    '''
    Check if zone have free connector, if direction is given it check if free connector for this direction exist
    '''
    def hasFreeConnector(self,direction = None):
        if direction == None:
            for loopDirection,connector in self.connectors.iteritems():
                if not connector.locked:
                    return True

        else:
            for loopDirection,connector in self.connectors.iteritems():
                    if loopDirection == direction:
                        if not connector.locked:
                            return True
        return False
    
    
   
    '''
    get compatible connector for requested connector
    ''' 
    def getCompatibleConnector(self,connector):
        self.log.debug('get compatible connector'+str(connector))
        self.log.debug(str(len(self.connectors))+' connectors for zone'+self.name)
        self.rotateForCompatibleConnector(connector) 
        return self.connectors[Direction.directionCompatibility[connector.direction]]
    
     
    '''
    Get all free connectors able to be connected to other zone
    '''             
    def getFreeConnectors(self):
        freeConnectors = []
        for loopDirection,connector in self.connectors.iteritems():
            if not connector.locked:
                freeConnectors.append(connector) 
        self.log.debug(self.name + ' get '+str(len(freeConnectors))+' free connectors :'+str(freeConnectors))
        
        for connector in freeConnectors:
            self.log.debug('Free connector : '+str(connector))
        
        return freeConnectors
    
    '''
    Get the first compatible connector
    '''
    def getOneFreeConnector(self):
        if len(self.getFreeConnectors()) > 0:
            return self.getFreeConnectors()[0]
        else:
            return None
    
    
    '''
    Rotate zone to find compatible connector
    '''
    def rotateForCompatibleConnector(self,connector):
        direction = connector.direction
        
        #there are only 4 rotation authorized
        for i in range(4):
            self.log.debug('free connectors '+str(self.getFreeConnectors())+ ',Rotate '+str(i)+' times')
            if not self.hasFreeConnector(Direction.directionCompatibility[direction]):
                self.log.debug('not compatible => rotate')
                self.rotate()
                self.createConnector()
            else:
                return True
        
        return False                   
    
    
           
            


class PositionnedZone(Zone):
    
    def __init__(self,zone):
        super(PositionnedZone,self).__init__(zone)
        self.startX = 0
        self.startY = 0
        self.zone = zone
        self.connectors = copy.deepcopy(zone.connectors)
        self.sizeX = zone.sizeX
        self.sizeY = zone.sizeY
        self.tiles = copy.deepcopy(zone.tiles)
        self.name = zone.name
        self.subType = zone.subType
    
    def translate(self,x,y):
        self.log.debug('Translate '+str(x)+' '+str(y))
        self.startX = self.startX + x
        self.startY = self.startY + y
        self.translateConnector(x,y)       
        
    def translateConnector(self,x,y):
        
        for direction,connector in self.connectors.iteritems():
            self.log.debug('Translate connector old '+str(connector))
            connector.position1X = connector.position1X + x
            connector.position1Y = connector.position1Y + y
            connector.position2X = connector.position2X + x
            connector.position2Y = connector.position2Y + y
            self.log.debug('Translate connector new '+str(connector))
            self.connectors[direction] = connector
        
    def getTile(self, x, y):
        #self.log.debug('sizeX: '+str(self.sizeX)+'/sizeY:'+str(self.sizeY))
        #self.log.debug('getTile @ '+str(x)+' '+str(y))
        realX = x - self.startX
        realY = y - self.startY
        #self.log.debug('getTile @real '+str(realX)+' '+str(realY))
        return self.zone.getTile(realX,realY)

    def rotate(self):
        self.zone.rotate()
        self.sizeX = self.zone.sizeX
        self.sizeY = self.zone.sizeY
        self.tiles = copy.deepcopy(self.zone.tiles)
        self.connectors = copy.deepcopy(self.zone.connectors)
        
    '''
    Set tile at position X/Y
    '''
    def setTile(self,tile,x,y):
        self.log.debug('setTile @ '+str(x)+' '+str(y))
        realX = x - self.startX
        realY = y - self.startY
        self.tiles[realX + (realY * self.sizeX)] = tile

    def getMaxX(self):
        return self.startX + (self.sizeX -1)
    
    def getMaxY(self):
        #self.log.debug('getMaxY sizeY:'+str(self.sizeY))
        return self.startY + (self.sizeY -1)

    def getMinY(self):
        return self.startY
    
    def getMinX(self):
        return self.startX
    
    def __str__(self, *args, **kwargs):
        render = AsciiRender()
        return render.renderZone(self)
          

        
             
        