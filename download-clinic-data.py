#!python3

import os
import requests
import time
from urllib.parse import urlparse, unquote
import json


def download_clinic_data(clinic_ids):
    # Create downloads directory if it doesn't exist
    download_dir = "downloads"
    if not os.path.exists(download_dir):
        print(f"Creating downloads dir: {download_dir}")
        os.makedirs(download_dir)

    # URL templates with placeholder for clinic ID
    url_templates = [
        "https://art.cdc.gov/api/ServicesAndProfiles/years/0/clinics/{clinic_id}/useArtDashboardSP/true",
        "https://art.cdc.gov/api/PatientAndCycle/years/0/clinics/{clinic_id}/useArtDashboardSP/true/nationalData/false",
        "https://art.cdc.gov/api/SuccessRateOwnEggs/years/0/clinics/{clinic_id}/useArtDashboardSP/true/nationalData/false",
        "https://art.cdc.gov/api/Summary/years/0/clinics/{clinic_id}/useArtDashboardSP/true",
    ]

    # Not including this header leads to a 503 error
    headers = {"x-database-type": "art"}

    for clinic_id in clinic_ids:
        print(f"Processing clinic ID: {clinic_id}")

        for url_template in url_templates:
            # Replace placeholder with actual clinic ID
            url = url_template.format(clinic_id=clinic_id)

            # Extract the endpoint name from the URL (e.g., "ServicesAndProfiles")
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.split("/")
            endpoint = path_parts[2]  # The API endpoint is at position 2 in the path

            # Create filename
            filename = f"{download_dir}/clinic_{clinic_id}_{endpoint}.json"

            # Check if file already exists
            if os.path.exists(filename):
                print(f"  - File already exists: {filename}")
                continue

            try:
                # Make the request
                print(f"  - Downloading: {url}")
                response = requests.get(url, headers=headers)

                # Check if request was successful
                if response.status_code == 200:
                    # Save the JSON response to file
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(response.json(), f, indent=2)
                    print(f"  - Successfully saved to {filename}")
                else:
                    print(f"  - Failed to download: HTTP {response.status_code}")

                # Add a small delay to be respectful to the server
                time.sleep(1)

            except Exception as e:
                print(f"  - Error downloading {url}: {str(e)}")

    print("Download process completed.")


if __name__ == "__main__":
    # List of clinic IDs
    clinic_ids = [
        "25",
        "31",
        "46",
        "47",
        "54",
        "64",
        "73",
        "75",
        "78",
        "81",
        "92",
        "106",
        "113",
        "126",
        "130",
        "133",
        "147",
        "181",
        "204",
        "227",
        "239",
        "264",
        "266",
        "271",
        "273",
        "293",
        "306",
        "313",
        "315",
        "319",
        "337",
        "381",
        "412",
        "416",
        "421",
        "437",
        "441",
        "463",
        "607",
        "617",
        "619",
        "625",
        "627",
        "708",
        "802",
        "805",
        "814",
        "819",
        "822",
        "824",
        "828",
        "835",
        "836",
        "838",
        "868",
        "873",
        "877",
        "880",
        "886",
    ]

    # Run the download function
    download_clinic_data(clinic_ids)
