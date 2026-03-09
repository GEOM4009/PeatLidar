#Import the polygon zipfile kmz and extract the kml
from zipfile import ZipFile

with ZipFile("polygon_peat_sample.kmz", "r") as z:
    z.extract("doc.kml")
    
    
#Loading the KML with geopandas
import geopandas as gpd

aoi = gpd.read_file("doc.kml", driver="KML")


#Adding the polygon_id
aoi["polygon_id"] = range(1, len(aoi) + 1)


#Assigning polygon ids to Lidar csvs
import pandas as pd

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
icesat_df = pd.read_csv("icesat_sample.csv")
gedi_df = pd.read_csv("GEDI_h5_to_pd.csv")

icesat_df = assign_polygon_ids(icesat_df, aoi)
gedi_df = assign_polygon_ids(gedi_df, aoi)


#Checking for the polygon_id if added
print(icesat_df.columns)
print(gedi_df.columns)


#Aggregate
def aggregate_by_polygon(df, stats, satellite_name):
    #Group by polygon
    grouped = df.groupby("polygon_id")

    #Detect measurement columns
    measurement_cols = [
        col for col in df.columns
        if col in ["h_canopy", "canopy_h", "elevation"]
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


#Combine the stats into one
combined_stats = pd.concat([icesat_stats, gedi_stats], ignore_index=True)


#Convert the combine to csv
combined_stats.to_csv("aggregated_stats.csv", index=False)