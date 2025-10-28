Behavior
--------

Configuration export process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Collection:** The extension collects all Sphinx-Needs configuration values
   (those starting with ``needs_``)
#. **Exclusion:** Excludes certain resolved configuration values that should not be written
   (see :ref:`excluded_configs`)
#. **Filtering:** Removes unsupported types that cannot be serialized to TOML
   (e.g., ``None`` values, functions)
#. **Conversion:** Converts special types (e.g., ``Path`` objects to strings) with warnings
#. **Sorting:** Sorts all data structures (dicts, lists, sets) for reproducible output
#. **Header generation:** If :ref:`config_add_header` is ``True`` (default),
   prepends an auto-generated warning header
#. **Comparison:** If file exists and :ref:`config_warn_on_diff` is ``True``,
   compares existing content with new content
#. **Writing:** Writes the TOML file to the specified output path

.. _`excluded_configs`:

Excluded configurations
~~~~~~~~~~~~~~~~~~~~~~~

The following ``needs_*`` configuration values are automatically excluded from the exported
TOML file:

- ``needs_from_toml``: Path to TOML file to load configuration from
- ``needs_from_toml_table``: Specific table name in TOML file to load
- ``needs_schema_definitions_from_json``: Path to JSON schema definitions file

**Rationale:** These configurations are used to *load* or *resolve* configuration from
external sources. Including them in the exported TOML file would create circular dependencies or
redundant references. The exported file contains the *resolved* values from these sources,
not the loading instructions themselves.

For example, if you use ``needs_from_toml = "shared.toml"`` to load shared configuration,
the exported ``ubproject.toml`` will contain the actual configuration values from ``shared.toml``,
not a reference to load from ``shared.toml`` again.

Type handling
~~~~~~~~~~~~~

The extension handles various Python types when converting configuration to TOML:

**Supported types:**

- Basic types: ``str``, ``int``, ``float``, ``bool``
- Date/time types: ``date``, ``datetime``, ``time``
- Collections: ``dict``, ``list``, ``tuple``, ``set``

**Special handling:**

- ``None`` values are filtered out (TOML doesn't support null)
- ``Path``/``PosixPath`` objects are converted to strings with a warning
- Sets are converted to sorted lists for reproducibility
- Unsupported types generate warnings and are filtered out

Sorting for reproducibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To ensure consistent hashes regardless of configuration order, the extension applies
custom sorting rules:

**Dictionary sorting:**

All dictionaries are sorted by key alphabetically.

**List sorting:**

Lists are sorted based on their content type and path in the configuration:

- ``external_needs``: Sorted by ``id_prefix`` field
- ``extra_links``: Sorted by ``option`` field
- ``extra_options``: Dynamically sorted - if list of strings, sorted as primitives;
  if list of dicts, sorted by ``name`` field
- ``flow_link_types``: Sorted as primitives
- ``json_exclude_fields``: Sorted as primitives
- ``statuses``: Sorted by ``name`` field
- ``tags``: Sorted by ``name`` field
- ``types``: Sorted by ``title`` field
- ``variant_options``: Sorted as primitives

Other lists preserve their original order but nested structures are still sorted.

.. note::

   The ``extra_options`` configuration supports two formats:

   - **List of strings**: ``needs_extra_options = ["component", "security", "version"]``

     Sorted alphabetically as primitives.

   - **List of dictionaries**:
     ``needs_extra_options = [dict(name="component", ...), dict(name="security", ...), ...]``

     Sorted alphabetically by the ``name`` field.

   The extension automatically detects the format and applies the appropriate sorting strategy.

**Set sorting:**

Sets are converted to sorted lists.

File lifecycle
~~~~~~~~~~~~~~

The extension follows this lifecycle during Sphinx builds:

1. **Build start:** Extension is initialized after all configuration is loaded
#. **Config initialized:** The ``write_ubproject_file`` function is called (priority 999)
#. **Content check:** If the output file exists:

   - Reads existing file content
   - Compares with new configuration content
   - If content matches: Logs info message, no file write
   - If content differs and :ref:`config_warn_on_diff` is ``True``: Emits warning
   - If content differs and :ref:`config_overwrite` is ``True``: Writes file, logs info
   - If content differs and :ref:`config_overwrite` is ``False``: Does not write file, logs info

4. **File creation:** If output file doesn't exist, creates parent directories and writes file

Warnings and logging
~~~~~~~~~~~~~~~~~~~~

The extension generates warnings for:

- **Path conversions:** When ``Path`` objects are converted to strings
- **Unsupported types:** When configuration values cannot be serialized to TOML
- **Content differences:** When existing file content differs from new configuration
  (if :ref:`config_warn_on_diff` is ``True``)

Info messages are logged for:

- File creation
- File updates (when content changes and :ref:`config_overwrite` is ``True``)
- Unchanged configuration (when content matches)
- Skipped updates (when content differs but :ref:`config_overwrite` is ``False``)
