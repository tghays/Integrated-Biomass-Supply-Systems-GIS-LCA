# Spatial-Bioethanol-LCA

This script conducts a Spatial Life Cycle Assessment of bioethanol production in North Carolina.  The script is written in Python and primarily uses the arcpy package to conduct geoprocessing operations.  This script reflects the Master's Thesis research of Tyler Hays, Department of Forest Biomaterials, NC State University.  The corresponding thesis can be referenced for further background, as this documentation only provides supplementary information on how to run the script.  The thesis title is "The Application of Geographic Information Systems in an Environmental Life Cycle Assessment of a Bioethanol Production System" and can be found in the NC State University Theses/Disserations Repository, beginning January 2017.

Life Cycle Assessment (LCA) is a methodology to determine the environmental impact from the complete life cycle of a product or service.  All life cycle stages are observed and the inputs/outputs for each life cycle stage are used in a Life Cycle Impact Assessment to determine the life cycle impacts.  This work applies these impacts from the bioethanol production life cycle to a geographic location.  This work considers the bioethanol production from cradle to ethanol distributor gate (cradle to gate).  Life cycle stages included in the study boundary are farmland establishment, feedstock maintenance and harvest, feedstock transportation to the biorefinery, ethanol conversion at the biorefinery, and ethanol distribution to the ethanol terminal.  Two feedstocks are considered for bioethanol production, a starch feedstock (corn grain) and a cellulosic feedstock (switchgrass).  A grid of quadrants is overlaid on the study area to retain life cycle impact values.

Each life cycle stage has a corresponding loop in the script to distribute the impacts across the landscape.  Farmland operation life cycle stages (establishment, maintenance and harvest) are combined into one loop.  The pseudocode for the script is below.
--------
FOR every quadrant
	SELECT farm polygons whose centroid is contained within quadrant (selection = primary quadrant)
	IF selection = TRUE
		GET FID for primary quadrant
		CALCULATE total farmland impacts based on farmland polygon area in primary quadrant
		CALCULATE 70% of Establishment impacts for primary quadrant
		CALCULATE 3.75% of Establishment impacts for secondary quadrants
		CALCULATE 70% of Harvest impacts for primary quadrant
		CALCULATE 3.75% of Harvest impacts for secondary quadrants
		WRITE Establishment impacts for primary quadrant to Establishment dictionary using FID for primary quadrant as key
		WRITE Harvest impacts for primary quadrants to Harvest dictionary using FID for primary quadrant as key
		SELECT quadrants bordering primary quadrant (selection = secondary quadrants)
		GET FID’s for secondary quadrants
		FOR each secondary quadrant FID
			WRITE Establishment impacts for secondary quadrants to Establishment dictionary using FID for secondary quadrant 			as key
			WRITE Harvest impacts for secondary quadrants to Harvest dictionary using FID for secondary quadrants as key
		END FOR
		CALCULATE total transportation impacts scaled to feedstock yield from farmland in quadrant
		CREATE line from quadrant centroid to biorefinery
		SELECT quadrants intersecting transportation line (selected quadrants = primary quadrants for transportation impacts)
		DIVIDE total transportation impacts by the number of intersected primary quadrants
		CALCULATE 70% of divided transportation impacts for primary quadrants
		CALCULATE 3.75% of divided transportation impacts for secondary quadrants
		FOR each intersected primary quadrant
			GET FID
			WRITE transportation impacts for primary quadrant to Feedstock Transportation dictionary using FID as key
			SELECT quadrants bordering primary quadrant (selection = secondary quadrants for transportation impacts)
			FOR every secondary quadrant
				GET FID
				WRITE transportation impacts for secondary quadrant to Feedstock Transportation dictionary using FID as 				key
			END FOR
		END FOR

	END IF
END FOR

CALCULATE 70% of total biorefinery impacts for primary quadrants
CALCULATE 3.75% of total biorefinery impacts for secondary impacts
SELECT quadrant containing biorefinery (selection = primary quadrant)
GET FID of primary quadrant
WRITE impacts for primary quadrants to Biorefinery dictionary using FID as key
SELECT quadrants bordering primary quadrant (selection = secondary quadrants)
FOR each secondary quadrant
	GET FID
	WRITE impacts for secondary quadrants to Biorefinery dictionary using FID as key
END FOR

CALCULATE 70% of Ethanol Distribution impacts for primary quadrants
CALCUALTE 3.75% of Ethanol Distribution impacts for secondary quadrants 
SELECT quadrants intersecting line of Ethanol Distribution Route (selection = primary quadrants)
FOR each intersected primary quadrant
GET FID
	WRITE ethanol distribution impacts for primary quadrants to Ethanol Distribution dictionary using FID as key
	SELECT quadrants bordering primary quadrant (selection = secondary quadrants)
	FOR each secondary quadrant
		GET FID
		WRITE ethanol distribution impacts for secondary quadrants to Ethanol Distribution dictionary using FID as key
	END FOR
END FOR

FOR each key in [Life Cycle Stage] dictionary
	GET impact values
	OPEN [Life Cycle Stage] quadrant shapefile
	FIND quadrant FID using key
	WRITE impact values to quadrant
END FOR
