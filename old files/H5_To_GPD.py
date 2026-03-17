# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 22:20:56 2026

Convert ICESat and GEDI data from h5 to pandas dataframes

@author: joshs
"""

import os
import pandas as pd
import geopandas as gpd
import h5py
import numpy as np
import glob

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
    final.to_csv("icesat_sample.csv")


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
    final_df.to_csv("GEDI_h5_to_pd.csv", index=False)

"""
def main():
    os.chdir("C:\\Users\\joshs\\OneDrive\\Desktop\\GEOM4009\\Group project")
    
    gedi_files = glob.glob("GEDI02_A_002-20260210_184841\\*.h5") # get each h5 file
    
    # import icesat-2 data
    icesat_files = glob.glob("ATL08_007-20260210_184835/*.h5")

    convert_gedi(gedi_files)
    convert_icesat(icesat_files)

if __name__ == "__main__":
    main()
"""