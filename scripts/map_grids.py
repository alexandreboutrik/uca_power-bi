import argparse
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import logging
import sys
import re
from pathlib import Path

# Standardized logging implementation matching the ETL interfaces
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

def print_help():
    """Prints the customized, template-compliant help page."""
    help_text = """USAGE:
  python scripts/map_grids.py [OPTIONS]

OPTIONS:
  -i, --input <file>       Filename or path to the source CSV file containing the 'idcar_nat' column.
  -o, --output <file>      [Optional] Output filename or path for the mapped CSV.
  -h, --help               Display this help message and exit.

EXAMPLES:
  Standard Mapping: python scripts/map_grids.py -i carreaux_nivNaturel_met.csv
  Custom Output: python scripts/map_grids.py -i temp1.csv -o mapped_temp1.csv
"""
    print(help_text)

def extract_coordinates(idcar_nat):
    """
    Extracts the North (Y) and East (X) coordinates from the string.
    Example: CRS3035RES1000mN2032000E4250000 -> Y=2032000, X=4250000
    Adds 500 meters to target the exact center point of the 1km x 1km grid.
    """
    match = re.search(r'N(\d+)E(\d+)', str(idcar_nat))
    if match:
        y_north = float(match.group(1))
        x_east = float(match.group(2))
        return x_east + 500, y_north + 500 
    return None, None

def execute_spatial_join(input_path: Path, output_path: Path, geojson_path: Path) -> None:
    """
    Reads the input CSV, extracts grid center coordinates, and performs
    a spatial join against the hardcoded geographic boundaries file.
    """
    if not input_path.exists():
        logging.error(f"Input file not found: {input_path}")
        sys.exit(1)
        
    if not geojson_path.exists():
        logging.error(f"Geographic boundaries file not found: {geojson_path}")
        logging.error("Ensure 'cantons-version-simplifiee.geojson' is located in the data/raw/ directory.")
        sys.exit(1)

    try:
        logging.info("Loading grid dataset (extracting ID column only)...")
        # We only need the ID column to create the mapping table
        df_grids = pd.read_csv(input_path, usecols=['idcar_nat'], low_memory=False)
        
        logging.info(f"Extracting coordinates for {len(df_grids)} grids...")
        coords = df_grids['idcar_nat'].apply(extract_coordinates)
        df_grids['X'] = [c[0] for c in coords]
        df_grids['Y'] = [c[1] for c in coords]
        
        # Drop any invalid or unparseable IDs
        initial_count = len(df_grids)
        df_grids = df_grids.dropna(subset=['X', 'Y'])
        if len(df_grids) < initial_count:
            logging.warning(f"Dropped {initial_count - len(df_grids)} rows with unparseable 'idcar_nat' values.")

        logging.info("Converting grids to spatial points (EPSG:3035)...")
        geometry = [Point(xy) for xy in zip(df_grids['X'], df_grids['Y'])]
        gdf_grids = gpd.GeoDataFrame(df_grids, geometry=geometry, crs="EPSG:3035")

        logging.info("Loading the spatial boundaries map...")
        gdf_boundaries = gpd.read_file(geojson_path)

        logging.info("Aligning map projections to match grid coordinates...")
        gdf_boundaries = gdf_boundaries.to_crs("EPSG:3035")

        logging.info("Performing Spatial Join (pinning grids to cantons)...")
        # Intersects checks which polygon the point falls inside
        mapped_grids = gpd.sjoin(gdf_grids, gdf_boundaries, how="left", predicate="intersects")

        # Standard French Open Data GeoJSONs typically use 'nom' and 'code'
        # Adjust these column names below if your specific GeoJSON uses different keys
        if 'nom' in mapped_grids.columns and 'code' in mapped_grids.columns:
            final_mapping = mapped_grids[['idcar_nat', 'nom', 'code']].copy()
            final_mapping.rename(columns={'nom': 'Canton', 'code': 'Code_INSEE'}, inplace=True)
            # Extract department from the first two characters of the Code_INSEE
            final_mapping['Departement'] = final_mapping['Code_INSEE'].astype(str).str[:2]
        else:
            logging.warning("Standard columns 'nom' and 'code' not found in GeoJSON. Saving all intersecting data.")
            # Drop the geometry and index_right columns to make it a clean CSV
            final_mapping = mapped_grids.drop(columns=['geometry', 'index_right', 'X', 'Y'], errors='ignore')

        logging.info(f"Success! Saving final mapping table to -> {output_path.name}")
        final_mapping.to_csv(output_path, index=False)

    except ValueError as ve:
        logging.error(f"Value Error (Check if 'idcar_nat' column exists in input): {ve}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred during spatial processing: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-i", "--input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("-h", "--help", action="store_true")
    
    args = parser.parse_args()
    
    if len(sys.argv) == 1 or args.help:
        print_help()
        sys.exit(0)

    # Validate basic requirements
    if not args.input:
        print("Error: Missing required argument (-i).\n")
        print_help()
        sys.exit(1)

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    # Hardcoded GeoJSON Path
    geojson_path = project_root / "data" / "raw" / "cantons-version-simplifiee.geojson"
    
    # Input resolution architecture
    input_path = args.input
    if not input_path.exists():
        fallback_extracted = project_root / "data" / "extracted" / input_path.name
        fallback_processed = project_root / "data" / "processed" / input_path.name
        
        if fallback_extracted.exists():
            input_path = fallback_extracted
        elif fallback_processed.exists():
            input_path = fallback_processed
            
    # Output resolution architecture
    output_path = args.output
    if not output_path:
        processed_dir = project_root / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        new_name = f"{input_path.stem}_mapped_to_cantons{input_path.suffix}"
        output_path = processed_dir / new_name
        
    execute_spatial_join(
        input_path=input_path, 
        output_path=output_path, 
        geojson_path=geojson_path
    )

if __name__ == "__main__":
    main()
