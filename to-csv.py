#!python3

import os
import json
import csv
import re
from typing import Any, Dict, List, Optional


def extract_nested_field(data: Dict[str, Any], path: str) -> Any:
    """Extract a value from a nested dictionary using a dot-notation path."""
    parts = path.split(".")
    current = data
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def extract_array_field(data: List[List[Any]], key_name: str) -> Optional[Any]:
    """Extract a value from an array of key-value pairs."""
    if not isinstance(data, list):
        return None

    for item in data:
        if isinstance(item, list) and len(item) >= 2 and item[0] == key_name:
            return item[1]
    return None


def extract_table_field(
    data: Dict[str, Any], table_path: str, row_name: str, age_group: str
) -> Optional[Any]:
    """Extract a value from a table structure based on row name and age group."""
    table = extract_nested_field(data, table_path)
    if not table or "DataRows" not in table or "RowHeaders" not in table:
        return None

    # Find the row with the matching row name
    row_index = -1
    for i, row in enumerate(table["DataRows"]):
        if len(row) > 0 and row[0] == row_name:
            row_index = i
            break

    if row_index == -1:
        return None

    # Find the column index for the age group
    col_index = -1
    if isinstance(table["RowHeaders"], list):
        try:
            col_index = table["RowHeaders"].index(age_group)
        except ValueError:
            # Try looking for age group in first row if RowHeaders doesn't contain it
            pass

    # If not found in RowHeaders, check if it's a list of strings (new structure)
    if col_index == -1 and len(table["DataRows"]) > 0:
        headers = table["RowHeaders"]
        try:
            col_index = headers.index(age_group)
        except (ValueError, TypeError):
            # Age group not found
            return None

    # Get the value at the intersection of row and column
    if col_index != -1 and row_index != -1:
        row_data = table["DataRows"][row_index]
        if len(row_data) > col_index:
            return row_data[col_index]

    return None


def extract_summary_table_field(
    data: Dict[str, Any], table_path: str, row_name: str, age_group: str
) -> Optional[Any]:
    """Extract a value from the Summary table structure based on row name and age group."""
    table = extract_nested_field(data, table_path)
    if not table or "DataRows" not in table or "RowHeaders" not in table:
        return None

    # Find the row with the matching row name
    row_index = -1
    for i, row in enumerate(table["DataRows"]):
        if len(row) > 0 and row[0] == row_name:
            row_index = i
            break

    if row_index == -1:
        return None

    # Get the age group column index
    # For Summary section, RowHeaders typically has age groups as items
    age_group_index = -1
    row_headers = table["RowHeaders"]

    if isinstance(row_headers, list):
        try:
            age_group_index = row_headers.index(age_group)
        except ValueError:
            # Age group not found in list
            pass

    # If age group not found and row_headers is a string, we need a different approach
    if age_group_index == -1:
        # Hardcoded age group indices based on the structure observed
        age_group_mapping = {"<35": 1, "35-37": 2, "38-40": 3, ">40": 4}
        age_group_index = age_group_mapping.get(age_group, -1)

    # Get the value at the intersection
    if age_group_index != -1 and row_index != -1:
        row_data = table["DataRows"][row_index]
        if len(row_data) > age_group_index:
            return row_data[age_group_index]

    return None


def extract_question_data(
    data: Dict[str, Any], data_path: str, question_id: str
) -> Optional[Dict[str, Any]]:
    """Extract question data for a specific question ID."""
    questions_data = extract_nested_field(data, data_path)
    if not questions_data:
        return None

    for question_data in questions_data:
        if question_data.get("QuestionId") == question_id:
            return question_data
    return None


def extract_question_value_by_age(
    data: Dict[str, Any], data_path: str, question_id: str, age_group: str = "<35"
) -> Optional[Any]:
    """Extract the value for a specific question ID and age group."""
    question_data = extract_question_data(data, data_path, question_id)
    if not question_data or "DataRows" not in question_data:
        return None

    # Find the age group index in row headers
    row_headers = question_data.get("RowHeaders", [])
    if not row_headers:
        return None

    try:
        age_index = row_headers.index(age_group)
    except ValueError:
        # Age group not found in headers
        return None

    # Get the value from the first data row at the age group index
    if question_data["DataRows"] and len(question_data["DataRows"]) > 0:
        data_row = question_data["DataRows"][0]
        if len(data_row) > age_index:
            return data_row[age_index]

    return None


def extract_field(data: Dict[str, Any], field_selector: Dict[str, Any]) -> Any:
    """Extract a field using various selector types."""
    selector_type = field_selector["type"]

    if selector_type == "nested":
        return extract_nested_field(data, field_selector["path"])

    elif selector_type == "array":
        array_data = extract_nested_field(data, field_selector["array_path"])
        if array_data:
            return extract_array_field(array_data, field_selector["key"])

    elif selector_type == "table":
        return extract_table_field(
            data,
            field_selector["table_path"],
            field_selector["row_name"],
            field_selector.get("age_group", "<35"),
        )

    elif selector_type == "summary_table":
        return extract_summary_table_field(
            data,
            field_selector["table_path"],
            field_selector["row_name"],
            field_selector.get("age_group", "<35"),
        )

    elif selector_type == "question":
        return extract_question_value_by_age(
            data,
            field_selector["data_path"],
            field_selector["question_id"],
            field_selector.get("age_group", "<35"),
        )

    return None


def process_json_files(
    input_dir: str, output_csv: str, field_selectors: Dict[str, Dict[str, Any]]
) -> None:
    """Process all JSON files and output to a single CSV."""
    # Ensure the input directory exists
    if not os.path.isdir(input_dir):
        print(f"Error: Directory '{input_dir}' not found.")
        return

    # Prepare CSV headers
    headers = ["filename"] + list(field_selectors.keys())

    # Process files
    rows = []
    for filename in os.listdir(input_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(input_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Extract fields
                row = {"filename": filename}
                for field_name, selector in field_selectors.items():
                    row[field_name] = extract_field(data, selector)

                rows.append(row)
                print(f"Processed: {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

    # Write to CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully wrote {len(rows)} rows to {output_csv}")


def main():
    # Define input and output paths
    input_directory = "consolidated-in-one-file"
    output_csv_file = "fertility_centers_data.csv"

    # Define field selectors
    field_selectors = {
        # Clinic information fields
        "facility_name": {
            "type": "nested",
            "path": "ServicesAndProfiles.ClinicInfo.FacilityName",
        },
        "address": {"type": "nested", "path": "ServicesAndProfiles.ClinicInfo.Address"},
        "city": {"type": "nested", "path": "ServicesAndProfiles.ClinicInfo.City"},
        "state": {"type": "nested", "path": "ServicesAndProfiles.ClinicInfo.StateDesc"},
        "zipcode": {"type": "nested", "path": "ServicesAndProfiles.ClinicInfo.ZipCode"},
        # Service fields - using array extraction
        "egg_cryopreservation": {
            "type": "array",
            "array_path": "ServicesAndProfiles.Services",
            "key": "Egg cryopreservation services",
        },
        "embryo_cryopreservation": {
            "type": "array",
            "array_path": "ServicesAndProfiles.Services",
            "key": "Embryo cryopreservation services",
        },
        # Profile fields
        "total_cycles": {
            "type": "array",
            "array_path": "ServicesAndProfiles.Profile",
            "key": "Total cycles",
        },
        "fertility_preservation_cycles": {
            "type": "array",
            "array_path": "ServicesAndProfiles.Profile",
            "key": "Fertility preservation cycles",
        },
        "pregnancies": {
            "type": "array",
            "array_path": "ServicesAndProfiles.Profile",
            "key": "Pregnancies",
        },
        "deliveries": {
            "type": "array",
            "array_path": "ServicesAndProfiles.Profile",
            "key": "Deliveries",
        },
        "total_infants_born": {
            "type": "array",
            "array_path": "ServicesAndProfiles.Profile",
            "key": "Total infants born",
        },
        # Patient and Cycle Questions - extracting <35 age group data
        "patients_under_35": {
            "type": "question",
            "data_path": "PatientAndCycle.Data",
            "question_id": "Q001",
            "age_group": "<35",
        },
        "own_eggs_and_embryos_under35": {
            "type": "question",
            "data_path": "PatientAndCycle.Data",
            "question_id": "Q003",
            "age_group": "<35",
        },
        "retrievals_discontinued_without_any_eggs_under35": {
            "type": "question",
            "data_path": "PatientAndCycle.Data",
            "question_id": "Q005",
            "age_group": "<35",
        },
        "percent_used_for_fertility_preservation_under35": {
            "type": "question",
            "data_path": "PatientAndCycle.Data",
            "question_id": "Q006",
            "age_group": "<35",
        },
        "discontinued_after_retrieval_before_transfer_or_banking_under35": {
            "type": "question",
            "data_path": "PatientAndCycle.Data",
            "question_id": "Q101",
            "age_group": "<35",
        },
        "discontinued_before_transfer_or_banking_under35": {
            "type": "question",
            "data_path": "PatientAndCycle.Data",
            "question_id": "Q102",
            "age_group": "<35",
        },
        "percent_transfers_using_frozen_embryos_under35": {
            "type": "question",
            "data_path": "PatientAndCycle.Data",
            "question_id": "Q008",
            "age_group": "<35",
        },
        "percent_transfers_using_single_embryo_under35": {
            "type": "question",
            "data_path": "PatientAndCycle.Data",
            "question_id": "Q110",
            "age_group": "<35",
        },
        "average_number_of_embryos_transerred_under35": {
            "type": "question",
            "data_path": "PatientAndCycle.Data",
            "question_id": "Q210",
            "age_group": "<35",
        },
        # Summary table fields - newly added
        "intended_retrievals_under35": {
            "type": "summary_table",
            "table_path": "Summary.Table1",
            "row_name": "Number of intended retrievals",
            "age_group": "<35",
        },
        "intended_retrievals_live_birth_under35": {
            "type": "summary_table",
            "table_path": "Summary.Table1",
            "row_name": "Percentage of intended retrievals resulting in live-birth deliveries",
            "age_group": "<35",
        },
        "intended_retrievals_singleton_live_birth_under35": {
            "type": "summary_table",
            "table_path": "Summary.Table1",
            "row_name": "Percentage of intended retrievals resulting in singleton live-birth deliveries",
            "age_group": "<35",
        },
        "actual_retrievals_under35": {
            "type": "summary_table",
            "table_path": "Summary.Table1",
            "row_name": "Number of actual retrievals",
            "age_group": "<35",
        },
        "actual_retrievals_live_birth_under35": {
            "type": "summary_table",
            "table_path": "Summary.Table1",
            "row_name": "Percentage of actual retrievals resulting in live-birth deliveries",
            "age_group": "<35",
        },
        "average_intended_retrievals_per_live_birth_under35": {
            "type": "summary_table",
            "table_path": "Summary.Table1",
            "row_name": "Average number of intended retrievals per live-birth delivery",
            "age_group": "<35",
        },
        "transfers_under35": {
            "type": "summary_table",
            "table_path": "Summary.Table1",
            "row_name": "Number of transfers",
            "age_group": "<35",
        },
        "transfers_35_37": {
            "type": "summary_table",
            "table_path": "Summary.Table1",
            "row_name": "Number of transfers",
            "age_group": "35-37",
        },
        "transfers_38_40": {
            "type": "summary_table",
            "table_path": "Summary.Table1",
            "row_name": "Number of transfers",
            "age_group": "38-40",
        },
        "transfers_40plus": {
            "type": "summary_table",
            "table_path": "Summary.Table1",
            "row_name": "Number of transfers",
            "age_group": ">40",
        },
        "percent_transfers_resulting_in_live_birth_under35": {
            "type": "summary_table",
            "table_path": "Summary.Table1",
            "row_name": "Percentage of transfers resulting in live-birth deliveries",
            "age_group": "<35",
        },
        "percent_transfers_resulting_in_live_birth_35_37": {
            "type": "summary_table",
            "table_path": "Summary.Table1",
            "row_name": "Percentage of transfers resulting in live-birth deliveries",
            "age_group": "35-37",
        },
        "percent_transfers_resulting_in_live_birth_38_40": {
            "type": "summary_table",
            "table_path": "Summary.Table1",
            "row_name": "Percentage of transfers resulting in live-birth deliveries",
            "age_group": "38-40",
        },
        "percent_transfers_resulting_in_live_birth_40plus": {
            "type": "summary_table",
            "table_path": "Summary.Table1",
            "row_name": "Percentage of transfers resulting in live-birth deliveries",
            "age_group": ">40",
        },
    }

    # Process the files
    process_json_files(input_directory, output_csv_file, field_selectors)


if __name__ == "__main__":
    main()
