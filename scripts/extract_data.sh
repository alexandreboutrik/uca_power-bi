#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

print_help() {
    cat <<EOF
USAGE:
  ./scripts/extract_data.sh [MODE] [OPTIONS]

MODES:
  run                      Extract all .zip and .7z archives to data/extracted/ and register metadata.

OPTIONS:
  -h, --help               Display this help message and exit.

EXAMPLES:
  $ ./scripts/extract_data.sh run
  $ ./scripts/extract_data.sh -h
EOF
}

if [[ $# -eq 0 ]] || [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    print_help
    exit 0
fi

if [[ "$1" != "run" ]]; then
    echo "Error: Unknown mode '$1'"
    print_help
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RAW_DIR="$PROJECT_ROOT/data/raw"
EXTRACTED_DIR="$PROJECT_ROOT/data/extracted"
TEMP_DIR="$PROJECT_ROOT/data/_temp_workspace"
CONFIG_DIR="$PROJECT_ROOT/config"
METADATA_FILE="$CONFIG_DIR/datasets_metadata.csv"

mkdir -p "$RAW_DIR" "$EXTRACTED_DIR" "$TEMP_DIR" "$CONFIG_DIR"

if [[ ! -f "$METADATA_FILE" ]]; then
    echo '"filename","source_url","institution","description","last_update","download_date"' > "$METADATA_FILE"
fi

echo "Starting data extraction process..."
echo "-----------------------------------"

shopt -s nullglob
for zip_file in "$RAW_DIR"/*.zip; do
    echo "Unzipping: $(basename "$zip_file")"
    unzip -q -o "$zip_file" -d "$TEMP_DIR"
done

for seven_z_file in "$TEMP_DIR"/*.7z; do
    echo "Extracting nested archive: $(basename "$seven_z_file")"
    7z x "$seven_z_file" -o"$TEMP_DIR" -y > /dev/null
    rm "$seven_z_file"
done

echo "Processing and registering extracted CSV files..."

# Standard pipe, but we explicitly redirect keyboard reads from /dev/tty
find "$TEMP_DIR" -type f -name "*.csv" | while read -r csv_path; do
    base_name=$(basename "$csv_path")
    
    if ! grep -q "^\"$base_name\"" "$METADATA_FILE" 2>/dev/null; then
        echo "-----------------------------------"
        echo "New dataset detected: $base_name"
        
        # Explicitly read from the terminal (/dev/tty)
        read -p "Enter the source URL: " user_url < /dev/tty
        read -p "Enter the institution (e.g., INSEE): " user_inst < /dev/tty
        read -p "Enter a brief description: " user_desc < /dev/tty
        read -p "Enter the last update (e.g., YYYY-MM-DD): " user_update < /dev/tty
        
        user_dl_date=$(date +%Y-%m-%d)
        
        # Clean inputs
        user_url=$(echo "$user_url" | sed 's/"/""/g')
        user_inst=$(echo "$user_inst" | sed 's/"/""/g')
        user_desc=$(echo "$user_desc" | sed 's/"/""/g')
        user_update=$(echo "$user_update" | sed 's/"/""/g')
        
        # Save record
        echo "\"$base_name\",\"$user_url\",\"$user_inst\",\"$user_desc\",\"$user_update\",\"$user_dl_date\"" >> "$METADATA_FILE"
        echo "Registered metadata for $base_name."
    fi
    
    mv "$csv_path" "$EXTRACTED_DIR/"
done

echo "Cleaning up temporary workspace..."
rm -rf "$TEMP_DIR"

echo "-----------------------------------"
echo "Extraction complete. Ready for analysis."
