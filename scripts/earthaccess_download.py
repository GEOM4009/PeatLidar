# Download H5 granules from NASA 
# developed as part of the PeatLidar final project for GEOM 4009

# Author: Vincent Ribberink

# earthaccess.login() -> uses an interactive login
    # change "persist=False" to True if you want to save credentials locally (.netrc file)

import earthaccess 
import geopandas as gpd
#import shapely # used for downloading polygon by polygon in (not used by default)
from pathlib import Path
from scripts.process_sat_lidar import read_config

### authenticate earthdata session
def authenticate(status_check=False): 
    """
    Authenticate Earthdata credentials and initialize a session

    @author: Vincent Ribberink

    Optional
    ----------
    status_check : Boolean
        Default = False
        When true, run a status check on the session authentication and connection.
            raises an error if login or connection are invalid
            This can take >1 minute

    Returns
    -------
    None
    """

    print("Authenticating...")

    earthaccess.login(persist=True)

    # check status before starting -> slow and probably not necessary
    if status_check == True:
        nasa_status = earthaccess.status()

        if nasa_status['Earthdata Login'] != 'OK':
            raise ValueError("Earthdata login not initialized properly")
        
        if nasa_status['Common Metadata Repository'] != 'OK':
            raise ValueError("Connection to Common Metadata Repository (CMR) not functioning properly")
        
    print("\nAuthentication successful")
    
### query granules
def search(short_name, date_range, polygon):
    """
    Query NASA EarthData products

    @author: Vincent Ribberink

    Parameters
    ----------
    short_name : string
        Short name of the Earthdata product (e.g. GEDI02_A)
    date_range : tuple
        Start and end date as strings in YYYY-MM-DD format
    polygon : list
        Linear ring of the input polygon

    Returns
    -------
    granules : list
        List of granule IDs returned by the query
    """

    # query for granules
    granules = earthaccess.search_data(
        short_name=short_name,
        cloud_hosted=True,
        temporal = date_range,
        polygon = polygon
        )
    
    # print number of granules found
    gran_count = len(granules)
    print(f"{gran_count} granules found.")

    return granules

### download granules
def download(granules, download_dir):
    """
    Download granules from NASA Earthdata

    Parameters
    ----------
    granules : list
        List of granule IDs
    download_dir : string
        Path of the download directory

    Returns
    -------
    filelist : list
        List of filepaths of downloaded granules
    """


    # download from NASA
    print(f"starting download of {len(granules)} granules")
    filelist = earthaccess.download(granules, 
                                    local_path = str(download_dir), 
                                    threads=8, 
                                    show_progress=True) 

    return filelist

def main():
    """
    Run the earthaccess_download script

    @author: Vincent Ribberink

    Returns
    -------
    None
    """

    ############
    # TESTING #
    import os
    # change this to the appropriate sample 
    os.chdir("sample_polygons/Alfred_Bog")
    # TESTING #
    ###########

    # read config file
    config_dict = read_config("config_process_sat_lidar.txt")

    # unpack parameters
    polygons_path = config_dict['PolygonsPath']
    download_dir = config_dict['DownloadDir']
    short_name = config_dict['ShortName']
    date_range = config_dict['DateRange']

    # read in polygons
    gdf = gpd.read_file(polygons_path)

    # EarthData authentication -> can be slow
    authenticate(status_check=False) 

    '''
    Downloading by individual polygon was removed due to issues with invalid geometries
    and long processing times with large numbers of polygons, but may still be useful in some cases

    # explode any multipolygons -> earthdata only accepts single Polygon objects
    boom = gdf.explode(index_parts=True).reset_index() 

    # iterate through polygons
    for idx, row in boom.iterrows():
        print(f"\n{row['Name']} started")
        # get linear ring from geometry
        polygon = list(shapely.get_coordinates(row.geometry.exterior))
    '''

    # fix short name
    if short_name == 'both':
        short_name = ['ATL08', 'GEDI02_A']
    else:
        short_name = [short_name]

    # iterate through short names
    for name in short_name:

        # get bounding box as linear ring -> this results in larger downloads, but too many issues were 
            # encountered downloading polygon by polygon
        minx, miny, maxx, maxy = gdf.total_bounds
        polygon = [(minx, miny),  (maxx, miny), (maxx, maxy),  (minx, maxy), (minx, miny)]

        # query granules
        granules = search(name, date_range, polygon)

        # skip download if no granules were found in query
        if len(granules) == 0:
            continue

        # download granules
        # adding a local directory avoids double downloads
        filelist = download(granules, download_dir)
    
    print(f"\n {name} download complete\n")


if __name__ == "__main__":
    main()



