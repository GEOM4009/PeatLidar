##### user_input3.py #####
# Developed as part of the PeatLidar final project for GEOM 4009

# Author: Ethan Gauthier

# Takes a user input to create a config file 
def write_user_config():
    print("=== User Input Configuration ===")

    #User Inputs
    polygons_path = input("Enter polygon file path (e.g., polygon_peat_sample.kmz): ")
    download_dir = input("Enter download directory name: ")
    short_name = input("Enter product short name (ATL08, GEDI02_A, both): ")
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")

    #ATL08 Section
    beam_type = input("Beam type (strong, weak, all): ")
    night_only = input("Night only? (True/False): ")

    #GEDI Section
    gedi_quality = input("Use only high-quality GEDI shots? (True/False): ")

    #Output Section
    output_dir = input("Enter output directory name: ")
    out_csv = input("Export CSV? (True/False): ")
    out_parquet = input("Export Parquet? (True/False): ")
    out_shp = input("Export Shapefile? (True/False): ")

    #Build Config Txt
    config_text = f"""[INPUT]
;Path to the input polygon(s) geometry file (common geospatial formats)
PolygonsPath = {polygons_path}

;Path to the directory where data granules will be downloaded
DownloadDir = {download_dir}

;Short name of the Earthdata product to download (ATL08, GEDI02_A, both)
ShortName = {short_name}

;Date range for the earthdata query
StartDate = {start_date}
EndDate = {end_date}


[ATL08]

;Beam type filter (strong, weak, all)
BeamType = {beam_type}

;Night flag filter
NightOnly = {night_only}


[GEDI02_A]
QualityFlag = {gedi_quality}


[OUTPUT]

;Path to the directory where aggregated files will be written
OutputDir = {output_dir}

;Output file format options
OutputCSV = {out_csv}
OutputParquet = {out_parquet}
OutputShapefile = {out_shp}
"""

    #Write to text file
    with open("config_process_sat_lidar.txt", "w") as f:
        f.write(config_text)

    print("\nConfiguration saved to config_process_sat_lidar.txt")
    print("Done.")

#Run the script
write_user_config()
