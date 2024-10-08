import pytest
import json
from fhir_validator.validator import validate_fhir_resource, validate_fhir_bundle_in_chunks, load_consolidated_fhir_schema, compile_fhir_schema

@pytest.fixture
def consolidated_schema():
    """Fixture to load the consolidated schema."""
    return load_consolidated_fhir_schema()

@pytest.fixture
def compiled_validator(consolidated_schema):
    """Fixture to compile the schema for fastjsonschema."""
    return compile_fhir_schema(consolidated_schema)

@pytest.fixture
def valid_fhir_bundle():
    """A valid FHIR bundle for testing."""
    return {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "example",
                    "name": [{"family": "Smith", "given": ["John"]}]
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "obs1",
                    "status": "final",
                    "code": {
                        "coding": [
                            {"system": "http://loinc.org", "code": "1234-5"}
                        ]
                    },
                    "subject": {"reference": "Patient/example"}
                }
            }
        ]
    }

@pytest.fixture
def invalid_fhir_bundle():
    """An invalid FHIR bundle with fields that are not part of the schema."""
    return {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "example",
                    "invalidField": "This field should not exist",  # Invalid field
                    "name": [{"family": "Smith", "given": ["John"]}]
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "obs1",
                    "invalidField": "This field should not exist",  # Invalid field
                    "status": "final",
                    "code": {
                        "coding": [
                            {"system": "http://loinc.org", "code": "1234-5"}
                        ]
                    },
                    "subject": {"reference": "Patient/example"}
                }
            }
        ]
    }

def test_valid_fhir_bundle(compiled_validator, valid_fhir_bundle):
    """Test that a valid FHIR bundle passes validation."""
    assert validate_fhir_bundle_in_chunks(valid_fhir_bundle, compiled_validator), "Valid FHIR bundle should pass validation"

def test_invalid_fhir_bundle(compiled_validator, invalid_fhir_bundle):
    """Test that an invalid FHIR bundle fails validation due to invalid fields."""
    assert not validate_fhir_bundle_in_chunks(invalid_fhir_bundle, compiled_validator), "Invalid FHIR bundle should fail validation due to invalid fields"

def test_validate_single_resource_valid(compiled_validator):
    """Test that a single valid FHIR resource passes validation."""
    valid_resource = {
        "resourceType": "Patient",
        "id": "example",
        "name": [{"family": "Doe", "given": ["Jane"]}]
    }
    is_valid, error = validate_fhir_resource(valid_resource, compiled_validator)
    assert is_valid, f"Expected valid resource to pass but got error: {error}"

def test_validate_single_resource_invalid(compiled_validator):
    """Test that a single invalid FHIR resource fails validation due to an invalid field."""
    invalid_resource = {
        "resourceType": "Patient",
        "id": "example",
        "invalidField": "This field should not exist"  # Invalid field
    }
    is_valid, error = validate_fhir_resource(invalid_resource, compiled_validator)
    print(f"Error: {error}")  # For debugging purposes
    assert not is_valid, "Expected invalid resource to fail validation due to invalid field"

def test_large_fhir_bundle_chunk_processing(compiled_validator):
    """Test that chunk processing works for large bundles."""
    large_fhir_bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [{"resource": {"resourceType": "Patient", "id": f"patient-{i}"}} for i in range(500)]
    }
    assert validate_fhir_bundle_in_chunks(large_fhir_bundle, compiled_validator, chunk_size=50), "Large FHIR bundle should pass validation"
