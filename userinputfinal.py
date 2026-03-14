def write_user_config():
    print("=== User Input Configuration ===")

    #User input prompts
    polygons_path = input("Enter polygon file path (e.g., polygon_peat_sample.kmz): ")
    download_dir = input("Enter download directory name: ")
    output_dir = input("Enter output directory name: ")
    short_name = input("Enter satellite short name (e.g., ATL08, GEDI02_A): ")
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")

    #build the config text
    config_text = f"""[CONFIG]
PolygonsPath = {polygons_path}
DownloadDir = {download_dir}
OutputDir = {output_dir}
ShortName = {short_name}
StartDate = {start_date}
EndDate = {end_date}
"""

    #write user input to a text file
    with open("config_process_sat_lidar.txt", "w") as f:
        f.write(config_text)

    print("\nConfiguration saved to config_process_sat_lidar.txt")
    print("Done.")

#run the script
write_user_config()
