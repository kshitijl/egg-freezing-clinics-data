#!python3

import json
import os
import sys
import re
from collections import defaultdict
import colorama

# Initialize colorama for colored terminal output
colorama.init()


def print_error(message):
    """Print error messages in red"""
    print(f"{colorama.Fore.RED}{message}{colorama.Style.RESET_ALL}")


def load_json_file(filepath):
    """Load a JSON file and return its contents"""
    try:
        print(f"Reading file: {filepath}")
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        print_error(f"Error reading {filepath}: {str(e)}")
        return None


def extract_clinic_id(filename):
    """Extract clinic ID from the filename"""
    match = re.search(r"clinic_(\d+)_", filename)
    if match:
        return match.group(1)
    return None


def get_facility_name(data):
    """Extract facility name from the services and profiles data"""
    try:
        if "ClinicInfo" in data and "FacilityName" in data["ClinicInfo"]:
            name = data["ClinicInfo"]["FacilityName"]
            print(f"Found facility name: {name}")
            return name
    except Exception as e:
        print_error(f"Error extracting facility name: {str(e)}")
    return None


def normalize_name(name):
    """Convert name to lowercase and replace spaces with hyphens"""
    if name:
        normalized = name.lower().replace(" ", "-")
        # Remove any special characters
        normalized = re.sub(r"[^a-z0-9-]", "", normalized)
        print(f"Normalized name: {normalized}")
        return normalized
    return None


def consolidate_clinic_data():
    """Main function to consolidate clinic data"""
    downloads_dir = "downloads"
    output_dir = "consolidated-in-one-file"

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        print(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir)

    # Group files by clinic ID
    clinic_files = defaultdict(list)

    try:
        for filename in os.listdir(downloads_dir):
            if filename.endswith(".json"):
                clinic_id = extract_clinic_id(filename)
                if clinic_id:
                    full_path = os.path.join(downloads_dir, filename)
                    clinic_files[clinic_id].append(full_path)

        print(f"Found data for {len(clinic_files)} clinics")
    except Exception as e:
        print_error(f"Error listing files in downloads directory: {str(e)}")
        return

    # Process each clinic
    for clinic_id, files in clinic_files.items():
        print(f"\nProcessing clinic ID: {clinic_id}")

        consolidated_data = {}
        facility_name = None

        # Process each file for this clinic
        for filepath in files:
            filename = os.path.basename(filepath)
            data = load_json_file(filepath)

            if data is None:
                continue

            # Extract facility name from services and profiles data
            if "ServicesAndProfiles" in filename:
                facility_name = get_facility_name(data)

            # Add the data to the consolidated object using the file type as a key
            file_type = re.search(r"_([^_]+)\.json$", filename).group(1)
            consolidated_data[file_type] = data

        if not facility_name:
            print_error(
                f"Could not find facility name for clinic {clinic_id}, using clinic ID as filename"
            )
            output_filename = f"clinic-{clinic_id}.json"
        else:
            output_filename = f"{normalize_name(facility_name)}.json"

        # Save the consolidated data
        output_path = os.path.join(output_dir, output_filename)
        try:
            print(f"Writing consolidated data to: {output_path}")
            with open(output_path, "w", encoding="utf-8") as outfile:
                json.dump(consolidated_data, outfile, indent=2)
            print(
                f"Successfully created consolidated file for {facility_name or clinic_id}"
            )
        except Exception as e:
            print_error(f"Error writing consolidated file: {str(e)}")


if __name__ == "__main__":
    print("Starting clinic data consolidation process...")
    consolidate_clinic_data()
    print("\nConsolidation process complete!")
