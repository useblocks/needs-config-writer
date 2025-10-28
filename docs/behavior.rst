Behavior
--------

Configuration Export Process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Collection:** The extension collects all Sphinx-Needs configuration values (those starting with ``needs_``)
2. **Filtering:** Removes unsupported types that cannot be serialized to TOML (e.g., ``None`` values, functions)
3. **Conversion:** Converts special types (e.g., ``Path`` objects to strings) with warnings
4. **Sorting:** Sorts all data structures (dicts, lists, sets) for reproducible output
5. **Comparison:** If file exists and :ref:`config_warn_on_diff` is ``True``, compares existing content with new content
6. **Writing:** Writes the TOML file to the specified output path

Type Handling
~~~~~~~~~~~~~

The extension handles various Python types when converting configuration to TOML:

**Supported Types:**

- Basic types: ``str``, ``int``, ``float``, ``bool``
- Date/time types: ``date``, ``datetime``, ``time``
- Collections: ``dict``, ``list``, ``tuple``, ``set``

**Special Handling:**

- ``None`` values are filtered out (TOML doesn't support null)
- ``Path``/``PosixPath`` objects are converted to strings with a warning
- Sets are converted to sorted lists for reproducibility
- Unsupported types generate warnings and are filtered out

Sorting for Reproducibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To ensure consistent hashes regardless of configuration order, the extension applies
custom sorting rules:

**Dictionary Sorting:**

All dictionaries are sorted by key alphabetically.

**List Sorting:**

Lists are sorted based on their content type and path in the configuration:

- ``external_needs``: Sorted by ``id_prefix`` field
- ``extra_links``: Sorted by ``option`` field
- ``extra_options``: Dynamically sorted - if list of strings, sorted as primitives; if list of dicts, sorted by ``name`` field
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

   - **List of dictionaries**: ``needs_extra_options = [dict(name="component", ...), dict(name="security", ...), ...]``

     Sorted alphabetically by the ``name`` field.

   The extension automatically detects the format and applies the appropriate sorting strategy.

**Set Sorting:**

Sets are converted to sorted lists.

File Lifecycle
~~~~~~~~~~~~~~

The extension follows this lifecycle during Sphinx builds:

1. **Build Start:** Extension is initialized after all configuration is loaded
2. **Config Initialized:** The ``write_ubproject_file`` function is called (priority 999)
3. **Content Check:** If the output file exists:

   - Reads existing file content
   - Compares with new configuration content
   - If content matches: Logs info message, no file write
   - If content differs and :ref:`config_warn_on_diff` is ``True``: Emits warning
   - If content differs and :ref:`config_overwrite` is ``True``: Writes file, logs info
   - If content differs and :ref:`config_overwrite` is ``False``: Does not write file, logs info

4. **File Creation:** If output file doesn't exist, creates parent directories and writes file

Warnings and Logging
~~~~~~~~~~~~~~~~~~~~

The extension generates warnings for:

- **Path conversions:** When ``Path`` objects are converted to strings
- **Unsupported types:** When configuration values cannot be serialized to TOML
- **Content differences:** When existing file content differs from new configuration (if :ref:`config_warn_on_diff` is ``True``)

Info messages are logged for:

- File creation
- File updates (when content changes and :ref:`config_overwrite` is ``True``)
- Unchanged configuration (when content matches)
- Skipped updates (when content differs but :ref:`config_overwrite` is ``False``)
