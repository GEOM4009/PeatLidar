# PeatLidar - About

PeatLidar is a tool used to download and aggregate satellite lidar data to one or more polygons.

This was designed to extract canopy height data from ICESat-2 ATL08 and GEDI L2A products. A comparison is done if data from both products is present in a polygon.

## General Workflow

**earthaccess_download.py** - Download granules (large chunks of data)
1. Get bounding box of input polygons
2. Query granules for given extent & date range
3. Download granules to local directory

![Flowchart - Download](images/flowcharts_download.jpg)

**process_sat_lidar.py** - Aggregate by polygon and compare
1. Extract canopy height from downloaded granules
2. Apply various filters (Night Flag, Beam Type) - See config
3. Aggregate by polygon (mean, min, max, stdev)
4. Compare GEDI L2A to ICESat-2 ATL08 values if both are present
5. Export aggregated data and/or comparison as one or more of CSV, 

![Flowchart - Aggregation](images/flowcharts_process.jpg)

**user_input3.py** - Optional script for interactively creating the config file

---

Python Dependencies:
- geopandas
- earthaccess
- h5py
- *configparser*
- *pathlib*
- *datetime*
- *OS*

This tool was developed as part of a final project for the Winter 2026 GEOM4009 Custom Geomatics Applications course at Carleton University.

Authors: Vincent Ribberink, Joshua Salvador, Ethan Gauthier

---

# Contents

**docs** - Documentation and related files generated with Sphinx

**scripts** - The three Python scripts comprising the tool

**samples** - Sample polygons, config files, and outputs for two demo folders. See User Guide below for how to run a demo

> /Alfred_Bog - 268 polygons, small area, E Ontario

> /Lake_Claire - 1 polygon, large area, N Alberta

**images** - Image files used throughout the documentation

**peatlidar.yml** - Conda environment file

---

# Getting Started

## Setup/Installation

### Conda Environment

With a valid Conda install, run the following to create the required Conda environment

`conda env create -f peatlidar.yml`


NASA EarthData account credentials are required for downloading data. An account can be created for free [here](https://urs.earthdata.nasa.gov/users/new)

### Clone Repository Locally

Change the working directory to the desired location for the cloned directory, then run

`git clone https://github.com/GEOM4009/PeatLidar.git`

### Config

Both the download (*earthaccess_download.py*) and aggregation/processing scripts (*process_sat_lidar.py*) use a configuration file to store various parameters. This file can be created manually, copied from the demo examples in */samples*, or created interactively with the optional third script *user_input3.py*. This file must be use INI format.

---

## User Guide

This section will give a brief overview on how to run the *"Alfred_Bog"* demo:



### 

---

## FAQ/Troubleshooting

**Do I have to enter my credentials every time I run earthaccess_download.py()?:** In earthaccess_download.authenticate(), "earthaccess.login("persist=False") can be set to True to store credentials locally in a .netrc file to avoid this.

**EarthData Authentication is taking a long time:** It can take 1-2 minutes depending on connection speed.

**No granules were found by earthaccess_download.py():** Try expanding the date range and/or choose a larger area.

**sjoin() got an unexpected keyword argument 'distance':** This is a relatively recent addition to sjoin(), try updating GeoPandas. If it still doesn't work, change the predicate to 'intersects' and use a buffer to simulate the footprints instead.

**There are a bunch of warnings when exporting as a Shapefile:** These are just truncation warnings, meaning some field names are too long for a Shapefile and they will be shortened to 10 characters. This can be avoided by renaming the columns or exporting to a different format.








