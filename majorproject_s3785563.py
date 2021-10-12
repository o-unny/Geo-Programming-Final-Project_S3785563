# -*- coding: utf-8 -*-
"""
Created on Fri Oct  1 16:07:59 2021

@author: olivi
"""

##Step 1: Startup
#Import statements (given by qGIS console)
#Set file path location
pathlocation = "C:\\Users\\olivi\\OneDrive\\Documents\\RMIT2021\\Semester2\\geosprogramming\\majorproject\\testdata\educationcentre\\"

#Declare variables needed for input files
#roads
roadsFile = "Roads.shp"
#lakes
lakesFile = "Lakes.shp"
#vegetation
vegFile = "Vegetation.shp"

#Load input layers into qGIS (building centroids, landcover) 
vegLayer = iface.addVectorLayer(f'{pathlocation}{vegFile}','Vegetation', 'ogr') 
lakesLayer = iface.addVectorLayer(f'{pathlocation}{lakesFile}','Lakes', 'ogr')
roadsLayer = iface.addVectorLayer(f'{pathlocation}{roadsFile}','Roads', 'ogr')

##Step 2: buffer
#Define parameters for the buffer process i.e., distance 
#Run buffer
buffer = processing.run("native:buffer",{'INPUT': roadsLayer,
                                         'DISTANCE': 300,
                                         'DISSOLVE': True,
                                         'OUTPUT': f'{pathlocation}bufferROAD.shp'})
#Add layer into qGIS
bufferLayerroad = iface.addVectorLayer(f'{pathlocation}bufferROAD.shp','Roads buffer','ogr')

#Step 2a: lakes buffer for lakes with different sizes
#set data provider for lake 
data = lakesLayer.dataProvider()
#start editing
lakesLayer.startEditing()
#Add Double field for buffer size on varying lake size
data.addAttributes([QgsField('BuffSize',QVariant.Int)])
#Update the field
lakesLayer.updateFields()
#Save
lakesLayer.commitChanges
#stop editing
iface.vectorLayerTools().stopEditing(lakesLayer,False)

#loop with if statement for different sizes of buffer and lake 
lakesLayer.startEditing()
for feat in lakesLayer.getFeatures():
        #If the area of the lake is < 5000m, buffer = 100m
    if feat['AREA'] < 5000:
        feat['BuffSize_1'] = 100
        #Else if the area is 5000m - 100000m, buffer = 250m
    if feat['AREA'] >= 5000 and feat['AREA'] < 100000:
        feat['BuffSize_1'] = 250
        #Else if the area is > 100000m, buffer = 500m
    if feat['AREA'] > 100000:
        feat['BuffSize_1'] = 500 
    #update field
    lakesLayer.updateFields()
    #update features
    lakesLayer.updateFeature(feat)
    ####PRESS ENTER IN THE CONSOLE
#save changes
lakesLayer.commitChanges()

#add lake buffer
#Define parameters for the buffer process i.e., distance 
#Run buffer
buffer2 = processing.run("saga:variabledistancebuffer",{'SHAPES': lakesLayer,
                                                        'DIST_FIELD': 'BuffSize_1',
                                                        'DISSOLVE': True,
                                                        'BUFFER': f'{pathlocation}bufferLAKE.shp'})
#Add layer into qGIS
bufferLayerlake = iface.addVectorLayer(f'{pathlocation}bufferLAKE.shp','Lakes buffer','ogr')

##Step 3:
#Remove the lake area from the lake buffer
diff = processing.run("native:symmetricaldifference",{'INPUT': bufferLayerlake,
                                                      'OVERLAY': lakesLayer,
                                                      'OUTPUT': f'{pathlocation}bufferdistLAKE.shp'})
bufferdistLake = iface.addVectorLayer(f'{pathlocation}bufferdistLAKE.shp','Lakes buffer difference','ogr')

#create a new layer with intersecting road and lake buffers
intersectbuffer = processing.run("native:intersection",{'INPUT': bufferdistLake,
                                                        'OVERLAY': bufferLayerroad,
                                                        'OUTPUT': f'{pathlocation}buffinter.shp'})
bufferintersection = iface.addVectorLayer(f'{pathlocation}buffinter.shp','Road and Lake buffer','ogr')


##Step 4: 
#create a new vegetation layer based on the desired vegetation
#select features by expression
vegLayer.selectByExpression("\"Veg Type\" = 'Wetland'")
#create layer by selection
selection = processing.run("native:saveselectedfeatures",{'INPUT': vegLayer,
                                                          'OUTPUT': f'{pathlocation}selection.shp'})
selectionLayer = iface.addVectorLayer(f'{pathlocation}selection.shp','Wetland Vegetation','ogr')


##Step 5:
#new layer from intersection of wetland and buffer intersections
finalintersect = processing.run("native:intersection",{'INPUT': selectionLayer,
                                                       'OVERLAY': bufferintersection,
                                                       'OUTPUT': f'{pathlocation}Locations.shp'})
finalintersection = iface.addVectorLayer(f'{pathlocation}Locations.shp','Locations','ogr')


##Step 6:
#multipart to single polygons
multipart = processing.run("native:multiparttosingleparts",{'INPUT': finalintersection,
                                                            'OUTPUT': f'{pathlocation}Split.shp'})
multitosingle = iface.addVectorLayer(f'{pathlocation}Split.shp','Multipart to Single polygons','ogr')


##Step 7:
#Tidy up attribute table
#start editing
multitosingle.startEditing()
#print attribute table field names
print(multitosingle.fields().names())
#delete fields
data2 = multitosingle.dataProvider()
data2.deleteAttributes([5,6,7,8,9,10,11,12,13,14,15])
#update fields
multitosingle.updateFields()
print (multitosingle.fields().names())
#save changes
multitosingle.commitChanges()
#stop editing
iface.vectorLayerTools().stopEditing(multitosingle,False)

#calculate the area of the polygons
#by expression
expression1 = QgsExpression('$area')
expression2 = QgsExpression('$perimeter')

context = QgsExpressionContext()
context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(multitosingle))

#edit
#add area calculations for polygons under the AREA field
with edit(multitosingle):
    for f in multitosingle.getFeatures():
        context.setFeature(f)
        f['AREA'] = expression1.evaluate(context)
        multitosingle.updateFeature(f)
        ####PRESS ENTER IN THE CONSOLE
#convert area calculations into hectares
with edit(multitosingle):
    for f in multitosingle.getFeatures():
        f['AREA'] = f['AREA'] / 10000
        multitosingle.updateFeature(f)
        ####PRESS ENTER IN THE CONSOLE
#add perimeter calculations for polygons under the PERIMETER field
with edit(multitosingle):
    for f in multitosingle.getFeatures():
        context.setFeature(f)
        f['PERIMETER'] = expression2.evaluate(context)
        multitosingle.updateFeature(f)
        ####PRESS ENTER IN THE CONSOLE


##Step 8:
#Create a new layer with all polygons greater or equal to the desired area
#select features by expression - greater than 30ha
multitosingle.selectByExpression("\"AREA\" >= '30'")
#create layer by selection
###writer = QgsVectorFileWriter.writeAsVectorFormat(vegLayer, pathlocation, 'utf-8', \driverName='ESRI Shaprefile', onlySelected=True)
ideal = processing.run("native:saveselectedfeatures",{'INPUT': multitosingle,
                                                      'OUTPUT': f'{pathlocation}Ideal Locations.shp'})
ideallocation = iface.addVectorLayer(f'{pathlocation}Ideal Locations.shp','Ideal Locations','ogr')


#Step 9
###CREATING A MAP
project = QgsProject.instance()

##Turn off all layers apart from Ideal locations, Vegetations, Lakes and Roads
delete1 = project.mapLayersByName('Locations')[0]
project.removeMapLayer(delete1.id())

delete2 = project.mapLayersByName('Multipart to Single polygons Split')[0]
project.removeMapLayer(delete2.id())

delete3 = project.mapLayersByName('Wetland Vegetation selection')[0]
project.removeMapLayer(delete3.id())

delete4 = project.mapLayersByName('Road and Lake buffer buffinter')[0]
project.removeMapLayer(delete4.id())

delete5 = project.mapLayersByName('Lakes buffer difference bufferdistLAKE')[0]
project.removeMapLayer(delete5.id())

delete6 = project.mapLayersByName('Lakes buffer bufferLAKE')[0]
project.removeMapLayer(delete6.id())

delete7 = project.mapLayersByName('Roads buffer bufferROAD')[0]
project.removeMapLayer(delete7.id())

#label ideal locations and turn into a list
layers1 = QgsProject.instance().mapLayersByName('Ideal Locations')
layerlist = layers1[0]
#change colour to brown
polygon = layerlist.renderer()
symbol = polygon.symbol()
symbol.setColor(QColor.fromRgb(255,106,106))

#label vegetation layer and turn into a list
layers2 = QgsProject.instance().mapLayersByName('Vegetation')
layerlist2 = layers2[0]
#change colour to green
polygon = layerlist2.renderer()
symbol = polygon.symbol()
symbol.setColor(QColor.fromRgb(0,100,0))

#label lake layer and turn into a list
layers3 = QgsProject.instance().mapLayersByName('Lakes')
layerlist3 = layers3[0]
#change colour to blue
polygon = layerlist3.renderer()
symbol = polygon.symbol()
symbol.setColor(QColor.fromRgb(0,238,238))

#label roads layer and turn into a list
layers4 = QgsProject.instance().mapLayersByName('Roads')
layerlist4 = layers4[0]
#change colour to dark grey
polygon = layerlist4.renderer()
symbol = polygon.symbol()
symbol.setColor(QColor.fromRgb(255,255,240))


#create a new layout for the map
project.layerTreeRoot().findLayer(layers1.id()).setItemVisibilityCheckedParentRecursive(True)
manager = project.layoutManager()
layoutName = 'ProgrammingOliviaUnny'
#in case there is already a layout with the same name
layouts_list = manager.printLayouts()
for layout in layouts_list:
    if layout.name() == layoutName:
        manager.removeLayout(layout)
        ####PRESS ENTER IN THE CONSOLE
layout = QgsPrintLayout(project)
layout.initializeDefaults()
layout.setName(layoutName)
#add new layout to layout tab
manager.addLayout(layout)

#add a map into the layout
map = QgsLayoutItemMap(layout)
map.setRect(20,20,20,20)
#set map extent 
ms = QgsMapSettings()
#layers to be mapped
ms.setLayers(layers1)
ms.setLayers(layers2)
ms.setLayers(layers3)
ms.setLayers(layers4) 
#size of map
rect = QgsRectangle(ms.fullExtent())
rect.scale(1.0)
ms.setExtent(rect)
map.setExtent(rect)
map.setBackgroundColor(QColor(255, 255, 255, 0))
layout.addLayoutItem(map)

#move and resize map
map.attemptMove(QgsLayoutPoint(5, 10, QgsUnitTypes.LayoutMillimeters))
map.attemptResize(QgsLayoutSize(210, 210, QgsUnitTypes.LayoutMillimeters))

#add legend to layout
legend = QgsLayoutItemLegend(layout)
#title
legend.setTitle("Legend")
layerTree = QgsLayerTree()
##layers to be added to legend
layerTree.addLayer(layerlist)
layerTree.addLayer(layerlist2)
layerTree.addLayer(layerlist3)
layerTree.addLayer(layerlist4)
legend.model().setRootGroup(layerTree)
#add frame around scale
legend.setFrameEnabled(True)
#add to layout
layout.addLayoutItem(legend)
#move
legend.attemptMove(QgsLayoutPoint(220, 40, QgsUnitTypes.LayoutMillimeters))

#add scalebar to layout
scalebar = QgsLayoutItemScaleBar(layout)
#type of scale
scalebar.setStyle('Line Ticks Up')
#units
scalebar.setUnits(QgsUnitTypes.DistanceKilometers)
#number of lines
scalebar.setNumberOfSegments(4)
scalebar.setNumberOfSegmentsLeft(0)
scalebar.setUnitsPerSegment(0.5)
#scale for map
scalebar.setLinkedMap(map)
#units
scalebar.setUnitLabel('km')
#font of scale
scalebar.setFont(QFont('Arial', 14))
#update scale bar
scalebar.update()
#add to layout
layout.addLayoutItem(scalebar)
#move
scalebar.attemptMove(QgsLayoutPoint(220, 185, QgsUnitTypes.LayoutMillimeters))

#add title to layout
title = QgsLayoutItemLabel(layout)
#title name
title.setText("Ideal Location of Wetland Education Centre")
#font
title.setFont(QFont('Arial', 40))
title.adjustSizeToText()
#add to layout
layout.addLayoutItem(title)
#move
title.attemptMove(QgsLayoutPoint(10, 5, QgsUnitTypes.LayoutMillimeters))






