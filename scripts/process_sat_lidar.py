##### process_sat_lidar.py #####
# reads and aggregates ICESat-2 ATL08 and GEDI L2A satellite lidar data
# this does not download any data, please use earthaccess_download.py

import pandas as pd
import geopandas as gpd
import h5py
import configparser
from pathlib import Path
from datetime import datetime

### read and validate configuration
def read_config(config_path):
    
    """
    Read and validate parameters from a config file.
    Config file must be written in .ini format, though the file can be .txt
    Based on ConfigParser user guide: https://docs.python.org/3/library/configparser.html#quick-start

    @author: Vincent Ribberink

    Parameters
    ----------
    config_path : string
        Path pointing to the config file 

    Returns
    -------
    config_dict (dictionary): 
        Dictionary containing the validated parameters as strings
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
    if ShortName not in ['ATL08', 'GEDI02_A', 'both']:
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

# get important info on downloaded granules (number, short name)
def download_check(download_dir, short_name):
    """
    Prints important information about the granules in the download directory

    @author: Vincent Ribberink

    Parameters
    ----------
    download_dir : String
        string path to the directory containing downloaded ATL08 and GEDI02_A .h5 granules

    Returns
    -------
    icesat_only (bool):
        True if only ATL08 granules are found
    gedi_only (bool):
        True if only GEDI02_A granules are found
    ATL08_granules (list):
        List of ICESat-2 ATL08 granules in download directory
    GEDI02_A_granules (list):
        List of GEDI L2A granules in download directory
    """
    # check existing granules in the download directory
    ATL08_granules = list(Path(download_dir).glob("ATL08*.h5"))
    GEDI02_A_granules = list(Path(download_dir).glob("GEDI02_A*.h5"))
        
    icesat_only = False
    gedi_only = False

    # override with short name if given -> prevents unnecessary converting and filtering
    if short_name == 'ATL08':
        icesat_only = True
        # exit if download dir is empty
        if len(ATL08_granules) == 0:
            raise FileNotFoundError("No granules were found in download directory")

    elif short_name == 'GEDI02_A':
        gedi_only = True
        # exit if download dir is empty
        if len(GEDI02_A_granules) == 0:
            raise FileNotFoundError("No granules were found in download directory")

    else:
        # if 0 granules are found for 1 or more short names
        if len(GEDI02_A_granules) == 0:
            # exit if download directory is empty
            if len(ATL08_granules) == 0:
                raise FileNotFoundError("No granules were found in download directory")
            # otherwise continue with only ATL08
            print(f"{len(ATL08_granules)} ATL08 granules found")
            print("0 GEDI L2A granules found in download directory. No comparison outputs will be created.")
            icesat_only = True

        elif len(ATL08_granules) == 0:
            print(f"{len(GEDI02_A_granules)} GEDI02_A granules found")
            print("0 ICESat-2 ATL08 granules found in download directory. No comparison outputs will be created.")
            gedi_only = True

        # if granules are found for both short names
        else:
            print(f"{len(ATL08_granules)} ATL08 granules found")
            print(f"{len(GEDI02_A_granules)} GEDI02_A granules found")

    return ATL08_granules, GEDI02_A_granules, icesat_only, gedi_only

# filter and extract ICESat-2 canopy height data
def convert_icesat(granules, beam_type, night_only):
    """
    Converts ICESat data from h5 files to Pandas DataFrames
    Extracts lat/long, canopy height and uncertainty
    Filters observations based on strong/weak beams and night flag (see config file)
    Based on Xarray documentation examples, altered for use with Pandas Dataframes

    @authors: Vincent Ribberink, Joshua Salvador

    Parameters
    ----------
    test_files : list
        List containing paths of ICESat-2 ATL08 .h5 granules

    Returns
    -------
    final : Pandas DataFrame
        Contains extracted and filtered observations
    """

    print("---------------------------------")
    print("Started extracting ATL08 data")

    # list of groups containing beam data
    beam_list = ["gt1l", "gt2l", "gt3l", "gt1r", "gt2r", "gt3r"] # groups in h5 file

    # create empty list #1
    df_combined_list = []

    # iterate through h5 files in directory
    for file in granules:
        
        try:
            
            # read file with H5py
            f = h5py.File(file)
        
        except:
            print(f"Skipping corrupted granule {file}")
            continue

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

                # filter out invalid canopy heights (3.4 e38)
                df = df.loc[(df['icesat_canopy'] < 10000) & (df['icesat_canopy_uncertainty'] < 1000)]

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
    Converts GEDI L2A files from h5 to Pandas DataFrames

    @author: Joshua Salvador (lead), Vincent Ribberink

    Parameters
    ----------
    files : list
        List containing paths of GEDI L2A .h5 granules

    Returns
    -------
    final_df : Pandas DataFrame
        Contains extracted and filtered observations
    """

    print("---------------------------------")
    print("Started extracting GEDI02_A data")

    # place all data in here
    all_data = []
    
    # look through each file
    for file in granules:
        #print(f"Processing {file}")

        # skip corrupted granules
        try:
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
        
                        # quality filter if set in config file
                        if quality_flag:
                            df2 = df.loc[df.quality==1]
                        
                        else:
                            df2 = df.copy()
                        
                        all_data.append(df2)
        
        except:
            print(f"Skipping corrupted granule: {file}")
            continue
                    
    # concatenate all data
    final_df = pd.concat(all_data, ignore_index=True)

    print(f"{len(final_df)} filtered observations returned")
    
    # convert to csv for testing purposes
    #final_df.to_csv("gedi.csv", index=False)

    return final_df

# aggregate data by polygons
def aggregate(polygons_path, df, satellite_name, radius):
    """
    Converts GEDI files from h5 to dataframes

    @author: Ethan Gauthier (lead), Vincent Ribberink

    Parameters
    ----------
    polygon_path : string
        Path pointing to input geometry
    df : Pandas DataFrame
        Extracted and filtered observations
    satellite_name : string
        Either "Icesat" or "GEDI"
    radius : int
        radius (m) for the dwithin spatial join

    Returns
    -------
    agg: Pandas DataFrame
        Aggregated Results
    """
    crs = "EPSG:3347" # stat can lambert
    aoi = gpd.read_file(polygons_path).to_crs(crs)

    print("---------------------------------")
    print(f"Starting aggregation for {len(aoi)} polygons")

    #Adding the polygon_id
    aoi = aoi.sort_values('id')
    aoi["polygon_id"] = range(0, len(aoi)) # changed this to start index at 0

    #Assigning polygon ids to Lidar csvs
    def assign_polygon_ids(df, aoi_gdf, radius):

        #Convert Lidar points to GeoDataFrame
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df.longitude, df.latitude),
            crs="EPSG:4326"
        )

        # project points for distance calculations
        gdf.to_crs(aoi_gdf.crs, inplace=True)

        #Spatial join by polygon_id, within a radius
        joined = gpd.sjoin(gdf, aoi_gdf[["polygon_id", "geometry"]], how="inner", predicate="dwithin", distance=radius) 
            # remove dwithin for very large inputs to save processing time 

        print(f"{len(joined)} intersecting observations were found")

        #Drop geometry for clean DataFrame
        return pd.DataFrame(joined.drop(columns="geometry"))
    
    joined = assign_polygon_ids(df, aoi, radius)

    # export for testing
    joined.to_csv(f"{satellite_name}_agg_test.csv")

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

    agg = aggregate_by_polygon(joined, stats, satellite_name)

    print("Aggregation complete")

    return agg
    
# compare
def compare_data(icesat_agg, gedi_agg):
    """
    Compares ICESat canopy data with GEDI canopy data

    @author: Joshua Salvador 

    Parameters
    ----------
    icesat_agg : dataframe
        dataframe containing ICESat-2 ATL08 data
    gedi_agg : dataframe
        dataframe containing ICESat-2 ATL08 data

    Returns
    -------
    df3: dataframe
        all compared results
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

    # Calculate percent difference with mean
    diff = abs(df3["icesat_canopy_mean"] - df3["gedi_canopy_mean"])
    avg = (df3["icesat_canopy_mean"] + df3["gedi_canopy_mean"]) / 2
    df3["percent_diff"] = (diff / avg) * 100 
    
    # Export as CSV for testing purposes
    df3.to_csv("compare3.csv", index=False)

    print("Comparison complete")

    return df3

# format and export for when data for both ICESat-2 ATL08 and GEDI L2A is available
def export(icesat_agg, gedi_agg, compared, config_dict):
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
    config_dict : dictionary
        dictionary of parameters 

    Returns
    -------
    None
    """

    print("---------------------------------")
    print("Starting export")

    # read configurations
    polygons_path = config_dict['PolygonsPath']
    out_dir = config_dict['OutputDir']

    # read output configurations, convert to boolean
    out_csv = (config_dict['OutputCSV'] == 'True')
    out_shp = (config_dict['OutputShapefile'] == 'True')
    out_parquet = (config_dict['OutputParquet'] == 'True')

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
        aoi = gpd.read_file(polygons_path)
        #Adding the polygon_id -> same thing is done in agg() for the spatial join
            # there is probably a better way that avoids doing this twice, but this works
        aoi = aoi.sort_values('id')
        aoi["polygon_id"] = range(0, len(aoi)) # changed this to start index at 0

        # convert to geodataframes
        icesat_agg = pd.merge(icesat_agg, aoi, how="inner", on="polygon_id")
        gedi_agg = pd.merge(gedi_agg, aoi, how="inner", on="polygon_id")
        compared = pd.merge(compared, aoi, how="inner", on="polygon_id")

        ice_agg_gdf = gpd.GeoDataFrame(icesat_agg, geometry=icesat_agg.geometry)
        gedi_agg_gdf = gpd.GeoDataFrame(gedi_agg, geometry=gedi_agg.geometry)
        comp_gdf = gpd.GeoDataFrame(compared, geometry=compared.geometry)

        # TO DO -> rename columns to avoid ambiguity from truncation when exporting as shp

        # export as shp
        ice_agg_gdf.to_file((out_dir + '/icesat_agg.shp')) # columns not renamed, will be truncated
        gedi_agg_gdf.to_file((out_dir + '/gedi_agg.shp'))
        comp_gdf.to_file((out_dir + '/comparison.shp'))

    print("Exporting complete")

# format and export for ICESat-2 only
# there is probably a better way to combine all 3 export functions, but this works
def export_ATL08(icesat_agg, config_dict):
    """
    Format and export the aggregated ICESat-2 ATL08 results as .shp, .csv, and/or .parquet

    @author: Vincent Ribberink

    Parameters
    ----------
    icesat_agg : Pandas DataFrame
        Aggregated ICESat-2 ATL08 data
    config_dict : dictionary
        dictionary of parameters 

    Returns
    -------
    None
    """

    print("---------------------------------")
    print("Starting export")

    # read configurations
    polygons_path = config_dict['PolygonsPath']
    out_dir = config_dict['OutputDir']

    # read output configurations, convert to boolean
    out_csv = (config_dict['OutputCSV'] == 'True')
    out_shp = (config_dict['OutputShapefile'] == 'True')
    out_parquet = (config_dict['OutputParquet'] == 'True')

    # export to csv
    if out_csv:
        icesat_agg.to_csv((out_dir + '/icesat_agg.csv'))

    # export to parquet
    if out_parquet:
        icesat_agg.to_parquet((out_dir + '/icesat_agg.parquet'))

    if out_shp:

        # read geometry
        aoi = gpd.read_file(polygons_path)
        #Adding the polygon_id -> same thing is done in agg() for the spatial join
            # there is probably a better way that avoids doing this twice, but this works
        aoi = aoi.sort_values('id')
        aoi["polygon_id"] = range(0, len(aoi)) # changed this to start index at 0
        geom = aoi.geometry

        # convert to geodataframes
        icesat_agg = pd.merge(icesat_agg, aoi, how="inner", on="polygon_id")
        ice_agg_gdf = gpd.GeoDataFrame(icesat_agg, geometry=icesat_agg.geometry)

        # export as shp
        ice_agg_gdf.to_file((out_dir + '/icesat_agg.shp')) # columns not renamed, will be truncated


    print("Exporting complete")

# format and export for GEDI L2A only
def export_GEDI02_A(gedi_agg, config_dict):
    """
    Format and export the aggregated GEDI L2A results as .shp, .csv, and/or .parquet

    @author: Vincent Ribberink

    Parameters
    ----------
    gedi_agg : Pandas DataFrame
        Aggregated GEDI L2A data
    config_dict : dictionary
        dictionary of parameters 

    Returns
    -------
    None
    """

    print("---------------------------------")
    print("Starting export")

    # read configurations
    polygons_path = config_dict['PolygonsPath']
    out_dir = config_dict['OutputDir']

    # read output configurations, convert to boolean
    out_csv = (config_dict['OutputCSV'] == 'True')
    out_shp = (config_dict['OutputShapefile'] == 'True')
    out_parquet = (config_dict['OutputParquet'] == 'True')

    # export to csv
    if out_csv:
        gedi_agg.to_csv((out_dir + '/gedi_agg.csv'))

    # export to parquet
    if out_parquet:
        gedi_agg.to_parquet((out_dir + '/gedi_agg.parquet'))

    if out_shp:
        # read geometry
        aoi = gpd.read_file(polygons_path)
        #Adding the polygon_id -> same thing is done in agg() for the spatial join
            # there is probably a better way that avoids doing this twice, but this works
        aoi = aoi.sort_values('id')
        aoi["polygon_id"] = range(0, len(aoi)) # changed this to start index at 0
        geom = aoi.geometry

        # convert to geodataframes
        gedi_agg = pd.merge(gedi_agg, aoi, how="inner", on="polygon_id")
        gedi_agg_gdf = gpd.GeoDataFrame(gedi_agg, geometry=gedi_agg.geometry)

        # export as shp
        gedi_agg_gdf.to_file((out_dir + '/gedi_agg.shp')) # columns not renamed, will be truncated

    print("Exporting complete")


def main():

    """
    Run the process_sat_lidar script.
    This does not download the granules from NASA - use earthaccess_download.py
    Input geometries, output directory, and chosen filters are written in the config  file (default: config_process_sat_lidar.txt) 

    @author: Vincent Ribberink

    Returns
    -------
    None.
    """

    #################
    # TESTING SETUP #
    import os
    # change this to the appropriate sample 
    os.chdir("sample_polygons/Alfred_Bog")
    # TESTING SETUP #
    #################


    ### SETUP ###

    # read config
    config_dict = read_config("config_process_sat_lidar.txt")

    # unpack parameters
    polygons_path = config_dict['PolygonsPath']
    download_dir = config_dict['DownloadDir']
    beam_type = config_dict['BeamType']
    night_only = config_dict['NightOnly']
    quality_flag = config_dict['QualityFlag']
    short_name = config_dict['ShortName']

    print("---------------------------------")

    # get info on downloaded granules
    ATL08_granules, GEDI02_A_granules, icesat_only, gedi_only = download_check(download_dir, short_name)


    ### FILTER & CONVERT ###

    if not gedi_only:
        # convert and filter ICESat-2 ATL08 h5 files to pandas dataframes
        icesat_df = convert_icesat(ATL08_granules, beam_type, night_only)
        print("ICESat-2 ATL08 granules complete")
        # aggregate by polygon
        icesat_agg = aggregate(polygons_path, icesat_df, "Icesat", 8) # 8 meter radius circles

    if not icesat_only:
        # convert and GEDI L2A GEDI L2A h5 files to pandas dataframes
        gedi_df = convert_gedi(GEDI02_A_granules, quality_flag)
        print("GEDI L2A granules complete")
        # aggregate by polygon
        gedi_agg = aggregate(polygons_path, gedi_df, "Gedi", 12.5) # 12.5 meter radius circles
 

    ### COMPARE ###

    # if both ATL08 and GEDI02_A are present, run the comparison
    if not (icesat_only | gedi_only):
        compared = compare_data(icesat_agg, gedi_agg)


    ### FORMAT & EXPORT ###

    if icesat_only:
        export_ATL08(icesat_agg, config_dict)
    elif gedi_only:
        export_GEDI02_A(gedi_agg, config_dict)
    else:
        export(icesat_agg, gedi_agg, compared, config_dict)
    
    print("---------------------------------")

if __name__ == "__main__":
    main()
    

        
