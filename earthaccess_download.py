# Download H5 granules from NASA 
# developed as part of a final project for GEOM 4009

# Author: Vincent Ribberink

# earthaccess.login() -> keeps a .netrc file of credentials
    # remove "persist=True" if you want to avoid saving credentials locally

import earthaccess 
import geopandas as gpd
import shapely
from pathlib import Path
from process_sat_lidar import read_config

### authenticate earthdata session
def authenticate(status_check=False):
    """
    Authenticate Earthdata credentials and initialize a session

    Optional
    ----------
    status_check : Boolean
        Default = False
        Run a status check on the session authentication and connection.
        This can take >1 minute

    Returns
    -------
    None
    """

    earthaccess.login(persist=True)

    # check status before starting -> slow and probably not necessary
    if status_check == True:
        nasa_status = earthaccess.status()

        if nasa_status['Earthdata Login'] != 'OK':
            raise ValueError("Earthdata login not initialized properly")
        
        if nasa_status['Common Metadata Repository'] != 'OK':
            raise ValueError("Connection to Common Metadata Repository (CMR) not functioning properly")
        
    print("\nauthentication successful")
    
### query granules
def search(short_name, date_range, polygon):
    """
    Query NASA EarthData products

    Parameters
    ----------
    short_name : string
        Short name of the Earthdata product (e.g. GEDI02_A)
    date_range : tuple
        Start and end date as strings in YYYY-MM-DD format
    polygon : string
        Short name of the Earthdata product (e.g. GEDI02_A)

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

    # if no granules were passed
    if len(granules) == 0:
        raise ValueError("no granules in input") 

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

    Returns
    -------
    None
    """

    # read config file
    config_dict = read_config("config_earthaccess.txt")

    # unpack parameters
    polygons_path = config_dict['PolygonsPath']
    download_dir = config_dict['DownloadDir']
    short_name = config_dict['ShortName']
    date_range = config_dict['DateRange']

    # read in polygons
    gdf = gpd.read_file(polygons_path)

    # EarthData authentication -> can be slow
    authenticate(status_check=False) 

    # explode any multipolygons -> earthdata only accepts single Polygon objects
    boom = gdf.explode(index_parts=True) # creates new index

    # iterate through polygons
    for idx, row in boom.iterrows():
        print(f"\n{row['Name']} started")

        # get linear ring from geometry
        polygon = list(shapely.get_coordinates(row.geometry.exterior))

        # query granules
        granules = search(short_name, date_range, polygon)

        # download granules
            # adding a local directory avoids double downloads
        filelist = download(granules, download_dir)
    
    print("\n all polygons complete\n")
    
if __name__ == "__main__":
    main()



