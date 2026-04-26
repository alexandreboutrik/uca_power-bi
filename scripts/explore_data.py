import argparse
import pandas as pd
import sys
from pathlib import Path

def print_help():
    """Prints the customized, template-compliant help page."""
    help_text = """USAGE:
  python scripts/explore_data.py [OPTIONS]

OPTIONS:
  -i, --input <file>       Filename or path to the dataset/metadata CSV file.
  -c, --config-dir <dir>   Path to config dir. Defaults to config/ relative to root.
  -s, --separator <sep>    Force a CSV delimiter. If omitted, pandas attempts to guess.
  -l, --list-datasets      List all available CSV datasets and their detailed provenance.
  --show-codes             Display the unique hierarchical modalities (Census format only).
  -h, --help               Display this help message and exit.

EXAMPLES:
  $ python scripts/explore_data.py -i carreaux_nivNaturel_met.csv
  $ python scripts/explore_data.py --list-datasets
"""
    print(help_text)

def list_available_datasets(project_root: Path) -> None:
    """
    Scans the extracted directory, maps files against the dataset registry,
    and outputs a comprehensive, formatted list detailing the lineage of each file.
    """
    extracted_dir = project_root / "data" / "extracted"
    registry_file = project_root / "config" / "datasets_metadata.csv"
    
    if not extracted_dir.exists():
        print(f"Error: The directory {extracted_dir} does not exist.")
        return

    csv_files = list(extracted_dir.glob("*.csv"))
    
    if not csv_files:
        print(f"No CSV datasets found in {extracted_dir.relative_to(project_root)}/")
        return

    # Load the registry into a dictionary for O(1) lookups
    registry = {}
    if registry_file.exists():
        try:
            # fillna ensures empty fields do not crash the script as 'NaN' floats
            df = pd.read_csv(registry_file, dtype=str).fillna("Not provided")
            for _, row in df.iterrows():
                registry[row['filename']] = {
                    'url': row.get('source_url', 'Not provided'),
                    'institution': row.get('institution', 'Not provided'),
                    'description': row.get('description', 'Not provided'),
                    'last_update': row.get('last_update', 'Not provided'),
                    'download_date': row.get('download_date', 'Not provided')
                }
        except Exception as e:
            print(f"Warning: Could not parse registry file at {registry_file}: {e}")

    # Output formatted, hierarchical list
    print(f"\nAvailable datasets in {extracted_dir.relative_to(project_root)}/:")
    print("=" * 85)
    
    for file in sorted(csv_files):
        print(f"  - {file.name}")
        info = registry.get(file.name)
        
        if info:
            print(f"      Institution:   {info['institution']}")
            print(f"      Source URL:    {info['url']}")
            print(f"      Description:   {info['description']}")
            print(f"      Last Update:   {info['last_update']}")
            print(f"      Downloaded On: {info['download_date']}")
        else:
            print("      [Unregistered Dataset - Run extract_data.sh to register provenance]")
        print()
    print("=" * 85)

def load_external_config(config_dir: Path, target_filename: str) -> dict:
    """
    Scans the configuration directory for dictionary files and builds
    a metadata mapping for the target dataset based on filename pattern matching.
    """
    if not config_dir.exists():
        return {}

    mapping = {}
    for config_file in config_dir.glob("*.csv"):
        # Prevent the central lineage registry from being parsed as a column dictionary
        if config_file.name == "datasets_metadata.csv":
            continue
            
        try:
            cfg_df = pd.read_csv(config_file, dtype=str)
            if {"dataset_pattern", "column_name", "description"}.issubset(cfg_df.columns):
                match_mask = cfg_df["dataset_pattern"].apply(lambda x: x in target_filename)
                relevant_cfg = cfg_df[match_mask]
                for _, row in relevant_cfg.iterrows():
                    mapping[row["column_name"]] = row["description"]
        except Exception as e:
            print(f"Warning: Could not parse config file {config_file.name}: {e}")
            
    return mapping

def explore_dataset(file_path: Path, config_dir: Path, show_codes: bool = False, sep: str = None) -> None:
    """
    Determines the dataset schema type (Long vs Wide format) and outputs
    the corresponding metadata dictionary to standard output.
    """
    if not file_path.exists():
        print(f"Error: Target file not found at '{file_path}'")
        sys.exit(1)
        
    try:
        peek_df = pd.read_csv(file_path, sep=sep, engine="python", nrows=5)
        columns = set(peek_df.columns)
        
        print(f"\nMetadata Summary for: {file_path.name}")
        print("=" * 85)

        # Handle self-describing long-format files (e.g., standard INSEE census definitions)
        if {"COD_VAR", "LIB_VAR", "COD_MOD", "LIB_MOD"}.issubset(columns):
            df = pd.read_csv(file_path, sep=sep, dtype=str)
            filtered_df = df[df["COD_VAR"] != "GEO"]
            
            grouped = filtered_df.groupby(["COD_VAR", "LIB_VAR"])
            for (cod_var, lib_var), group in grouped:
                modalities = group[["COD_MOD", "LIB_MOD"]].drop_duplicates().to_dict('records')
                print(f"\n[{cod_var}] : {lib_var} ({len(modalities)} unique codes)")
                
                if show_codes:
                    for i, row in enumerate(modalities):
                        branch = "└──" if i == len(modalities) - 1 else "├──"
                        print(f"   {branch} {row['COD_MOD']:<10} : {row['LIB_MOD']}")

        # Handle wide-format data files relying on external definitions
        else:
            metadata_dict = load_external_config(config_dir, file_path.name)
            if not metadata_dict:
                print(f"Notice: No matching metadata found in '{config_dir}/' for this file pattern.")
                print("Showing raw column names only:\n")
            
            for col in peek_df.columns:
                description = metadata_dict.get(col, "Description missing in config")
                print(f"[{col:<15}] : {description}")
                
        print("\n" + "=" * 85 + "\n")
        
    except Exception as e:
        print(f"An error occurred while parsing the dataset: {e}")
        sys.exit(1)

def main():
    # Disable default argparse behavior to enforce strict templated output
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-i", "--input", type=Path)
    parser.add_argument("-c", "--config-dir", type=Path)
    parser.add_argument("-s", "--separator", type=str)
    parser.add_argument("-l", "--list-datasets", action="store_true")
    parser.add_argument("--show-codes", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    
    args = parser.parse_args()

    # Trigger custom help routing
    if len(sys.argv) == 1 or args.help:
        print_help()
        sys.exit(0)

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Execute dataset listing routine
    if args.list_datasets:
        list_available_datasets(project_root)
        sys.exit(0)

    # Validate logical flow for extraction
    if not args.input:
        print("Error: -i / --input is required unless using -l / --list-datasets.\n")
        print_help()
        sys.exit(1)

    # Dynamic Path Resolution
    config_dir = args.config_dir if args.config_dir else project_root / "config"
    input_path = args.input
    
    # Fallback to absolute project directories if the user passes only a filename
    if not input_path.exists():
        fallback_path = project_root / "data" / "extracted" / input_path.name
        if fallback_path.exists():
            input_path = fallback_path
            
    explore_dataset(
        file_path=input_path, 
        config_dir=config_dir, 
        show_codes=args.show_codes, 
        sep=args.separator
    )

if __name__ == "__main__":
    main()
