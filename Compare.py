# -*- coding: utf-8 -*-
"""
Created on Sat Mar  7 21:52:57 2026

Compare ICESat canopy data with GEDI canopy data

@author: joshs
"""
import os
import pandas as pd
import geopandas as gpd
import h5py
import numpy as np
import glob

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
    
"""
def main():
    os.chdir("C:\\Users\\joshs\\OneDrive\\Desktop\\GEOM4009\\Group project\\")
    
    df = pd.read_csv("aggregated_stats.xls")
    
    compare_data(df)

if __name__ == "__main__":
    main()
"""
