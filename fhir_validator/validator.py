import os
import json
import argparse
from typing import Any, Dict, Tuple
import fastjsonschema
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Path to the default consolidated FHIR schema
CONSOLIDATED_SCHEMA_PATH = "schemas/r4/fhir.schema.json"

# Content Structure Types
CONTENT_STRUCTURE_UNSPECIFIED = "CONTENT_STRUCTURE_UNSPECIFIED"
BUNDLE = "BUNDLE"
RESOURCE = "RESOURCE"
BUNDLE_PRETTY = "BUNDLE_PRETTY"
RESOURCE_PRETTY = "RESOURCE_PRETTY"


def load_consolidated_fhir_schema(schema_path :str =CONSOLIDATED_SCHEMA_PATH) -> Dict:
    """
    Load the consolidated FHIR schema from the specified file path.

    Args:
        schema_path (str): The path to the consolidated FHIR schema file. Defaults to CONSOLIDATED_SCHEMA_PATH. Must be a json schema file

    Returns:
        dict: The loaded FHIR schema as a dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist at the specified path.
    """
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as schema_file:
            return json.load(schema_file)
    else:
        raise FileNotFoundError(f"Consolidated FHIR schema not found at {schema_path}")


def compile_fhir_schema(schema :dict) -> Any:
    """
    Compile the FHIR schema using fastjsonschema.
    Args:
        schema (dict): The FHIR schema to compile.
    Returns:
        Any: The compiled schema.
    Raises:
        ValueError: If the schema compilation fails.
    """
    
    try:
        return fastjsonschema.compile(schema)
    except fastjsonschema.JsonSchemaException as e:
        raise ValueError(f"Failed to compile schema: {e}")


def validate_fhir_resource(resource, compiled_validator: Any) -> Tuple[bool, str]:
    """
    Validate a FHIR resource using the compiled validator.

    Args:
        resource: The FHIR resource to be validated.
        compiled_validator (Any): The compiled JSON schema validator.

    Returns:
        Tuple[bool, str]: A tuple where the first element is a boolean indicating 
                            whether the validation was successful, and the second 
                            element is a string containing the error message if 
                            validation failed, or None if validation was successful.
    """
    
    try:
        compiled_validator(resource)
        return True, None
    except fastjsonschema.JsonSchemaException as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def split_bundle(bundle, chunk_size=100):
    """Split a FHIR bundle into smaller chunks."""
    entries = bundle.get('entry', [])
    for i in range(0, len(entries), chunk_size):
        chunk = entries[i:i + chunk_size]
        yield {'resourceType': 'Bundle', 'entry': chunk}


def validate_fhir_bundle_in_chunks(bundle : dict, compiled_validator: Any, chunk_size=100) -> bool:
    """
    Validate a FHIR bundle in chunks to avoid long validation times.

    Args:
        bundle (dict): The FHIR bundle to be validated.
        compiled_validator (object): The compiled validator to use for validation.
        chunk_size (int, optional): The size of each chunk to split the bundle into. Defaults to 100.

    Returns:
        bool: True if all chunks are valid, False if any chunk is invalid.
    """
    idx = 0
    for chunk in split_bundle(bundle, chunk_size):
        is_valid = validate_fhir_bundle(chunk, compiled_validator)
        logging.debug(f"\t Validating chunk {idx} as {is_valid}...")
        if not is_valid:
            return False
        idx += 1
    return True


def validate_fhir_bundle(bundle, compiled_validator) -> bool:
    """
    Validates each resource in the given FHIR bundle.
    Args:
        bundle (dict): The FHIR bundle to be validated. It should be a dictionary 
                        with a 'resourceType' key set to 'Bundle' and an 'entry' key 
                        containing a list of resources.
        compiled_validator (object): The compiled validator object used to validate 
                                        each resource in the bundle.
    Returns:
        bool: True if all resources in the bundle are valid, False if any resource 
                fails validation.
    Raises:
        ValueError: If the input bundle does not have 'resourceType' set to 'Bundle'.
    """
    
    if bundle.get('resourceType') != 'Bundle':
        raise ValueError("Input is not a valid FHIR Bundle")
    
    for entry in bundle.get("entry", []):
        resource = entry.get("resource")
        if resource:
            is_valid, error_message = validate_fhir_resource(resource, compiled_validator)
            if not is_valid:
                logging.error(f"Validation failed for {resource.get('resourceType', 'Unknown')}: {error_message}")
                return False
    return True

def is_ndjson(file_path):
    try:
        with open(file_path, 'r') as f:
            idx = 0
            for line in f:
                if line.strip() not in [",", ""]:
                    json.loads(line)  # Try to parse each line as JSON
                    idx += 1
                    
                    # If more than one line can be parsed as JSON, it's likely NDJSON
                    # Return early to avoid reading the entire file
                    if idx > 1:
                        return True
        return True
    except json.JSONDecodeError:
        return False
    
def is_bundle_or_resource(json_obj: json) -> str:
    """Check if the JSON object is a FHIR Bundle or Resource."""
    
    if 'resourceType' in json_obj:
        if json_obj['resourceType'] == 'Bundle' :
            return BUNDLE 
        else :
            return RESOURCE
    return CONTENT_STRUCTURE_UNSPECIFIED


def identify_content_structure(file_path) -> str:
    """
    Identify the content structure of the input file.
    This function determines whether the provided file is a FHIR Bundle or Resource.
    It first checks if the file is in NDJSON format and processes the first line to 
    identify the structure. If the file is not NDJSON, it reads the entire file as 
    JSON and identifies the structure.
    Args:
        file_path (str): The path to the file to be checked.
    Returns:
        str: A string indicating whether the file is a 'BUNDLE_PRETTY' or 'RESOURCE_PRETTY'.
    Raises:
        ValueError: If the NDJSON file is invalid.
    """
    
    
    # Granted this is not the most efficient way to check for a FHIR Bundle or Resource
    # But it's readable and easy to understand
        
    if is_ndjson(file_path):
        with (open(file_path, 'r')) as f:
            first_line = f.readline().strip()
            try:
                first_json = json.loads(first_line)
                return is_bundle_or_resource(first_json)
            except json.JSONDecodeError:
                raise ValueError("Invalid NDJSON file")
    
    with open(file_path, 'r') as f:
        json_obj = json.load(f)
        if is_bundle_or_resource(json_obj) == BUNDLE:
            return BUNDLE_PRETTY
        else:
            return RESOURCE_PRETTY
            


def batch_validate_fhir_bundles(bundle_files, chunk_size=100):
    """
    Batch validate FHIR bundle files using the compiled validator in chunks.
    Args:
        bundle_files (list of str): List of file paths to FHIR bundle JSON files.
        chunk_size (int, optional): Number of entries to validate at a time. Defaults to 100.
    Returns:
        None
    Raises:
        json.JSONDecodeError: If a bundle file cannot be parsed as JSON.
    Prints:
        str: Validation status of each bundle file.
    """
    
    consolidated_schema = load_consolidated_fhir_schema()
    compiled_validator = compile_fhir_schema(consolidated_schema)
    
    for bundle_file in bundle_files:
        print(f"Validating {bundle_file}...")
        try:
            with open(bundle_file, "r") as f:
                bundle = json.load(f)
                if validate_fhir_bundle_in_chunks(bundle, compiled_validator, chunk_size):
                    print(f"{bundle_file} is valid.")
                else:
                    print(f"{bundle_file} is invalid.")
        except json.JSONDecodeError as e:
            print(f"Failed to parse {bundle_file}: {e}")

def get_fhir_files_from_directory(directory):
    """Get all JSON files in a directory."""
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".json")]

def main():
    parser = argparse.ArgumentParser(description="FHIR Bundle Validator and Content Structure Identifier")
    parser.add_argument('--path', type=str, help="File or directory path to validate or identify content structure")
    parser.add_argument('--action', choices=['validate', 'identify'], default='validate', help="Action to perform: validate the FHIR bundles or identify the content structure")
    parser.add_argument('--chunk-size', type=int, default=100, help="Number of entries per chunk for validation (default: 100)")
    
    args = parser.parse_args()
    path = args.path
    action = args.action
    chunk_size = args.chunk_size

    if os.path.isfile(path):
        if action == 'identify':
            content_structure = identify_content_structure(path)
            print(f"Content structure of {path}: {content_structure}")
        else:
            # Single file validation
            batch_validate_fhir_bundles([path], chunk_size)
    elif os.path.isdir(path):
        fhir_files = get_fhir_files_from_directory(path)
        if not fhir_files:
            print(f"No JSON files found in directory: {path}")
        else:
            if action == 'identify':
                for file in fhir_files:
                    content_structure = identify_content_structure(file)
                    print(f"Content structure of {file}: {content_structure}")
            else:
                batch_validate_fhir_bundles(fhir_files, chunk_size)
    else:
        print(f"{path} is not a valid file or directory")

if __name__ == "__main__":
    main()
