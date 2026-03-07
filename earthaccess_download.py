# Download H5 granules from NASA 
# developed as part of a final project for GEOM 4009

# Author: Vincent Ribberink

# earthaccess.login() -> keeps a .netrc file of credentials
    # remove "persist=True" if you want to avoid saving credentials locally

import earthaccess 
import geopandas as gpd
import shapely
import configparser
from pathlib import Path

### read config
def read_config(config_path):
    
    config = configparser.ConfigParser()

    config.read(config_path)

    # read in parameters
    polygons_path = config['CONFIG']['PolygonsPath']
    download_dir = config['CONFIG']['DownloadDir']
    short_name = config['CONFIG']['ShortName']
    start_date = config['CONFIG']['StartDate']
    end_date = config['CONFIG']['EndDate']

    ### validation

    # geometry
    if Path(polygons_path).is_file() == False:
        raise FileNotFoundError("input geometry filepath is invalid")

    # download directory
    if download_dir == None:
        download_dir = (Path.cwd() / "download_dir").mkdir()
        print("No download directory specified.\nGranules will be downloaded at {download_dir}")

    elif Path(download_dir).is_dir() == False:
        raise FileNotFoundError("input download directory is invalid")

    # short name -> leave validation to earthaccess

    # date range -> testing required later
    date_range = (start_date, end_date)

    return polygons_path, download_dir, short_name, date_range

### authenticate earthdata session
def authenticate(status_check=True):

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

    # read config file
    config_list = read_config('config_earthaccess.txt')
    polygons_path, download_dir, short_name, date_range = config_list

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



