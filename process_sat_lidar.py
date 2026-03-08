# all code combined

import pandas as pd
import geopandas as gpd
import h5py
import configparser
from pathlib import Path

### read config
def read_config(config_path):
    
    # initialize config parser
    config = configparser.ConfigParser()

    # read config file
    config.read(config_path)

    # read in parameters -> probably a better way to do this with a dictionary, but this works for now
    polygons_path = config['CONFIG']['PolygonsPath']
    download_dir = config['CONFIG']['DownloadDir']
    output_dir = config['CONFIG']['OutputDir']
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

    return polygons_path, download_dir, output_dir, short_name, date_range


# filter and extract ICESat-2 vegetation height
def convert_icesat(test_files):
    """
    Converts ICESat data from h5 files to dataframes

    Parameters
    ----------
    test_files : h5
        ICESat data

    Returns
    -------
    None.
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

    # export
    #final.to_csv("icesat_sample.csv")

    return final


# filter and extract GEDI vegetation height
def convert_gedi(files):
    """
    Converts GEDI files from h5 to dataframes

    Parameters
    ----------
    files : h5
        GEDI data

    Returns
    -------
    None.
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
    
    # convert to csv
    #final_df.to_csv("GEDI_h5_to_pd.csv", index=False)

    return final_df


# compare
def compare_data(df):
    """
    Compares ICESat canopy data with GEDI canopy data

    Parameters
    ----------
    df : dataframe
        dataframe containing both ICESat and GEDI data

    Returns
    -------
    None.
    """
    # Merge duplicated polygon IDs
    df2 = df.groupby("polygon_id").first().reset_index()
    
    # Make sure both icesat and gedi contains data
    df3 = df2.dropna(subset=["icesat_canopy_mean", "gedi_canopy_mean"]).copy()
    
    # Calculate difference for icesat canopy height mean, max, min, std with gedi.
    df3["mean_diff"] = df3["icesat_canopy_mean"] - df3["gedi_canopy_mean"]
    df3["max_diff"]= df3["icesat_canopy_max"] - df3["gedi_canopy_max"]
    df3["min_diff"] = df3["icesat_canopy_min"] - df3["gedi_canopy_min"]
    df3["std_diff"] = df3["icesat_canopy_std"] - df3["gedi_canopy_std"]
    
    # Export as CSV
    df3.to_csv("comparison.csv", index=False)

    return df3


# format and export
def export(icesat_agg, gedi_agg, compared, polygons_path, out_dir):

    geom_gdf = gpd.read_file(polygons_path)
    geom = geom_gdf.geometry

    ice_agg_gdf = gpd.GeoDataFrame(icesat_agg[:2].reset_index(drop=True), geometry=geom[-2:].reset_index(drop=True))
    gedi_agg_gdf = gpd.GeoDataFrame(gedi_agg[2:], geometry=geom)
    comp_gdf = gpd.GeoDataFrame(compared, geometry=geom)

    ice_agg_gdf = ice_agg_gdf[['polygon_id', 'h_canopy_mean', 'h_canopy_min', 'h_canopy_max', 'h_canopy_std', 'satellite', 'geometry']]
    gedi_agg_gdf.drop(columns=['h_canopy_mean', 'h_canopy_min', 'h_canopy_max', 'h_canopy_std'], inplace=True)

    comp_gdf = comp_gdf.reset_index()
    comp_gdf['polygon_id'] = comp_gdf['index'] + 1
    comp_gdf.drop(columns=['index'])

    ice_agg_gdf.rename(columns={'h_canopy_mean':'h_can_mean', 'h_canopy_min':'h_can_min', 'h_canopy_max':'h_can_max', 'h_canopy_std':'h_can_std'}, inplace=True)
    gedi_agg_gdf.rename(columns={'elevation_mean':'elev_mean', 'elevation_min':'elev_min', 'elevation_max':'elev_max', 'elevation_std':'elev_std',
                                'canopy_h_mean':'can_h_mean', 'canopy_h_min':'can_h_min', 'canopy_h_max':'can_h_max', 'canopy_h_std':'can_h_std',}, inplace=True)

    ice_agg_gdf.to_file((out_dir + '/icesat_agg.shp'))
    gedi_agg_gdf.to_file((out_dir + '/gedi_agg.shp'))
    comp_gdf.to_file((out_dir + '/comparison.shp'))

    ice_agg_gdf.drop(columns=['geometry'], inplace=True)
    gedi_agg_gdf.drop(columns=['geometry'], inplace=True)
    comp_gdf.drop(columns=['geometry'], inplace=True)

    ice_agg_gdf.to_csv((out_dir + '/icesat_agg.csv'))
    gedi_agg_gdf.to_csv((out_dir + '/gedi_agg.csv'))
    comp_gdf.to_csv((out_dir + '/comparison.csv'))



def main():

    # read config
    polygons_path, download_dir, output_dir, short_name, date_range = read_config("config_earthaccess.txt")

    # run appropriate h5 conversions
    icesat_files = list(Path(download_dir).glob("ATL08*.h5"))
    icesat_result = convert_icesat(icesat_files)
    print("\nICESat-2 ATL08 granules complete")

    gedi_files = list(Path(download_dir).glob("GEDI02_A*.h5"))
    gedi_result = convert_gedi(gedi_files)
    print("\nGEDI L2A granules complete")

    # run comparison
    combined = pd.concat([icesat_result, gedi_result])
    compared = compare_data(combined)

    # format and export
    export(icesat_result, gedi_result, compared, polygons_path, output_dir)

if __name__ == "__main__":
    main()
    

        
