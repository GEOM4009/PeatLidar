# all code combined

import pandas as pd
import geopandas as gpd
import h5py
import configparser
from pathlib import Path
from datetime import datetime

### read config
def read_config(config_path):
    
    """
    Read and validate parameters from a config file.
    Config file must be written in .ini format, though the file can be .txt
    Based on ConfigParser user guide

    @author: Vincent Ribberink

    Parameters
    ----------
    config_path : string
        Path pointing to the config file 

    Returns
    -------
    config_dict (dictionary): 
        Dictionary containing the validated parameters
    """

    # initialize config parser
    config = configparser.ConfigParser()

    # read config file
    config.read(config_path)

    ### read in parameters 

    # INPUT
    PolygonsPath = config['INPUT']['PolygonsPath']
    DownloadDir = config['INPUT']['DownloadDir']
    ShortName = config['INPUT']['ShortName']
    StartDate = config['INPUT']['StartDate']
    EndDate = config['INPUT']['EndDate']

    # ATL08
    BeamType = config['ATL08']['BeamType']
    NightOnly = config['ATL08']['NightOnly']

    # GEDI02_A
    QualityFlag = config['GEDI02_A']['QualityFlag']

    # OUTPUT
    OutputDir = config['OUTPUT']['OutputDir']
    OutputCSV = config['OUTPUT']['OutputCSV']
    OutputShapefile = config['OUTPUT']['OutputShapefile']
    OutputParquet = config['OUTPUT']['OutputParquet']


    ##################
    ### Validation ###
    ##################

    #################
    ### Input

    # geometry
    if Path(PolygonsPath).is_file() == False:
        raise FileNotFoundError("input geometry filepath is invalid")

    # download directory
    if Path(DownloadDir).is_dir() == False:
        raise FileNotFoundError("input download directory is invalid or does not exist")
    
    # short name 
    if ShortName not in ['ATL08', 'GEDI']:
        raise ValueError("Input short name is invalid")

    # date range
    format = "%Y-%m-%d"
    def validate_date_str_format(date_str, format):
        """
        check if a date string matches a given format
        based on example from https://www.geeksforgeeks.org/python/python-validate-string-date-format/

        @author: Vincent Ribberink

        Parameters
        ----------
        date_str : string
            date string to validate
        format : string
            format usable by datetime (e.g. "%Y-%m-%d")

        Returns
        -------
        None. Raises ValueError if date_str doesn't match format
        """
        valid = datetime.strptime(date_str, format)
        if not valid:
            raise ValueError("one or more input dates are invalid. please use YYYY-MM-DD format")

    validate_date_str_format(StartDate, format)
    validate_date_str_format(StartDate, format)

    #################
    ### ATL08

    # ATL08 beam type 
    if BeamType not in ['strong', 'weak', 'all']:
        raise ValueError("input ATL08 beam type is invalid. Please use one of (strong, weak, both)")

    # ATL08 night flag -> check values first
    if NightOnly not in ["True", "False"]:
        raise ValueError("Night flag parameter is invalid. Please use one of (True, False))")

    #################
    ### GEDI02_A

    # GEDI02_A quality flag -> check values first

    #################
    ### Output

    # Output directory
    if Path(OutputDir).is_dir() == False:
        raise FileNotFoundError("input download directory is invalid or does not exist")

    # Output Formats
    for out_format in [OutputCSV, OutputShapefile, OutputParquet]:
        if out_format not in ["True", "False"]:
            raise ValueError("one or more output format parameters are invalid. Please use one of (True, False))")

    # format date range for output
    date_range = (StartDate, EndDate)

    # create config dictionary
    config_dict = {
        'PolygonsPath' : PolygonsPath,
        'DownloadDir' : DownloadDir,
        'ShortName' : ShortName,
        'DateRange' : date_range,
        'BeamType' : BeamType,
        'NightOnly' : NightOnly,
        'QualityFlag' : QualityFlag,
        'OutputDir' : OutputDir,
        'OutputCSV' : OutputCSV,
        'OutputShapefile' : OutputShapefile,
        'OutputParquet' : OutputParquet,
    }

    print("---------------------------------")
    print("Config validated!")

    return config_dict


# filter and extract ICESat-2 vegetation height
def convert_icesat(granules, beam_type, night_only):
    """
    Converts ICESat data from h5 files to dataframes
    Based on Xarray documentation examples

    @authors: Vincent Ribberink, Joshua Salvador

    Parameters
    ----------
    test_files : list
        List containing paths of ICESat-2 ATL08 .h5 granules

    Returns
    -------
    None
    """

    print("---------------------------------")
    print("Started extracting ATL08 data")

    # list of groups containing beam data
    beam_list = ["gt1l", "gt2l", "gt3l", "gt1r", "gt2r", "gt3r"] # groups in h5 file

    # create empty list #1
    df_combined_list = []

    # iterate through h5 files in directory
    for file in granules:
        # read file with H5py
        f = h5py.File(file)

        ### beam type filter

        # if beam_type == all -> continue
        
        # get orientation (backward/forward/transition, 0/1/2)
        orientation = f['orbit_info']['sc_orient'][0]

        # transition period -> low quality data, skip
        if orientation == 2:
            continue

        if beam_type == "strong":
            
            # forward orientation
            if orientation == 1:
                # right beams are strong 
                beam_list = beam_list[3:]

            # backwards orientation
            if orientation == 0:
                # left beams are strong
                beam_list = beam_list[:3]

        if beam_type == "weak":
            
            # forward orientation
            if orientation == 1:
                # left beams are weak 
                beam_list = beam_list[:3]

            # backwards orientation
            if orientation == 0:
                # right beams are weak
                beam_list = beam_list[3:]
        
        # create empty list #2
        df_list = []

        # iterate through groups to find beam data
        for group in list(f.keys()):
            if group in beam_list:
                
                # create pandas dataframe with canopy height, coordinates
                df = pd.DataFrame({
                        "icesat_canopy" : f[f"{group}/land_segments/canopy/h_canopy"][:],
                        "icesat_canopy_uncertainty" : f[f"{group}/land_segments/canopy/h_canopy_uncertainty"][:],
                        "longitude" : f[f"{group}/land_segments/longitude"][:],
                        "latitude" : f[f"{group}/land_segments/latitude"][:],
                        "night_flag" : f[f"{group}/land_segments/night_flag"][:],
                        "beam" : str(group)
                })

                # filter night flag
                if (night_only == True):
                    df = df.loc[df['night_flag']==1]
                
                # add to list #2
                df_list.append(df)

        # continue if no results are found
        if not df_list:
            continue      
        # concatenate all beams for a given file
        df_combined = pd.concat(df_list)

        # add to list #1
        df_combined_list.append(df_combined)

    # concatenate all files
    final = pd.concat(df_combined_list).reset_index()

    print(f"{len(final)} filtered observations returned")

    # export to csv for testing purposes
    #final.to_csv("icesat.csv")

    return final


# filter and extract GEDI vegetation height
def convert_gedi(granules, quality_flag):
    """
    Converts GEDI files from h5 to dataframes

    @author: Joshua Salvador

    Parameters
    ----------
    files : list
        List containing paths of GEDI L2A .h5 granules

    Returns
    -------
    None
    """

    print("---------------------------------")
    print("Started extracting GEDI02_A data")

    # place all data in here
    all_data = []
    
    # look through each file
    for file in granules:
        #print(f"Processing {file}")
    
        with h5py.File(file, 'r') as f:
            for beam_name in f.keys():
                beam = f[beam_name]
    
                # if beam contains data
                if 'shot_number' in beam:
                    shot = beam['shot_number'][:]
                    rh = beam['rh'][:]
                    lat = beam['geolocation/lat_lowestmode_a1'][:]
                    lon = beam['geolocation/lon_lowestmode_a1'][:]
                    elev = beam['elev_lowestmode'][:]
                    qual = beam['quality_flag'][:]
    
                    canopy_h = rh[:,98]
    
                    df = pd.DataFrame({
                        'file': file,
                        'beam': beam_name,
                        'shot_number': shot,
                        'latitude': lat,
                        'longitude': lon,
                        'elevation': elev,
                        'gedi_canopy': canopy_h,
                        'quality': qual
                    })
    
                    df2 = df.loc[df.quality==1]
                    
                    all_data.append(df2)
                    
    # concatenate all data
    final_df = pd.concat(all_data, ignore_index=True)

    print(f"{len(final_df)} filtered observations returned")
    
    # convert to csv for testing purposes
    #final_df.to_csv("gedi.csv", index=False)

    return final_df

'''
# initial spatial join -> filter results within 50 m to save storage space and processing time
# GEDI footprints are 25 m circles, icesat approximated with 8 meter circles
# may not be necessary
def within_100m(geom, df, xcol, ycol, crs):

    # project geometry
    geom = geom.to_crs(crs) # Statistics Canada Lambert -> should work for most of Canada

    # convert points to gdf
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[xcol], df[ycol]), crs="EPSG:4326")

    # project points
    gdf.to_crs(crs, inplace=True) 

    # remove invalid geometries
    gdf = gdf.loc[gdf.geometry.is_valid]

    # spatial join
    gdf_join = gdf.sjoin_nearest(geom, how='inner', max_distance=50, distance_col="distance")

    return gdf_join
'''

# aggregate data by polygons
def aggregate(polygons_path, icesat_df, gedi_df):
    """
    Converts GEDI files from h5 to dataframes

    @author: Ethan Gauthier (lead), Vincent Ribberink

    Parameters
    ----------
    polygon_path : string
        Path pointing to input geometry

    Returns
    -------
    None
    """

    aoi = gpd.read_file(polygons_path)

    print("---------------------------------")
    print(f"Starting aggregation for {len(aoi)} polygons")

    #Adding the polygon_id
    aoi["polygon_id"] = range(0, len(aoi)) # changed this to start index at 0

    #Assigning polygon ids to Lidar csvs
    def assign_polygon_ids(df, aoi_gdf, satellite_name):

        #Convert Lidar points to GeoDataFrame
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df.longitude, df.latitude),
            crs=aoi_gdf.crs
        )

        #Spatial join by polygon_id
        joined = gpd.sjoin(gdf, aoi_gdf[["polygon_id", "geometry"]], how="inner")

        #Drop geometry for clean DataFrame
        return pd.DataFrame(joined.drop(columns="geometry"))
    
    #Reading the csv
    #icesat_df = pd.read_csv("icesat.csv")
    #gedi_df = pd.read_csv("gedi.csv")

    icesat_joined = assign_polygon_ids(icesat_df, aoi, "ICESat-2")
    gedi_joined = assign_polygon_ids(gedi_df, aoi, "GEDI")

    #
    def aggregate_by_polygon(df, stats, satellite_name):
        #Group by polygon
        grouped = df.groupby("polygon_id")

        #Detect measurement columns
        measurement_cols = [
            col for col in df.columns
            if col in ["icesat_canopy", "icesat_canopy_uncertainty", "gedi_canopy", "elevation"]
        ]

        #Compute stats
        result = grouped[measurement_cols].agg(stats)

        #Flatten multi-index columns
        result.columns = ["_".join(col) for col in result.columns]
        result = result.reset_index()

        #Add satellite label
        result["satellite"] = satellite_name

        return result
    
    #Running aggregation
    stats = ["mean", "min", "max", "std"]

    icesat_agg = aggregate_by_polygon(icesat_joined, stats, "ICESat-2")
    gedi_agg = aggregate_by_polygon(gedi_joined, stats, "GEDI")


    # export to csv for testing purposes
    #icesat_agg.to_csv("icesat_agg.csv")
    #gedi_agg.to_csv("gedi_agg.csv")

    print("Aggregation complete")

    return icesat_agg, gedi_agg
    

# compare
def compare_data(icesat_agg, gedi_agg):
    """
    Compares ICESat canopy data with GEDI canopy data

    @author: Joshua Salvador 

    Parameters
    ----------
    df : dataframe
        dataframe containing both ICESat and GEDI data

    Returns
    -------
    None
    """

    print("---------------------------------")
    print("Starting comparison")

    #Combine the stats into one
    df = pd.concat([icesat_agg, gedi_agg], ignore_index=True)

    # Merge duplicated polygon IDs
    df2 = df.groupby("polygon_id").first().reset_index()
    
    # Make sure both icesat and gedi contains data
    df3 = df2.dropna(subset=["icesat_canopy_mean", "gedi_canopy_mean"]).copy()
    
    # Calculate difference for icesat canopy height mean, max, min, std with gedi.
    df3["mean_diff"] = df3["icesat_canopy_mean"] - df3["gedi_canopy_mean"]
    df3["max_diff"]= df3["icesat_canopy_max"] - df3["gedi_canopy_max"]
    df3["min_diff"] = df3["icesat_canopy_min"] - df3["gedi_canopy_min"]
    df3["std_diff"] = df3["icesat_canopy_std"] - df3["gedi_canopy_std"]
    
    # Export as CSV for testing purposes
    df3.to_csv("comparison.csv", index=False)

    print("Comparison complete")

    return df3


# format and export
def export(icesat_agg, gedi_agg, compared, polygons_path, out_dir, config_dict):
    """
    Format and export the aggregated and compared results as .shp, .csv, and/or .parquet

    @author: Vincent Ribberink

    Parameters
    ----------
    icesat_agg : Pandas DataFrame
        Aggregated ICESat-2 ATL08 data
    gedi_agg : Pandas DataFrame
        Aggregated GEDI L2A data
    compared : Pandas DataFrame
        Comparison DataFrame of ICESat-2 ATL08 and GEDI L2A aggregated data
    polygons_path : string
        Path pointing to input geometry
    file_formats : list
        list of file formats as strings
    out_dir : string
        Path pointing to directory where outputs are written
    config_dict : dictionary
        dictionary of parameters 

    Returns
    -------
    None
    """

    ### NEEDS TESTING

    print("---------------------------------")
    print("Starting export")

    # read output configurations, convert to boolean
    out_csv = (config_dict['OutputCSV'] == 'True')
    out_shp = (config_dict['OutputShapefile'] == 'True')
    out_parquet = (config_dict['OutputParquet'] == 'True')

    # fix polygon ID for comparison df
    '''
    compared = compared.reset_index()
    compared['polygon_id'] = compared['index'] + 1
    compared.drop(columns=['index'])
    '''

    # export to csv
    if out_csv:
        icesat_agg.to_csv((out_dir + '/icesat_agg.csv'))
        gedi_agg.to_csv((out_dir + '/gedi_agg.csv'))
        compared.to_csv((out_dir + '/comparison.csv'))

    # export to parquet
    if out_parquet:
        icesat_agg.to_parquet((out_dir + '/icesat_agg.parquet'))
        gedi_agg.to_parquet((out_dir + '/gedi_agg.parquet'))
        compared.to_parquet((out_dir + '/comparison.parquet'))

    if out_shp:

        # read geometry
        geom_gdf = gpd.read_file(polygons_path)
        geom = geom_gdf.geometry

        # convert to geodataframes
        ice_agg_gdf = gpd.GeoDataFrame(icesat_agg, geometry=geom)
        gedi_agg_gdf = gpd.GeoDataFrame(gedi_agg, geometry=geom)
        comp_gdf = gpd.GeoDataFrame(compared, geometry=geom)

        # TO DO -> rename columns to avoid ambiguity from truncation when exporting as shp

        # export as shp
        ice_agg_gdf.to_file((out_dir + '/icesat_agg.shp'))
        gedi_agg_gdf.to_file((out_dir + '/gedi_agg.shp'))
        comp_gdf.to_file((out_dir + '/comparison.shp'))

    print("Exporting complete")


def main():

    """
    Run the process_sat_lidar script.
    This does not download the granules from NASA - use earthaccess_download.py

    @author: Vincent Ribberink

    Returns
    -------
    None.
    """

    # read config
    config_dict = read_config("config_process_sat_lidar.txt")

    # unpack parameters
    polygons_path = config_dict['PolygonsPath']
    download_dir = config_dict['DownloadDir']
    output_dir = config_dict['OutputDir']
    beam_type = config_dict['BeamType']
    night_only = config_dict['NightOnly']
    quality_flag = config_dict['QualityFlag']
  
    # check existing granules in the download directory
    ATL08_granules = list(Path(download_dir).glob("ATL08*.h5"))
    GEDI02_A_granules = list(Path(download_dir).glob("GEDI02_A*.h5"))
    print("---------------------------------")
    print(f"{len(ATL08_granules)} ATL08 granules found")
    print(f"{len(GEDI02_A_granules)} GEDI02_A granules found")

    ### run appropriate h5 conversions
    # ICESat-2 ATL08
    icesat_df = convert_icesat(ATL08_granules, beam_type, night_only)
    print("ICESat-2 ATL08 granules complete")
    # GEDI L2A
    gedi_df = convert_gedi(GEDI02_A_granules, quality_flag)
    print("GEDI L2A granules complete")
 
    # aggregate by polygon
    icesat_agg, gedi_agg = aggregate(polygons_path, icesat_df, gedi_df)

    # run comparison
    compared = compare_data(icesat_agg, gedi_agg)

    # format and export
    export(icesat_agg, gedi_agg, compared, polygons_path, output_dir, config_dict)

if __name__ == "__main__":
    main()
    

        
