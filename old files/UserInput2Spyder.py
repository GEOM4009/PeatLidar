#Interactive configuration setup
import geopandas as gpd
from zipfile import ZipFile
from datetime import datetime

def load_aoi(polygon_file):
    """
    Loads AOI polygon from KMZ, KML, Shapefile, GeoJSON, or GeoPackage.
    Ensures polygon_id exists.
    """
    #KMZ to extract KML
    if polygon_file.lower().endswith(".kmz"):
        with ZipFile(polygon_file, "r") as z:
            z.extract("doc.kml")
        aoi = gpd.read_file("doc.kml", driver="KML")
    else:
        aoi = gpd.read_file(polygon_file)

    #Assign polygon IDs if missing
    if "polygon_id" not in aoi.columns:
        aoi["polygon_id"] = range(1, len(aoi) + 1)

    return aoi

def get_user_config_interactive():
    print("=== GEOM4009 User Input Module ===")

    #AOI file
    polygon_file = input("Enter AOI polygon filename (e.g., polygon_peat_sample.kmz): ").strip()

    #EarthData login
    username = input("Enter EarthData username: ").strip()
    password = input("Enter EarthData password: ").strip()

    #Satellite choice
    print("\nChoose satellites:")
    print("1 = ICESat-2")
    print("2 = GEDI")
    print("3 = Both")
    sat_choice = input("Enter choice (1/2/3): ").strip()

    satellites = {
        "1": "ICESat-2",
        "2": "GEDI",
        "3": "both"
    }.get(sat_choice, "both")

    #Beam strength choice (ICESat-2 only)
    beam_strength = "both"
    if satellites in ["ICESat-2", "both"]:
        print("\nICESat-2 beam strength:")
        print("1 = strong")
        print("2 = weak")
        print("3 = both")
        beam_choice = input("Enter choice (1/2/3): ").strip()
        beam_strength = {
            "1": "strong",
            "2": "weak",
            "3": "both"
        }.get(beam_choice, "both")

    #Statistics
    print("\nChoose statistics (comma-separated):")
    print("Options: mean, min, max, std, median")
    stats_input = input("Enter stats (default = mean,min,max,std): ").strip()

    if stats_input == "":
        stats = ["mean", "min", "max", "std"]
    else:
        stats = [s.strip() for s in stats_input.split(",")]

    #Product selection
    print("\nUse default products?")
    print("ICESat-2 → ATL08_007")
    print("GEDI → GEDI02_A_002")
    prod_choice = input("Enter Y to use defaults, N to specify custom: ").strip().lower()

    if prod_choice == "n":
        icesat_prod = input("Enter ICESat-2 product (default ATL08_007): ").strip() or "ATL08_007"
        gedi_prod = input("Enter GEDI product (default GEDI02_A_002): ").strip() or "GEDI02_A_002"
    else:
        icesat_prod = "ATL08_007"
        gedi_prod = "GEDI02_A_002"

    products = {
        "ICESat-2": icesat_prod,
        "GEDI": gedi_prod
    }

    #Date range
    print("\nOptional: Enter date range (YYYY-MM-DD to YYYY-MM-DD)")
    date_input = input("Enter date range or press Enter to skip: ").strip()

    date_range = None
    if date_input:
        try:
            start_str, end_str = date_input.split("to")
            start = datetime.fromisoformat(start_str.strip())
            end = datetime.fromisoformat(end_str.strip())
            if start > end:
                raise ValueError("Start date must be before end date.")
            date_range = (start, end)
        except:
            print("Invalid date format. Skipping date range.")

    #Load the AOI
    aoi = load_aoi(polygon_file)

    #Config dictionary
    config = {
        "aoi": aoi,
        "auth": {"username": username, "password": password},
        "satellites": satellites,
        "statistics": stats,
        "beam_strength": beam_strength,
        "products": products,
        "date_range": date_range
    }

    print("\nConfiguration loaded successfully.")
    return config
config = get_user_config_interactive()