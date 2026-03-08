# all code combined

import pandas as pd
import geopandas as gpd
import h5py
import configparser
from pathlib import Path

### read config
def read_config(config_path):
    
    """
    Read and validate parameters from a config file.
    Config file must be written in .ini format, though the file can be .txt

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

    # read in parameters 
    PolygonsPath = config['CONFIG']['PolygonsPath']
    DownloadDir = config['CONFIG']['DownloadDir']
    OutputDir = config['CONFIG']['OutputDir']
    ShortName = config['CONFIG']['ShortName']
    StartDate = config['CONFIG']['StartDate']
    EndDate = config['CONFIG']['EndDate']

    ### validation

    # geometry
    if Path(PolygonsPath).is_file() == False:
        raise FileNotFoundError("input geometry filepath is invalid")

    # download directory
    if Path(DownloadDir).is_dir() == False:
        raise FileNotFoundError("input download directory is invalid or does not exist")
    
    # output directory
    if Path(OutputDir).is_dir() == False:
        raise FileNotFoundError("input download directory is invalid or does not exist")

    # short name -> leave validation to earthaccess

    # date range 
    date_range = (StartDate, EndDate)

    # create config dictionary
    config_dict = {
        'PolygonsPath' : PolygonsPath,
        'DownloadDir' : DownloadDir,
        'OutputDir' : OutputDir,
        'ShortName' : ShortName,
        'DateRange' : date_range
    }

    return config_dict


# filter and extract ICESat-2 vegetation height
def convert_icesat(test_files):
    """
    Converts ICESat data from h5 files to dataframes

    @authors: Vincent Ribberink, Joshua Salvador

    Parameters
    ----------
    test_files : list
        List containing paths of ICESat-2 ATL08 .h5 granules

    Returns
    -------
    None
    """
    # list of groups containing beam data
    beam_list = ["gt1l", "gt1r", "gt2l", "gt2r", "gt3l", "gt3r"] # groups in h5 file
    
    # create empty list #1
    df_combined_list = []
    
    # iterate through h5 files in directory
    for file in test_files:
        # read file with H5py
        f = h5py.File(file)
        
        # create empty list #2
        df_list = []
    
        # iterate through groups to find beam data
        for group in list(f.keys()):
            if group in beam_list:
                
                # create pandas dataframe with canopy height, coordinates
                df = pd.DataFrame({
                        "icesat_canopy" : f[f"{group}/land_segments/canopy/h_canopy"][:],
                        "longitude" : f[f"{group}/land_segments/longitude"][:],
                        "latitude" : f[f"{group}/land_segments/latitude"][:],
                        "beam" : str(group)
                })
                
                # add to list #2
                df_list.append(df)
                
        # concatenate all beams for a given file
        df_combined = pd.concat(df_list)
    
        # add to list #1
        df_combined_list.append(df_combined)

    # concatenate all files
    final = pd.concat(df_combined_list).reset_index()

    # export to csv for testing purposes
    #final.to_csv("icesat.csv")

    return final


# filter and extract GEDI vegetation height
def convert_gedi(files):
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
    # place all data in here
    all_data = []
    
    # look through each file
    for file in files:
        print(f"Processing {file}")
    
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
    
                    canopy_h = rh[:,98]
    
                    df = pd.DataFrame({
                        'file': file,
                        'beam': beam_name,
                        'shot_number': shot,
                        'latitude': lat,
                        'longitude': lon,
                        'elevation': elev,
                        'gedi_canopy': canopy_h
                    })
    
                    all_data.append(df)
                    
    # concatenate all data
    final_df = pd.concat(all_data, ignore_index=True)
    
    # convert to csv for testing purposes
    #final_df.to_csv("gedi.csv", index=False)

    return final_df

#### TO DO -> this function is returning an empty dataframe for ICESat-2 data
# aggregate data by polygons
def aggregate(polygons_path, icesat_df, gedi_df):
    """
    Converts GEDI files from h5 to dataframes

    @author: Ethan Gauthier

    Parameters
    ----------
    polygon_path : string
        Path pointing to input geometry

    Returns
    -------
    None
    """

    aoi = gpd.read_file(polygons_path)

    #Adding the polygon_id
    aoi["polygon_id"] = range(1, len(aoi) + 1)

    #Assigning polygon ids to Lidar csvs
    def assign_polygon_ids(df, aoi_gdf):

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

    icesat_df = assign_polygon_ids(icesat_df, aoi)
    gedi_df = assign_polygon_ids(gedi_df, aoi)

    #
    def aggregate_by_polygon(df, stats, satellite_name):
        #Group by polygon
        grouped = df.groupby("polygon_id")

        #Detect measurement columns
        measurement_cols = [
            col for col in df.columns
            if col in ["icesat_canopy", "gedi_canopy", "elevation"]
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

    icesat_stats = aggregate_by_polygon(icesat_df, stats, "ICESat-2")
    gedi_stats = aggregate_by_polygon(gedi_df, stats, "GEDI")


    # export for testing purposes
    #icesat_stats.to_csv("icesat_agg.csv")
    #gedi_stats.to_csv("icesat_agg.csv")

    return icesat_stats, gedi_stats
    

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
    #df3.to_csv("comparison.csv", index=False)

    return df3


# format and export
def export(icesat_agg, gedi_agg, compared, polygons_path, out_dir):

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
    out_dir : string
        Path pointing to directory where outputs are written

    Returns
    -------
    None
    """

    ## TO DO -> integrate output format(s) parameter from config file

    # fix polygon ID for comparison df
    compared = compared.reset_index()
    compared['polygon_id'] = compared['index'] + 1
    compared.drop(columns=['index'])

    # export to csv
    icesat_agg.to_csv((out_dir + '/icesat_agg.csv'))
    gedi_agg.to_csv((out_dir + '/gedi_agg.csv'))
    compared.to_csv((out_dir + '/comparison.csv'))

    ## TO DO -> export as parquet with pyarrow

    # read geometry
    geom_gdf = gpd.read_file(polygons_path)
    geom = geom_gdf.geometry

    # convert to geodataframes
    ice_agg_gdf = gpd.GeoDataFrame(icesat_agg[:2].reset_index(drop=True), geometry=geom[-2:].reset_index(drop=True))
    gedi_agg_gdf = gpd.GeoDataFrame(gedi_agg[2:], geometry=geom)
    comp_gdf = gpd.GeoDataFrame(compared, geometry=geom)

    # TO DO -> rename columns to avoid ambiguity from truncation when exporting as shp

    # export as shp
    ice_agg_gdf.to_file((out_dir + '/icesat_agg.shp'))
    gedi_agg_gdf.to_file((out_dir + '/gedi_agg.shp'))
    comp_gdf.to_file((out_dir + '/comparison.shp'))



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
  
    ### run appropriate h5 conversions
    # ICESat-2 ATL08
    icesat_files = list(Path(download_dir).glob("ATL08*.h5"))
    icesat_df = convert_icesat(icesat_files)
    print("\nICESat-2 ATL08 granules complete\n")

    # GEDI L2A
    gedi_files = list(Path(download_dir).glob("GEDI02_A*.h5"))
    gedi_df = convert_gedi(gedi_files)
    print("\nGEDI L2A granules complete\n")
 
    # aggregate
    icesat_agg, gedi_agg = aggregate(polygons_path, icesat_df, gedi_df)

    # run comparison
    compared = compare_data(icesat_agg, gedi_agg)

    # format and export
    export(icesat_agg, gedi_agg, compared, polygons_path, output_dir)

if __name__ == "__main__":
    main()
    

        
