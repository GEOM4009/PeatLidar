# About

PeatLidar is a tool used to download and aggregate satellite lidar data to one or more polygons.

This was designed to extract canopy height data from ICESat-2 ATL08 and GEDI L2A products. A comparison is done if data from both products is present in a polygon.

Python Dependencies:
- geopandas
- earthaccess
- h5py
- *configparser*
- *pathlib*
- *datetime*
- *OS*


This tool was developed as part of a final project for the GEOM4009 course at Carleton University.

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

## Prerequisites

With a valid Conda install, run the following to create the required Conda environment

`conda env create -f peatlidar.yml`


NASA EarthData account credentials are required for downloading data. An account can be created for free [here](https://urs.earthdata.nasa.gov/users/new)

---

## Setup

### Config

Both the download (*earthaccess_download.py*) and aggregation/processing scripts (*process_sat_lidar.py*) use a configuration file to store various parameters. This file can be created manually, copied from the examples in /sample_polygons, or created interactively with the optional third script *user_input3.py*. This file must be use INI format.

## User Guide









