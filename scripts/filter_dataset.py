import argparse
import pandas as pd
import logging
import sys
import csv
from pathlib import Path

# Standardized logging implementation for command-line ETL interfaces
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

def print_help():
    """Prints the customized, template-compliant help page."""
    help_text = """USAGE:
  python scripts/filter_dataset.py [OPTIONS]

OPTIONS:
  -i, --input <file>       Filename or path to the source CSV file.
  -c, --column <name>      The exact name of the column to filter on (e.g., tmaille, ind_snv).
  -v, --value <val>        [Exact Match] The value that must be matched to keep the row.
  --min <val>              [Range Match] Minimum numeric value (inclusive).
  --max <val>              [Range Match] Maximum numeric value (inclusive).
  -o, --output <file>      [Optional] Output filename or path.
  -h, --help               Display this help message and exit.

EXAMPLES:
  Exact Match: python scripts/filter_dataset.py -i carreaux_nivNaturel_met.csv -c tmaille -v 1000
  Range Match: python scripts/filter_dataset.py -i carreaux_nivNaturel_met.csv -c ind_snv --min 50000 --max 100000
  Greater Than: python scripts/filter_dataset.py -i carreaux_nivNaturel_met.csv -c ind --min 500
"""
    print(help_text)

def detect_separator(file_path: Path) -> str:
    """Reads the first line of the CSV to auto-detect the delimiter dynamically."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            sniffer = csv.Sniffer()
            return sniffer.sniff(first_line).delimiter
    except Exception:
        logging.warning("Could not auto-detect separator, defaulting to ','.")
        return ','

def execute_filter(input_path: Path, output_path: Path, column: str, value: str = None, min_val: float = None, max_val: float = None, chunk_size: int = 100000) -> None:
    """
    Streams a massive CSV using chunks to maintain a negligible memory footprint.
    Performs block-writes to persist filtered rows natively.
    Supports both string matching and numeric range filtering.
    """
    if not input_path.exists():
        logging.error(f"Input file not found: {input_path}")
        sys.exit(1)

    sep = detect_separator(input_path)
    logging.info(f"Detected separator '{sep}'. Processing dataset...")
    
    if value is not None:
        logging.info(f"Rule: Keep rows where [{column}] == '{value}'")
    else:
        logging.info(f"Rule: Keep rows where [{column}] is between {min_val} and {max_val}")
    
    try:
        # Utilize 'python' engine for safer quoting/parsing across massive chunks
        chunk_iterator = pd.read_csv(input_path, sep=sep, dtype=str, chunksize=chunk_size, engine="python")
        first_chunk = True
        total_rows = 0

        for chunk in chunk_iterator:
            # Terminate execution safely if column is misidentified
            if first_chunk and column not in chunk.columns:
                logging.error(f"Column '{column}' does not exist in this dataset.")
                logging.error(f"Available columns are: {list(chunk.columns)}")
                sys.exit(1)

            # --- FILTERING LOGIC ---
            if value is not None:
                # 1. Exact string match
                filtered_chunk = chunk[chunk[column] == value]
            else:
                # 2. Numeric range match
                # Convert target column to numeric (forces errors/blanks to NaN so it doesn't crash)
                numeric_series = pd.to_numeric(chunk[column], errors='coerce')
                
                # Start with a mask where everything is True
                mask = pd.Series(True, index=chunk.index)
                
                # Apply limits if they were provided
                if min_val is not None:
                    mask = mask & (numeric_series >= min_val)
                if max_val is not None:
                    mask = mask & (numeric_series <= max_val)
                
                filtered_chunk = chunk[mask]

            mode = 'w' if first_chunk else 'a'
            header = first_chunk
            
            # Flush data to disk incrementally
            # We only write if there's data in the filtered chunk, or if it's the very first chunk (to guarantee headers)
            if not filtered_chunk.empty or first_chunk:
                filtered_chunk.to_csv(output_path, index=False, sep=sep, mode=mode, header=header)
            
            total_rows += len(filtered_chunk)
            first_chunk = False

        logging.info(f"Success! Extracted {total_rows} rows into -> {output_path.name}")

    except Exception as e:
        logging.error(f"An unexpected IO error occurred: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-i", "--input", type=Path)
    parser.add_argument("-c", "--column", type=str)
    parser.add_argument("-v", "--value", type=str, default=None)
    parser.add_argument("--min", type=float, default=None)
    parser.add_argument("--max", type=float, default=None)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("-h", "--help", action="store_true")
    
    args = parser.parse_args()
    
    if len(sys.argv) == 1 or args.help:
        print_help()
        sys.exit(0)

    # Validate basic requirements
    if not args.input or not args.column:
        print("Error: Missing required arguments (-i, -c).\n")
        print_help()
        sys.exit(1)

    # Validate logical requirements (Must provide either exact value or a range limit)
    if args.value is None and args.min is None and args.max is None:
        print("Error: You must provide a filtering rule (-v for exact, or --min/--max for range).\n")
        print_help()
        sys.exit(1)

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    # Input resolution architecture (UPDATED)
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
        
        # Build a smart filename based on the filter used
        if args.value is not None:
            rule_str = f"{args.value}"
        else:
            min_str = f"min{args.min}" if args.min is not None else "noMin"
            max_str = f"max{args.max}" if args.max is not None else "noMax"
            rule_str = f"range_{min_str}_{max_str}"
            
        new_name = f"{input_path.stem}_filtered_{args.column}_{rule_str}{input_path.suffix}"
        output_path = processed_dir / new_name
        
    execute_filter(
        input_path=input_path, 
        output_path=output_path, 
        column=args.column, 
        value=args.value,
        min_val=args.min,
        max_val=args.max
    )

if __name__ == "__main__":
    main()
