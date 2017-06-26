from __future__ import division
import arcpy, sys, os, arcgisscripting, math, datetime

#Dir on VCL --> C:/Users/tghays/Desktop/CG-GIS

#***REQUIRED ARGUMENTS***
#Argument 1: location of main directory -------->>>>  'I:'
dir = sys.argv[1]
arcpy.env.workspace = sys.argv[1]
#Argument 2: specify CG or SWG
feedstock = sys.argv[2]
#Argument 3: Feedstock Availability, specify "ALL" or "HALF"
FA = sys.argv[3]
#Arugment 4: Specify quadrant size
quadrantSize = int(sys.argv[4])


receptorDist = '15 kilometers' #Specify radius of receptor distance from corn emitter to calculate concentration.
arcpy.env.overwriteOutput = True
refdir = dir + '/Ref_Files'
rundir = dir + '/Run_Data'
#*************FILE SELECTION for scenario parameters, based on user-specified arguments*********
#*** Feedstock and Minimum farm size selection
if feedstock == 'CG':
    if FA == 'ALL':
        farmPoly = refdir + 'Feedstocks/CG/NCSCcorn10aALLRadius51-6Mile.shp'
        centroid = refdir + 'Feedstocks/CG/NCSCcorn10aALL_cent.shp'
        tDist = '52 miles'
    elif FA == 'HALF':
        farmPoly = refdir + 'Feedstocks/CG/NCSCcorn10aHALFRadius76-48Mile.shp'
        centroid = refdir + 'Feedstocks/CG/NCSCcorn10aHALF_cent.shp'
        tDist = '77 miles'
    else:
        print 'Invalid Argument 3 (FA) Input'

elif feedstock == 'SWG':
    if FA == 'ALL':
        farmPoly = refdir + '/Feedstocks/SWG/NCSC_SWG_10aALL_53-777Mile.shp'
        centroid = refdir + '/Feedstocks/SWG/NCSC_SWG_10aALL_cent.shp'
        tDist = '54 Miles'
    elif FA == 'HALF':
        farmPoly = refdir + '/Feedstocks/SWG/NCSC_SWG_10aHALF_69-225Mile.shp'
        centroid = refdir + '/Feedstocks/SWG/NCSC_SWG_10aHALF_cent.shp'
        tDist = '70 Miles'
    else:
        print 'Invalid Argument 3 (FA) Input'
else:
    print 'Invalid Argument 2 (Feedstock) Input'

# Quadrant size and associted receptors file selection
quads = refdir + '/QuadrantsReceptors/NCSC_{0}kmquad.shp'.format(quadrantSize)

#Biorefinery emissions
if feedstock == 'CG':
    biorefinery = refdir + '/Biorefinery/CBF_CG_emissions.shp'
elif feedstock == 'SWG':
    biorefinery = refdir + '/Biorefinery/CBF_Cell_emissions.shp'

#***** Farmland emission values in kg/acre*yr ***************
if feedstock == 'CG':
    HGWAv = 5.06E+01
    HAAv = 5.80E+00
    HHHPv = 2.03E-01
    HEAv = 3.66E-01
    HSAv = 0.00E+00
    HODv = 2.47E+01
    HHHCv = 0.00E+00
    HHHNCv = 3.93E-05

    EGWAv = 1.92E+01
    EAAv = 3.41E+00
    EHHPv = 1.20E-01
    EEAv = 2.15E-01
    ESAv = 0.00E+00
    EODv = 4.55E+00
    EHHCv = 0.00E+00
    EHHNCv = 0.00E+00

    fYield = 3.358896016 #BDMT/acre

elif feedstock == 'SWG':
    HGWAv = 8.34E+01
    HAAv = 5.50E-01
    HHHPv = 1.47E-02
    HEAv = 3.48E-02
    HSAv = 0.00E+00
    HODv = 1.28E+02
    HHHCv = 0.00E+00
    HHHNCv = 6.65E-06

    EGWAv = 5.45E+01
    EAAv = 3.79E+00
    EHHPv = 1.31E-01
    EEAv = 2.39E-01
    ESAv = 0.00E+00
    EODv = 1.29E+01
    EHHCv = 0.00E+00
    EHHNCv = 0.00E+00

    fYield = 7.486695939 #BDMT/acre

TGWAv = EGWAv + HGWAv
TAAv = EAAv + HAAv
THHPv = EHHPv + HHHPv
TEAv = EEAv + HEAv
TSAv = ESAv + HSAv
THHCv = EHHCv + HHHCv
THHNCv = EHHNCv + HHHNCv

sr = arcpy.SpatialReference(2264)

#Add Field to quads with quad source FID
arcpy.AddField_management(quads, "quadSource", "DOUBLE") 
arcpy.CalculateField_management(quads, "quadSource", '!FID!', 'PYTHON_9.3')

#Product directory and buildfiles directory creations
arcpy.CreateFolder_management(dir, '/Products/{0}{1}{2}km'.format(feedstock, FA, str(quadrantSize)))
Pdir = dir + '/Products/{0}{1}{2}km'.format(feedstock, FA, str(quadrantSize))
arcpy.CreateFolder_management(rundir, '/buildFiles')
arcpy.CreateFolder_management(rundir, '/buildFiles/transLines')

#bioGeo geometry and point specification for BIOREFINERY impact calculations
bioCursor = arcpy.da.SearchCursor(biorefinery, ['SHAPE@', 'GWA', 'AA','HHPA','EA','SA', 'OD', 'HHC','HHNC','SHAPE@XY'])
#                                                   0       1      2     3     4   5      6     7      8       9
bio = bioCursor.next()
bioCats = bio[1:9]
bioGeo = bio[0]
bioGeoXY = bio[9]
bioGeoX = bioGeoXY[0]
bioGeoY = bioGeoXY[1]
bioPt = arcpy.Point(bioGeoX, bioGeoY)

#Product File to be written to
arcpy.CopyFeatures_management(quads, Pdir + '/Total_QuadsWt.shp')
PTquads = Pdir + '/Total_QuadsWt.shp'
arcpy.CopyFeatures_management(quads, Pdir + '/Total_QuadsWOt.shp')
Pquads = Pdir + '/Total_QuadsWOt.shp'
arcpy.CopyFeatures_management(quads, Pdir + '/Establishment_Quads.shp')
Equads = Pdir + '/Establishment_Quads.shp'
arcpy.CopyFeatures_management(quads, Pdir + '/Harvest_Quads.shp')
Hquads = Pdir + '/Harvest_Quads.shp'
arcpy.CopyFeatures_management(quads, Pdir + '/etOHdist_Quads.shp')
Dquads = Pdir + '/etOHdist_Quads.shp'
arcpy.CopyFeatures_management(quads, Pdir + '/Farm_Quads.shp')
Fquads = Pdir + '/Farm_Quads.shp'

#Transport emissions associated with 1 tkm of transport using Diesel fuel. Format is [GWA, AA, HHPA, EA, SA, OD, HHC,HHNC]. Kg of impact/tkm
tEmissions = [2.46E-01, 1.50E-03, 1.10E-04, 2.28E-04, 4.24E-02, 2.19E-08, 7.57E-09, 3.42E-08]


# *******TIME******
t0 = datetime.datetime.now()
print 'Directories have been specified.  Initializing script at time: {0}'.format(t0)
arcpy.AddMessage('Directories have been specified.  Initializing script at time: {0}'.format(t0))
# ******TIME******
#*******TIME data******
nEmit = arcpy.GetCount_management(centroid)
numEmit = int(nEmit.getOutput(0))
print 'Number of farm emitters: {0}'.format(numEmit) 
arcpy.AddMessage('Number of farm emitters: {0}'.format(numEmit))
#*******TIME data******

#quadrant selection for transportation quadrants
arcpy.MakeFeatureLayer_management(quads, 'layer')
arcpy.SelectLayerByLocation_management('layer', 'WITHIN_A_DISTANCE', bioGeo, tDist, 'NEW_SELECTION')
arcpy.CopyFeatures_management('layer', Pdir + '/Transport_Quads.shp')
Tquads = Pdir + '/Transport_Quads.shp'
arcpy.Delete_management('layer')
#Transportation quadrant layer creation
arcpy.MakeFeatureLayer_management(Tquads, 't_lyr')

#********quadrant selection for farmland emissions, 
arcpy.MakeFeatureLayer_management(quads, 'fQuad_lyr')
arcpy.MakeFeatureLayer_management(centroid, 'centroid_lyr')
arcpy.SelectLayerByLocation_management('fQuad_lyr', 'CONTAINS', 'centroid_lyr', '', 'NEW_SELECTION')
arcpy.CopyFeatures_management('fQuad_lyr', Pdir + '/quadswFarm.shp')
farmQuads = Pdir + '/quadswFarm.shp'
nQuad = arcpy.GetCount_management(farmQuads)
numQuad = int(nQuad.getOutput(0))

#Adding fields to farmquads shapefile for farmland area calculations
arcpy.AddField_management(farmQuads, 'perFArea', 'DOUBLE')
arcpy.AddField_management(farmQuads, 'FArea', 'DOUBLE')
arcpy.Delete_management('centroid_lyr')
arcpy.Delete_management('fQuad_lyr')

#Dictionary definitions
receptorDict = {}
receptorTdict = {}
totalFarmDict = {}
receptorTdict2 = {}
eDict = {}
hDict = {}
fqDict = {}
totalFarea = 0
totalTKM = 0
totalYield = 0
totaldistKM = 0

#-----------Calculate Impacts from ESTABLISHMENT & MAINTENANCE/HARVEST stages ----------
#Distribution of impacts, % of emitted pollutant(impact) that is assumed to impact the quadrants.  q0 is the emitting quadrant, q1 are the 4 quads bordering the emitting quadrant--> 0.7 + (4*0.075) = 1.00
qPercent0 = 0.70
qPercent1 = 0.0375

quadCursor = arcpy.da.UpdateCursor(farmQuads, ['FID', 'SHAPE@','perFArea','quadSource', 'SHAPE@XY', 'FArea'])
for quad in quadCursor:                                 #1          2           3           4          5
    g = arcpy.Geometry()
    qnFID = quad[0]
    quadGeo = quad[1]
    quadFID = quad[3]
    arcpy.MakeFeatureLayer_management(farmPoly, 'farmPoly_lyr')
    time.sleep(1)
    arcpy.SelectLayerByLocation_management('farmPoly_lyr', 'HAVE_THEIR_CENTER_IN', quadGeo, '', 'NEW_SELECTION')
    time.sleep(1)
    arcpy.CopyFeatures_management('farmPoly_lyr', rundir + '/buildFiles/farmPoly0_{0}.shp'.format(int(quadFID)))
    geoList = arcpy.CopyFeatures_management(rundir + '/buildFiles/farmPoly0_{0}.shp'.format(int(quadFID)), g)
    arcpy.Delete_management('farmPoly_lyr')
    if geoList:
        arcpy.MakeFeatureLayer_management(quads, 'farmQuad_lyr1')
        arcpy.SelectLayerByLocation_management('farmQuad_lyr1', 'WITHIN_A_DISTANCE', quadGeo, '1 kilometers', 'NEW_SELECTION')
        arcpy.SelectLayerByLocation_management('farmQuad_lyr1', 'ARE_IDENTICAL_TO', quadGeo, '', 'REMOVE_FROM_SELECTION')
        time.sleep(1)
        arcpy.CopyFeatures_management('farmQuad_lyr1', rundir + '/buildFiles/q1farmQuads_{0}.shp'.format(int(quadFID)))
        qQuads = rundir + '/buildFiles/q1farmQuads_{0}.shp'.format(int(quadFID))
        fArea = 0
        for geo in geoList:
            fArea += geo.area
        fAreaAcres = fArea * 2.29568e-5 #convert ft2 to acres
        totalFarea += fAreaAcres
        quad[5] = fAreaAcres
        qArea = quadGeo.area
        perFArea = fArea/qArea
        quad[2] = perFArea
        quadCursor.updateRow(quad)
        HcatsMain = [HGWAv, HAAv, HHHPv, HEAv, HSAv, HODv, HHHCv, HHHNCv]
        EcatsMain = [EGWAv, EAAv, EHHPv, EEAv, ESAv, EODv, EHHCv, EHHNCv]
        HcatsMain_Farea = [fAreaAcres * x for x in HcatsMain]
        EcatsMain_Farea = [fAreaAcres * x for x in EcatsMain]
        Hcatsq0 = [qPercent0 * x for x in HcatsMain_Farea]
        Ecatsq0 = [qPercent0 * x for x in EcatsMain_Farea]
        Hcatsq1 =[qPercent1 * x for x in HcatsMain_Farea]
        Ecatsq1 = [qPercent1 * x for x in EcatsMain_Farea]
        key = quadFID
        tFcatsq0 = [x + y for x, y in zip(Ecatsq0, Hcatsq0)]
        tFcatsq1 = [x + y for x, y in zip(Ecatsq1, Hcatsq1)]

#Writing the impact values for establishment and harvest to a quadrant for q0 quads, the quadrants that contain the centroid of the farmland
        if key in hDict:
            hDict[key] = [hDict[key][i] + Hcatsq0[i] for i in xrange(len(hDict[key]))]
        else:
            hDict[key] = Hcatsq0

        if key in eDict:
            eDict[key] = [eDict[key][i] + Ecatsq0[i] for i in xrange(len(eDict[key]))]
        else:
            eDict[key] = Ecatsq0

        if key in totalFarmDict:
            totalFarmDict[key] = [totalFarmDict[key][i] + tFcatsq0[i] for i in xrange(len(totalFarmDict[key]))]
        else:
            totalFarmDict[key] = tFcatsq0

        if key in receptorDict:
            receptorDict[key] = [receptorDict[key][i] + tFcatsq0[i] for i in xrange(len(receptorDict[key]))]
        else:
            receptorDict[key] = tFcatsq0
        del key
#Writing the impact values for establishment and harvest to the associated quadrants for the q1 quads, the 4 quadrants that surround the central quadrant containing the centroid of the farmland
        qQuadCursor = arcpy.da.SearchCursor(qQuads, ['quadSource'])
        for q in qQuadCursor:
            key2 = q[0]
            if key2 in hDict:
                hDict[key2] = [hDict[key2][i] + Hcatsq1[i] for i in xrange(len(hDict[key2]))]
            else:
                hDict[key2] = Hcatsq1

            if key2 in eDict:
                eDict[key2] = [eDict[key2][i] + Ecatsq1[i] for i in xrange(len(eDict[key2]))]
            else:
                eDict[key2] = Ecatsq1

            if key2 in totalFarmDict:
                totalFarmDict[key2] = [totalFarmDict[key2][i] + tFcatsq1[i] for i in xrange(len(totalFarmDict[key2]))]
            else:
                totalFarmDict[key2] = tFcatsq1

            if key2 in receptorDict:
                receptorDict[key2] = [receptorDict[key2][i] + tFcatsq1[i] for i in xrange(len(receptorDict[key2]))]
            else:
                receptorDict[key2] = tFcatsq1
        
        # *******TIME******
        t01 = datetime.datetime.now()
        c= t01-t0
        min = divmod(c.total_seconds(), 60)[0]
        sec = divmod(c.total_seconds(), 60)[1]
        print 'Writing concentration values for quadrants containing farmland areas. Quad {0}/{1} complete. Elapsed Time: {2} min {3} seconds'.format(int(qnFID), numQuad, min, sec)
        arcpy.AddMessage('Writing concentration values for quadrants containing farmland areas. Quad {0}/{1} complete. Elapsed Time: {2} min {3} seconds'.format(int(qnFID), numQuad, min, sec))
        # ******TIME******
        
        #This is the transportation calculation for the selected quadrant (still within the farmQuad 'for' loop). Those quads are the average of the farmland falling in selected quad
        #This loop adds the point geometry(key) and the impacts(value) to a transportation impact dictionary    
        farmArea = fArea * 2.29568e-5  #area in ft2 to acres conversion
        Yield = farmArea * fYield #(BDMT/acre) * acre = BDMT, yield from selected farm
        totalYield += Yield
        quadGeoXY = quad[4]
        quadGeoX =  quadGeoXY[0]
        quadGeoY = quadGeoXY[1]
        quadPt = arcpy.Point(quadGeoX, quadGeoY)
        array = arcpy.Array([bioPt, quadPt])
        line = arcpy.Polyline(array)
        arcpy.CopyFeatures_management(line, rundir + '/buildFiles/transLines/farmTLine_qFID{0}.shp'.format(int(quadFID)))
        arcpy.DefineProjection_management(rundir + '/buildFiles/transLines/farmTLine_qFID{0}.shp'.format(int(quadFID)), sr)
        arcpy.AddField_management(rundir + '/buildFiles/transLines/farmTLine_qFID{0}.shp'.format(int(quadFID)), 'lineQuad', 'DOUBLE')
        dist = line.length
        distKM = dist * 0.0003048 #convert line length in ft to km
        totaldistKM += distKM
        tkm = Yield * distKM
        totalTKM += tkm
        tEm = [tkm * i for i in tEmissions]
        arcpy.SelectLayerByLocation_management('t_lyr', 'INTERSECT', line, '', 'NEW_SELECTION')
        time.sleep(1)
        arcpy.CopyFeatures_management('t_lyr', rundir + '/buildFiles/transLines/q0tLinequads_qFID{0}.shp'.format(int(quadFID)))
        num = arcpy.GetCount_management(rundir + '/buildFiles/transLines/q0tLinequads_qFID{0}.shp'.format(int(quadFID)))
        qNumber = int(num.getOutput(0))
        tImpacts = [x / qNumber for x in tEm] #dividing total transportation emissions from selected farm yield into even separate section based on number of quadrants on tLine
        q0tImpacts = [qPercent0 * i for i in tImpacts]
        q1tImpacts = [qPercent1 * i for i in tImpacts]
        
        arcpy.SelectLayerByAttribute_management('t_lyr', 'CLEAR_SELECTION')
        q0tQuads = rundir + '/buildFiles/transLines/q0tLinequads_qFID{0}.shp'.format(int(quadFID))
        q0tQuadsCursor = arcpy.da.SearchCursor(q0tQuads, ['SHAPE@', 'quadSource'])
        for q0 in q0tQuadsCursor:
            tqGeo = q0[0]
            q0tLkey = q0[1]
            if q0tLkey in receptorTdict:
                receptorTdict[q0tLkey] = [receptorTdict[q0tLkey][i]+q0tImpacts[i] for i in xrange(len(receptorTdict[q0tLkey]))]
            else:
                receptorTdict[q0tLkey] = q0tImpacts
            arcpy.SelectLayerByLocation_management('t_lyr', 'WITHIN_A_DISTANCE', tqGeo, '1 kilometers', 'NEW_SELECTION')
            arcpy.SelectLayerByLocation_management('t_lyr', 'ARE_IDENTICAL_TO', tqGeo, '', 'REMOVE_FROM_SELECTION')
            arcpy.MakeFeatureLayer_management('t_lyr', 'q1_lyr')
            q1Cursor = arcpy.da.SearchCursor('q1_lyr', ['quadSource'])
            for q1i in q1Cursor:
                q1tLkey = q1i[0]
                if q1tLkey in receptorTdict:
                    receptorTdict[q1tLkey] = [receptorTdict[q1tLkey][i]+q1tImpacts[i] for i in xrange(len(receptorTdict[q1tLkey]))]
                else:
                    receptorTdict[q1tLkey] = q1tImpacts
            del q1Cursor
            arcpy.SelectLayerByAttribute_management('t_lyr', 'CLEAR_SELECTION')
            arcpy.Delete_management('q1_lyr')
        del q0tQuadsCursor



#-----------Calculate Impacts from BIOREFINERY/ETHANOL CONVERSION----------
#Distribution of impacts, % of emitted pollutant(impact) that is assumed to impact the quadrants.  q0 is the emitting quadrant, q1 are the 4 quads bordering the emitting quadrant--> 0.7 + (4*0.075) = 1.00
qPercent0 = 0.70
qPercent1 = 0.0375

biorefDict = {}
q0bioCats = [x * qPercent0 for x in bioCats]
q1bioCats = [u * qPercent1 for u in bioCats]
arcpy.MakeFeatureLayer_management(quads, 'bioQuad_lyr')
arcpy.SelectLayerByLocation_management('bioQuad_lyr', 'CONTAINS', bioGeo, '', 'NEW_SELECTION')
arcpy.CopyFeatures_management('bioQuad_lyr', rundir + '/buildFiles/q0BioQuads.shp')
q0bioCursor = arcpy.da.SearchCursor(rundir + '/buildFiles/q0BioQuads.shp', ['quadSource', 'SHAPE@'])
q0bio = q0bioCursor.next()
q0bioKey = q0bio[0]
bioQuadGeo = q0bio[1]
biorefDict[q0bioKey] = q0bioCats
del q0bioCursor

arcpy.MakeFeatureLayer_management(rundir + '/buildFiles/q0BioQuads.shp', 'q0bioQuad_lyr')
arcpy.SelectLayerByLocation_management('bioQuad_lyr', 'WITHIN_A_DISTANCE', 'q0bioQuad_lyr', '1 kilometers', 'NEW_SELECTION')
arcpy.CopyFeatures_management('bioQuad_lyr', Pdir + '/Biorefinery_Quads.shp')
Bquads = Pdir + '/Biorefinery_Quads.shp'
arcpy.SelectLayerByLocation_management('bioQuad_lyr', 'WITHIN_A_DISTANCE', 'q0bioQuad_lyr', '1 kilometers', 'NEW_SELECTION')
arcpy.SelectLayerByLocation_management('bioQuad_lyr', 'ARE_IDENTICAL_TO', bioQuadGeo, '', 'REMOVE_FROM_SELECTION')
arcpy.CopyFeatures_management('bioQuad_lyr', rundir + '/buildFiles/q1BioQuads.shp')
q1bioCursor = arcpy.da.SearchCursor(rundir + '/buildFiles/q1BioQuads.shp', ['quadSource'])
for q1bio in q1bioCursor:
    q1bioKey = q1bio[0]
    biorefDict[q1bioKey] = q1bioCats
del q1bioCursor
arcpy.Delete_management('bioQuad_lyr')
arcpy.Delete_management('q0bioQuad_lyr')

#Adding biorefinery impacts to receptor dictionary
for key in biorefDict:
    if key in receptorDict:
        receptorDict[key] = [receptorDict[key][i] + biorefDict[key][i] for i in xrange(len(receptorDict[key]))]
    else:
        receptorDict[key] = biorefDict[key]


#-----------Calculate Impacts from ETHANOL DISTRIBUTION----------
#Distribution of impacts, % of emitted pollutant(impact) that is assumed to impact the quadrants.  q0 is the emitting quadrant, q1 are the 4 quads bordering the emitting quadrant--> 0.7 + (4*0.075) = 1.00
qPercent0 = 0.70
qPercent1 = 0.0375

distDict = {}
distQuads = dir + '/Ref_Files/etOH_Dist/lineQuads.shp'
q0distQuads = dir + '/Ref_Files/etOH_Dist/lineQuads.shp'
distLine = dir + '/Ref_Files/etOH_Dist/line.shp'
distImpacts = [7.29736657E+04, 4.45516148E+02, 3.26014928E+01, 6.76954562E+01, 1.25705748E+04, 6.49593969E-03, 2.24525716E-03, 1.01382932E-02] #kg impact/year
q0distImpacts = [qPercent0 * i for i in distImpacts]
q1distImpacts = [qPercent1 * i for i in distImpacts]

buffDist = str(quadrantSize + 1) + ' kilometers'
arcpy.MakeFeatureLayer_management(quads, 'distQuad_lyr')
arcpy.SelectLayerByLocation_management('distQuad_lyr', 'WITHIN_A_DISTANCE', distLine, buffDist, 'NEW_SELECTION')
arcpy.CopyFeatures_management('distQuad_lyr', rundir + '/buildFiles/q1LineDistQuads.shp')
q1distQuads = rundir + '/buildFiles/q1LineDistQuads.shp'

arcpy.MakeFeatureLayer_management(q1distQuads, 'q1distQuad_lyr')
q0distCursor = arcpy.da.SearchCursor(distQuads, ['SHAPE@', 'quadSource'])
for q0 in q0distCursor:
    q0distGeo = q0[0]
    q0distkey = q0[1]
    if q0distkey in distDict:
        distDict[q0distkey] = [distDict[q0distkey][i]+q0distImpacts[i] for i in xrange(len(distDict[q0distkey]))]
    else:
        distDict[q0distkey] = q0distImpacts
    
    arcpy.SelectLayerByLocation_management('q1distQuad_lyr', 'WITHIN_A_DISTANCE', q0distGeo, '1 kilometers', 'NEW_SELECTION')
    arcpy.SelectLayerByLocation_management('q1distQuad_lyr', 'ARE_IDENTICAL_TO', q0distGeo, '', 'REMOVE_FROM_SELECTION')
    arcpy.MakeFeatureLayer_management('q1distQuad_lyr', 'q1_lyr')
    q1distCursor = arcpy.da.SearchCursor('q1_lyr', ['quadSource'])
    for q1 in q1distCursor:
        q1distkey = q1[0]
        if q1distkey in distDict:
            distDict[q1distkey] = [distDict[q1distkey][i]+q1distImpacts[i] for i in xrange(len(distDict[q1distkey]))]
        else:
            distDict[q1distkey] = q1distImpacts
    del q1distCursor
    arcpy.SelectLayerByAttribute_management('q1distQuad_lyr', 'CLEAR_SELECTION')
del q0distCursor

#adding etOHdist dictionary impacts to receptor dictionary
for key in distDict:
    if key in receptorDict:
        receptorDict[key] = [receptorDict[key][i] + distDict[key][i] for i in xrange(len(receptorDict[key]))]
    else:
        receptorDict[key] = distDict[key]
        

#-----------------------------------CALCULATIONS COMPLETE-----------------------------------
#-------------WRITING IMPACTS FOR EACH LIFE CYCLE STAGE TO A UNIQUE SHAPEFILE-----

#writing impact values from only farmland to unique shapefiles for establishment
equadCursor = arcpy.da.UpdateCursor(Equads, ['FID', 'GWA', 'AA','HHPA','EA','SA', 'OD', 'HHC','HHNC'])
for quadE in equadCursor:
    qFID = quadE[0]
    if qFID in eDict:
        quadE[1:] = eDict[qFID]
        equadCursor.updateRow(quadE)
del equadCursor

#Writing impact values from only farmland to unique shapefiles for Maintenance & Harvest
hquadCursor = arcpy.da.UpdateCursor(Hquads, ['FID', 'GWA', 'AA','HHPA','EA','SA', 'OD', 'HHC','HHNC'])
for quadH in hquadCursor:
    qFID = quadH[0]
    if qFID in hDict:
        quadH[1:] = hDict[qFID]
        hquadCursor.updateRow(quadH)
del hquadCursor

#Writing emissions from transport to unique shapefile
transQCursor = arcpy.da.UpdateCursor(Tquads, ['GWA', 'AA','HHPA','EA','SA', 'OD', 'HHC','HHNC', 'SHAPE@','quadSource'])
for qu in transQCursor:
    tQuadSource = qu[9]
    for key in receptorTdict:
        if tQuadSource == key:
            qu[:8] = receptorTdict[key]
            transQCursor.updateRow(qu)
del transQCursor

#Writing biorefinery impacts to unique quadrant shapefile with only biorefinery impacts
bquadCursor = arcpy.da.UpdateCursor(Bquads, ['quadSource', 'GWA', 'AA','HHPA','EA','SA', 'OD', 'HHC','HHNC'])
for quadB in bquadCursor:
    qFID = quadB[0]
    if qFID in biorefDict:
        quadB[1:] = biorefDict[qFID]
        bquadCursor.updateRow(quadB)
del bquadCursor

#writing farm quadrant emissions to unique shapefile
quadCursor = arcpy.da.UpdateCursor(Fquads, ['FID', 'GWA', 'AA','HHPA','EA','SA', 'OD', 'HHC','HHNC'])
for quadF in quadCursor:
    qFID = quadF[0]
    if qFID in totalFarmDict:
        quadF[1:] = totalFarmDict[qFID]
        quadCursor.updateRow(quadF)
del quadCursor

#Writing emissions from etOH dist dict to unique shapefile
distQCursor = arcpy.da.UpdateCursor(Dquads, ['GWA', 'AA','HHPA','EA','SA', 'OD', 'HHC','HHNC', 'SHAPE@','quadSource'])
for qu in distQCursor:
    dQuadSource = qu[9]
    for key in distDict:
        if dQuadSource == key:
            qu[:8] = distDict[key]
            distQCursor.updateRow(qu)
del distQCursor


#*********** WRITING RECEPTOR DICTIONARY VALUES TO CORRESPONDING QUADRANTS **********
#farmland and biorefinery emissions
n = 1
numberQ = len(receptorDict.keys())
quadCursor = arcpy.da.UpdateCursor(Pquads, ['FID', 'GWA', 'AA','HHPA','EA','SA', 'OD', 'HHC','HHNC'])
for quad in quadCursor:
    qFID = quad[0]
    if qFID in receptorDict:
        quad[1:] = receptorDict[qFID]
        quadCursor.updateRow(quad)
        n = n + 1
        
        # ******TIME******
        t5 = datetime.datetime.now()
        c= t5-t0
        min = divmod(c.total_seconds(), 60)[0]
        sec = divmod(c.total_seconds(), 60)[1]
        print 'Writing values for relevant quadrants. Quad {0}/{3} complete. Total elapsed Time: {1} min {2} seconds'.format(n, min, sec, numberQ)
        arcpy.AddMessage('Writing values for relevant quadrants. Quad {0}/{3} complete. Total elapsed Time: {1} min {2} seconds'.format(n, min, sec, numberQ))
        # ******TIME******
del quadCursor

#adding transportation dictionary impacts to receptor dictionary
for key in receptorTdict:
    if key in receptorDict:
        receptorDict[key] = [receptorDict[key][i] + receptorTdict[key][i] for i in xrange(len(receptorDict[key]))]
    else:
        receptorDict[key] = receptorTdict[key]

#farmland, biorefinery, transportation, and distribution emissions
quadCursor = arcpy.da.UpdateCursor(PTquads, ['FID', 'GWA', 'AA','HHPA','EA','SA', 'OD', 'HHC','HHNC'])
for quad in quadCursor:
    qFID = quad[0]
    chems = quad[1:]
    if qFID in receptorDict:
        for i, v in enumerate(receptorDict[qFID]):
            chems[i] = v
        quad[1:] = chems
        quadCursor.updateRow(quad)
del quadCursor

#----------TEXT FILE: Writing transportation data to text file, in 'Products' directory------------------------
outFile = open(Pdir + '/runInfo.text', 'w')
outFile.write('total farm area = ' + str(totalFarea) +'\n'+ 'total tkm = ' + str(totalTKM) +'\n'+ 'total feedstock yield = ' + str(totalYield) +'\n'+ 'totaldistKM = ' + str(totaldistKM))
outFile.close()
del outFile

#******TIME*********
t6 = datetime.datetime.now()
c= t6-t0
min = divmod(c.total_seconds(), 60)[0]
sec = divmod(c.total_seconds(), 60)[1]
print 'Script complete. Total runtime: {0} min {1} seconds'.format(min, sec)
#******TIME*********
