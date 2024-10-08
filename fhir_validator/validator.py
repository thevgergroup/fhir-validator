import os
import json
import argparse
import fastjsonschema

# Path to the consolidated FHIR schema
CONSOLIDATED_SCHEMA_PATH = "schemas/r4/fhir.schema.json"

# Content Structure Types
CONTENT_STRUCTURE_UNSPECIFIED = "CONTENT_STRUCTURE_UNSPECIFIED"
BUNDLE = "BUNDLE"
RESOURCE = "RESOURCE"
BUNDLE_PRETTY = "BUNDLE_PRETTY"
RESOURCE_PRETTY = "RESOURCE_PRETTY"

def load_consolidated_fhir_schema():
    """Load the consolidated FHIR schema from the file."""
    if os.path.exists(CONSOLIDATED_SCHEMA_PATH):
        with open(CONSOLIDATED_SCHEMA_PATH, 'r') as schema_file:
            return json.load(schema_file)
    else:
        raise FileNotFoundError(f"Consolidated FHIR schema not found at {CONSOLIDATED_SCHEMA_PATH}")

def compile_fhir_schema(schema):
    """Compile the FHIR schema using fastjsonschema."""
    try:
        return fastjsonschema.compile(schema)
    except fastjsonschema.JsonSchemaException as e:
        raise ValueError(f"Failed to compile schema: {e}")

def validate_fhir_resource(resource, compiled_validator):
    """Validate a FHIR resource using the compiled validator."""
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

def validate_fhir_bundle_in_chunks(bundle, compiled_validator, chunk_size=100):
    """Validate a FHIR bundle in chunks to avoid long validation times."""
    idx = 0
    for chunk in split_bundle(bundle, chunk_size):
        is_valid = validate_fhir_bundle(chunk, compiled_validator)
        print(f"\t Validating chunk {idx} as {is_valid}...")
        if not is_valid:
            return False
        idx += 1
    return True

def validate_fhir_bundle(bundle, compiled_validator):
    """Validates each resource in the FHIR bundle."""
    if bundle.get('resourceType') != 'Bundle':
        raise ValueError("Input is not a valid FHIR Bundle")
    
    for entry in bundle.get("entry", []):
        resource = entry.get("resource")
        if resource:
            is_valid, error_message = validate_fhir_resource(resource, compiled_validator)
            if not is_valid:
                print(f"Validation failed for {resource.get('resourceType', 'Unknown')}: {error_message}")
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


def identify_content_structure(file_path):
    """Identify the content structure of the input file."""
    
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
    """Batch validate FHIR bundle files using the compiled validator in chunks."""
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
