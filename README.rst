FHIR Validator
==============

-  `FHIR Validator <#fhir-validator>`__

   -  `Background <#background>`__
   -  `Objective <#objective>`__

      -  `Example: CLI validation
         usage <#example-cli-validation-usage>`__

   -  `Installation <#installation>`__

      -  `Using pip <#using-pip>`__
      -  `Using Poetry <#using-poetry>`__

   -  `CLI Usage <#cli-usage>`__

      -  `Validate a FHIR File: <#validate-a-fhir-file>`__
      -  `Identify the Content
         Structure: <#identify-the-content-structure>`__
      -  `Options: <#options>`__
      -  `Chunk size <#chunk-size>`__

   -  `Integration <#integration>`__

      -  `Example: Validate a FHIR
         File <#example-validate-a-fhir-file>`__

   -  `Development <#development>`__

      -  `Setting Up Your Development
         Environment <#setting-up-your-development-environment>`__
      -  `Tests <#tests>`__

Background
----------

While testing Google’s FHIR Store and following the provided
documentation, we encountered an issue where the import process wasn’t
working as expected. A great tool from MITRE called
`Synthea <https://github.com/synthetichealth/synthea/>`__ generates
synthetic patient FHIR records, and it’s even recommended by Google in
their examples. However, either due to unclear documentation or our
oversight, the import of this generated data failed. After struggling
with over 60,000 “invalid JSON” error messages in Google Healthcare, we
realized we were missing a crucial content-structure flag. It took us an
entire day to figure out the issue.

This got us thinking—what happens when you have an ETL process dealing
with hundreds of thousands of files?

We explored existing FHIR validation tools, including those from HL7.
However, we found that even for a small 2MB patient file, some
validators took up to 6 minutes and produced over 1,000 warnings and
errors—most of which were related to external terminologies and content
that was valid and parsable by the FHIR store.

This led us to develop a simple validator designed to quickly check if
your FHIR files conform to the FHIR R4 schema. The goal is to quickly
reject problematic files before they clutter your logs and overwhelm
your monitoring systems.

Objective
---------

The objective of ``fhir-validator`` is to quickly and efficiently
validate FHIR (Fast Healthcare Interoperability Resources) files i
against the FHIR schema for structure.

Most validators are rules based delving deep into contents of the FHIR
messages, and are often embedded directly into FHIR stores of software
used to process FHIR messages and are heavily verbose.

This is meant to be a lightweight fast validation ensure conformity
against the FHIR structure.

This script also identifies the FHIR messages content structure used
primarily in Google FHIR Store. (e.g., ``BUNDLE``, ``RESOURCE``,
``BUNDLE_PRETTY``, ``RESOURCE_PRETTY``)

Allowing you to determine the appropriate switch for import

Example: CLI validation usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: sh

   $ fhir-validator --path data/samples/fhir --action identify
   Content structure of data/samples/fhir/practitionerInformation1728333795898.json: BUNDLE_PRETTY
   Content structure of data/samples/fhir/hospitalInformation1728333795898.json: BUNDLE_PRETTY
   Content structure of data/samples/fhir/Maricela194_Heidenreich818_9a998c27-9e98-29c2-8878-e214c9cef5ed.json: BUNDLE_PRETTY
   Content structure of data/samples/fhir/Laquanda221_Haag279_84a90023-0c6b-0eb9-95d6-50861e13f9b3.json: BUNDLE_PRETTY

   # Performing a google import
   $ gcloud healthcare fhir-stores import gcs fhir-store \
       --dataset=fhir-dataset \
       --gcs-uri=gs://$BUCKET_NAME/*.json \
       --content-structure=bundle-pretty

Installation
------------

You can install ``fhir-validator`` using either ``pip`` or ``Poetry``.

Using pip
~~~~~~~~~

.. code:: bash

   pip install fhir-validator

Using Poetry
~~~~~~~~~~~~

.. code:: bash

   poetry add fhir-validator

CLI Usage
---------

Once installed, you can use the ``fhir-validator`` CLI to validate FHIR
files or identify their content structure.

.. code:: sh

   $ fhir-validator --help
   usage: fhir-validator [-h] [--path PATH] [--action {validate,identify}] [--chunk-size CHUNK_SIZE]

   FHIR Bundle Validator and Content Structure Identifier

   optional arguments:
     -h, --help            show this help message and exit
     --path PATH           File or directory path to validate or identify content structure
     --action {validate,identify}
                           Action to perform: validate the FHIR bundles or identify the content structure
     --chunk-size CHUNK_SIZE
                           Number of entries per chunk for validation (default: 100)

Validate a FHIR File:
~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   fhir-validator --path path/to/fhir_file.json --action validate

Identify the Content Structure:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   fhir-validator --path path/to/fhir_file.json --action identify

This will return

+---------+------------------------------------------------------------+
| FLAG    | Description                                                |
+=========+============================================================+
| ``B     | The source file contains one or more lines of              |
| UNDLE`` | newline-delimited JSON (ndjson). Each line is a bundle,    |
|         | which contains one or more resources. If you don’t specify |
|         | ContentStructure, it defaults to BUNDLE.                   |
+---------+------------------------------------------------------------+
| ``RES   | The source file contains one or more lines of              |
| OURCE`` | newline-delimited JSON (ndjson). Each line is a single     |
|         | resource.                                                  |
+---------+------------------------------------------------------------+
| ``RES   | The entire source file is one JSON resource. The JSON can  |
| OURCE-P | span multiple lines.                                       |
| RETTY`` |                                                            |
+---------+------------------------------------------------------------+
| ``B     | The entire source file is one JSON bundle. The JSON can    |
| UNDLE-P | span multiple lines.                                       |
| RETTY`` |                                                            |
+---------+------------------------------------------------------------+

Options:
~~~~~~~~

-  ``--path``: Specify the file or directory path to validate or
   identify.
-  ``--action``: Choose ``validate`` to validate the file or
   ``identify`` to determine the content structure.
-  ``--chunk-size``: (Optional) Number of entries per chunk for
   validation, defaults to 100.

Chunk size
~~~~~~~~~~

Breaks the file into it’s entry components allowing for faster
validation against chunks of the json files.

Integration
-----------

You can also use ``fhir-validator`` directly in your Python code. Here’s
an example of how to integrate the validation or content structure
identification into a Python project:

Example: Validate a FHIR File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

   from fhir_validator import (compile_fhir_schema, 
                               identify_content_structure, 
                               load_consolidated_fhir_schema,
                               validate_fhir_bundle_in_chunks,
                               BUNDLE_PRETTY) 
   import json                            

   file_path = "data/samples/fhir/Laquanda221_Haag279_84a90023-0c6b-0eb9-95d6-50861e13f9b3.json"
   content_structure = identify_content_structure(file_path)

   print(f"Content structure: {content_structure}")

   # By default loads the r4 schema
   schema_json = load_consolidated_fhir_schema('schemas/r4/fhir.schema.json')
   compiled_validator = compile_fhir_schema(schema_json)

   # If content structure is a bundle, validate it
   if content_structure == BUNDLE_PRETTY:
       with open(file_path, 'r') as f:
           bundle = json.load(f)
       is_valid = validate_fhir_bundle_in_chunks(bundle, compiled_validator)
       print(f"File : {file_path} is valid ? {is_valid}")

This simple Python snippet demonstrates how to check the content
structure of a FHIR file and, if it’s a ``BUNDLE_PRETTY``, how to
validate its content.

--------------

Development
-----------

To contribute to the ``fhir-validator`` project, you’ll need to install
the necessary dependencies, including the ``dev`` and ``test`` groups
for development tools and testing. The ``pre-commit`` hooks are part of
the ``dev`` group, and ``pytest`` is part of the ``test`` group.

Setting Up Your Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Clone the repository**:

   .. code:: bash

      git clone https://github.com/thevgergroup/fhir-validator.git
      cd fhir-validator

2. **Install dependencies using Poetry**:

   Install both the ``dev`` and ``test`` groups to ensure you have all
   the necessary tools for development and testing:

   .. code:: bash

      poetry install --with dev,test

   This command installs the base dependencies along with the ``dev``
   group (which includes tools like ``pre-commit``) and the ``test``
   group (which includes tools like ``pytest``).

   We use pandoc to generate the README.rst for pypi to ensure links are
   correctly structured see [Installing
   Pandoc](https://pandoc.org/installing.html] Update the any necessary
   changes in ``README.md`` and the pre-commit hook will perform the
   conversion.

3. **Install the Pre-commit Hooks**:

   The project uses ``pre-commit`` to automate tasks such as converting
   ``README.md`` to ``README.rst`` before commits. To set up the
   pre-commit hooks locally, run:

   .. code:: bash

      poetry run pre-commit install

   This will configure the Git hooks to automatically run when you make
   a commit.

Tests
~~~~~

We use pytest see the unit tests in ``tests``

.. code:: sh

   poetry run pytest

.. _fhir-validator-1:

FHIR Validator
==============

-  `FHIR Validator <#fhir-validator>`__

   -  `Background <#background>`__
   -  `Objective <#objective>`__

      -  `Example: CLI validation
         usage <#example-cli-validation-usage>`__

   -  `Installation <#installation>`__

      -  `Using pip <#using-pip>`__
      -  `Using Poetry <#using-poetry>`__

   -  `CLI Usage <#cli-usage>`__

      -  `Validate a FHIR File: <#validate-a-fhir-file>`__
      -  `Identify the Content
         Structure: <#identify-the-content-structure>`__
      -  `Options: <#options>`__
      -  `Chunk size <#chunk-size>`__

   -  `Integration <#integration>`__

      -  `Example: Validate a FHIR
         File <#example-validate-a-fhir-file>`__

   -  `Development <#development>`__

      -  `Setting Up Your Development
         Environment <#setting-up-your-development-environment>`__
      -  `Tests <#tests>`__

.. _background-1:

Background
----------

While testing Google’s FHIR Store and following the provided
documentation, we encountered an issue where the import process wasn’t
working as expected. A great tool from MITRE called
`Synthea <https://github.com/synthetichealth/synthea/>`__ generates
synthetic patient FHIR records, and it’s even recommended by Google in
their examples. However, either due to unclear documentation or our
oversight, the import of this generated data failed. After struggling
with over 60,000 “invalid JSON” error messages in Google Healthcare, we
realized we were missing a crucial content-structure flag. It took us an
entire day to figure out the issue.

This got us thinking—what happens when you have an ETL process dealing
with hundreds of thousands of files?

We explored existing FHIR validation tools, including those from HL7.
However, we found that even for a small 2MB patient file, some
validators took up to 6 minutes and produced over 1,000 warnings and
errors—most of which were related to external terminologies and content
that was valid and parsable by the FHIR store.

This led us to develop a simple validator designed to quickly check if
your FHIR files conform to the FHIR R4 schema. The goal is to quickly
reject problematic files before they clutter your logs and overwhelm
your monitoring systems.

.. _objective-1:

Objective
---------

The objective of ``fhir-validator`` is to quickly and efficiently
validate FHIR (Fast Healthcare Interoperability Resources) files i
against the FHIR schema for structure.

Most validators are rules based delving deep into contents of the FHIR
messages, and are often embedded directly into FHIR stores of software
used to process FHIR messages and are heavily verbose.

This is meant to be a lightweight fast validation ensure conformity
against the FHIR structure.

This script also identifies the FHIR messages content structure used
primarily in Google FHIR Store. (e.g., ``BUNDLE``, ``RESOURCE``,
``BUNDLE_PRETTY``, ``RESOURCE_PRETTY``)

Allowing you to determine the appropriate switch for import

.. _example-cli-validation-usage-1:

Example: CLI validation usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: sh

   $ fhir-validator --path data/samples/fhir --action identify
   Content structure of data/samples/fhir/practitionerInformation1728333795898.json: BUNDLE_PRETTY
   Content structure of data/samples/fhir/hospitalInformation1728333795898.json: BUNDLE_PRETTY
   Content structure of data/samples/fhir/Maricela194_Heidenreich818_9a998c27-9e98-29c2-8878-e214c9cef5ed.json: BUNDLE_PRETTY
   Content structure of data/samples/fhir/Laquanda221_Haag279_84a90023-0c6b-0eb9-95d6-50861e13f9b3.json: BUNDLE_PRETTY

   # Performing a google import
   $ gcloud healthcare fhir-stores import gcs fhir-store \
       --dataset=fhir-dataset \
       --gcs-uri=gs://$BUCKET_NAME/*.json \
       --content-structure=bundle-pretty

.. _installation-1:

Installation
------------

You can install ``fhir-validator`` using either ``pip`` or ``Poetry``.

.. _using-pip-1:

Using pip
~~~~~~~~~

.. code:: bash

   pip install fhir-validator

.. _using-poetry-1:

Using Poetry
~~~~~~~~~~~~

.. code:: bash

   poetry add fhir-validator

.. _cli-usage-1:

CLI Usage
---------

Once installed, you can use the ``fhir-validator`` CLI to validate FHIR
files or identify their content structure.

.. code:: sh

   $ fhir-validator --help
   usage: fhir-validator [-h] [--path PATH] [--action {validate,identify}] [--chunk-size CHUNK_SIZE]

   FHIR Bundle Validator and Content Structure Identifier

   optional arguments:
     -h, --help            show this help message and exit
     --path PATH           File or directory path to validate or identify content structure
     --action {validate,identify}
                           Action to perform: validate the FHIR bundles or identify the content structure
     --chunk-size CHUNK_SIZE
                           Number of entries per chunk for validation (default: 100)

.. _validate-a-fhir-file-1:

Validate a FHIR File:
~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   fhir-validator --path path/to/fhir_file.json --action validate

.. _identify-the-content-structure-1:

Identify the Content Structure:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   fhir-validator --path path/to/fhir_file.json --action identify

This will return

+---------+------------------------------------------------------------+
| FLAG    | Description                                                |
+=========+============================================================+
| ``B     | The source file contains one or more lines of              |
| UNDLE`` | newline-delimited JSON (ndjson). Each line is a bundle,    |
|         | which contains one or more resources. If you don’t specify |
|         | ContentStructure, it defaults to BUNDLE.                   |
+---------+------------------------------------------------------------+
| ``RES   | The source file contains one or more lines of              |
| OURCE`` | newline-delimited JSON (ndjson). Each line is a single     |
|         | resource.                                                  |
+---------+------------------------------------------------------------+
| ``RES   | The entire source file is one JSON resource. The JSON can  |
| OURCE-P | span multiple lines.                                       |
| RETTY`` |                                                            |
+---------+------------------------------------------------------------+
| ``B     | The entire source file is one JSON bundle. The JSON can    |
| UNDLE-P | span multiple lines.                                       |
| RETTY`` |                                                            |
+---------+------------------------------------------------------------+

.. _options-1:

Options:
~~~~~~~~

-  ``--path``: Specify the file or directory path to validate or
   identify.
-  ``--action``: Choose ``validate`` to validate the file or
   ``identify`` to determine the content structure.
-  ``--chunk-size``: (Optional) Number of entries per chunk for
   validation, defaults to 100.

.. _chunk-size-1:

Chunk size
~~~~~~~~~~

Breaks the file into it’s entry components allowing for faster
validation against chunks of the json files.

.. _integration-1:

Integration
-----------

You can also use ``fhir-validator`` directly in your Python code. Here’s
an example of how to integrate the validation or content structure
identification into a Python project:

.. _example-validate-a-fhir-file-1:

Example: Validate a FHIR File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

   from fhir_validator import (compile_fhir_schema, 
                               identify_content_structure, 
                               load_consolidated_fhir_schema,
                               validate_fhir_bundle_in_chunks,
                               BUNDLE_PRETTY) 
   import json                            

   file_path = "data/samples/fhir/Laquanda221_Haag279_84a90023-0c6b-0eb9-95d6-50861e13f9b3.json"
   content_structure = identify_content_structure(file_path)

   print(f"Content structure: {content_structure}")

   # By default loads the r4 schema
   schema_json = load_consolidated_fhir_schema('schemas/r4/fhir.schema.json')
   compiled_validator = compile_fhir_schema(schema_json)

   # If content structure is a bundle, validate it
   if content_structure == BUNDLE_PRETTY:
       with open(file_path, 'r') as f:
           bundle = json.load(f)
       is_valid = validate_fhir_bundle_in_chunks(bundle, compiled_validator)
       print(f"File : {file_path} is valid ? {is_valid}")

This simple Python snippet demonstrates how to check the content
structure of a FHIR file and, if it’s a ``BUNDLE_PRETTY``, how to
validate its content.

--------------

.. _development-1:

Development
-----------

To contribute to the ``fhir-validator`` project, you’ll need to install
the necessary dependencies, including the ``dev`` and ``test`` groups
for development tools and testing. The ``pre-commit`` hooks are part of
the ``dev`` group, and ``pytest`` is part of the ``test`` group.

.. _setting-up-your-development-environment-1:

Setting Up Your Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Clone the repository**:

   .. code:: bash

      git clone https://github.com/thevgergroup/fhir-validator.git
      cd fhir-validator

2. **Install dependencies using Poetry**:

   Install both the ``dev`` and ``test`` groups to ensure you have all
   the necessary tools for development and testing:

   .. code:: bash

      poetry install --with dev,test

   This command installs the base dependencies along with the ``dev``
   group (which includes tools like ``pre-commit``) and the ``test``
   group (which includes tools like ``pytest``).

   We use pandoc to generate the README.rst for pypi to ensure links are
   correctly structured see [Installing
   Pandoc](https://pandoc.org/installing.html] Update the any necessary
   changes in ``README.md`` and the pre-commit hook will perform the
   conversion.

3. **Install the Pre-commit Hooks**:

   The project uses ``pre-commit`` to automate tasks such as converting
   ``README.md`` to ``README.rst`` before commits. To set up the
   pre-commit hooks locally, run:

   .. code:: bash

      poetry run pre-commit install

   This will configure the Git hooks to automatically run when you make
   a commit.

.. _tests-1:

Tests
~~~~~

We use pytest see the unit tests in ``tests``

.. code:: sh

   poetry run pytest
