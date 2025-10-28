Configuration
=============

The ``needs-config-writer`` extension provides several configuration options to control how
Sphinx-Needs configuration is exported to ``ubproject.toml``.

Configuration Options
---------------------

All configuration options are set in your Sphinx ``conf.py`` file.

needscfg_outpath
~~~~~~~~~~~~~~~~

**Type:** ``str``

**Default:** ``"${outdir}/ubproject.toml"``

Specifies the output path where the ``ubproject.toml`` file will be written.

The path supports template variables:

- ``${outdir}`` - Replaced with the Sphinx output directory (build directory)
- ``${srcdir}`` - Replaced with the Sphinx source directory

Relative paths are interpreted relative to the configuration directory (where ``conf.py`` is located).

**Examples:**

.. code-block:: python

   # Write to build output directory (default)
   needscfg_outpath = "${outdir}/ubproject.toml"

   # Write to source directory
   needscfg_outpath = "${srcdir}/ubproject.toml"

   # Write to custom subdirectory in output
   needscfg_outpath = "${outdir}/config/needs.toml"

   # Relative path (relative to conf.py location)
   needscfg_outpath = "generated/ubproject.toml"

   # Absolute path
   needscfg_outpath = "/absolute/path/to/ubproject.toml"

needscfg_use_hash
~~~~~~~~~~~~~~~~~

**Type:** ``bool``

**Default:** ``True``

Controls whether to generate and include a SHA1 hash of the configuration in the output file.

When enabled, the extension:

1. Calculates a SHA1 hash of the needs configuration
2. Adds a ``[meta]`` section with ``needs_hash`` to the output file
3. Compares the hash with existing files to detect changes

The hash is calculated from the sorted and normalized configuration to ensure reproducibility
regardless of the order in which configuration values are defined in ``conf.py``.

**Examples:**

.. code-block:: python

   # Enable hash generation (default)
   needscfg_use_hash = True

   # Disable hash generation
   needscfg_use_hash = False

**Output with hash:**

.. code-block:: toml

   [meta]
   needs_hash = "a1b2c3d4e5f6..."

   [needs]
   # ... configuration ...

**Output without hash:**

.. code-block:: toml

   [needs]
   # ... configuration ...

needscfg_overwrite
~~~~~~~~~~~~~~~~~~

**Type:** ``bool``

**Default:** ``False``

Controls whether to overwrite an existing output file when the configuration has changed.

This option only takes effect when ``needscfg_use_hash = True`` and the hash of the new
configuration differs from the existing file's hash.

**Behavior:**

- ``False`` (default): Issues a warning about hash mismatch but does not overwrite the file
- ``True``: Overwrites the file with the new configuration and logs an info message

**Examples:**

.. code-block:: python

   # Warn but don't overwrite (default)
   needscfg_overwrite = False

   # Automatically update when configuration changes
   needscfg_overwrite = True

.. note::

   When ``needscfg_use_hash = False``, files are always written on each build regardless
   of this setting.

needscfg_write_defaults
~~~~~~~~~~~~~~~~~~~~~~~

**Type:** ``bool``

**Default:** ``False``

Controls whether to include all Sphinx-Needs configuration values (including defaults) or
only explicitly configured values.

**Behavior:**

- ``False`` (default): Only writes configuration values that were explicitly set in ``conf.py``
- ``True``: Writes all Sphinx-Needs configuration values, including default values

**Examples:**

.. code-block:: python

   # Write only explicitly configured values (default)
   needscfg_write_defaults = False

   # Write all configuration including defaults
   needscfg_write_defaults = True

.. tip::

   Set this to ``True`` if you want to see the complete configuration with all defaults,
   useful for documentation or when migrating configuration to ``ubproject.toml``.

Extension Behavior
------------------

Configuration Export Process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Collection:** The extension collects all Sphinx-Needs configuration values (those starting with ``needs_``)
2. **Filtering:** Removes unsupported types that cannot be serialized to TOML (e.g., ``None`` values, functions)
3. **Conversion:** Converts special types (e.g., ``Path`` objects to strings) with warnings
4. **Sorting:** Sorts all data structures (dicts, lists, sets) for reproducible output
5. **Hashing:** Optionally calculates SHA1 hash of the configuration
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
- ``extra_options``: Sorted as primitives
- ``flow_link_types``: Sorted as primitives
- ``json_exclude_fields``: Sorted as primitives
- ``statuses``: Sorted by ``name`` field
- ``tags``: Sorted by ``name`` field
- ``types``: Sorted by ``title`` field
- ``variant_options``: Sorted as primitives

Other lists preserve their original order but nested structures are still sorted.

**Set Sorting:**

Sets are converted to sorted lists.

File Lifecycle
~~~~~~~~~~~~~~

The extension follows this lifecycle during Sphinx builds:

1. **Build Start:** Extension is initialized after all configuration is loaded
2. **Config Initialized:** The ``write_ubproject_file`` function is called (priority 999)
3. **Hash Check:** If the output file exists and ``needscfg_use_hash = True``:

   - Reads existing file and extracts hash
   - Compares with new configuration hash
   - If hashes match: Logs info message, no file write
   - If hashes differ and ``needscfg_overwrite = False``: Logs warning, no file write
   - If hashes differ and ``needscfg_overwrite = True``: Overwrites file, logs info

4. **File Creation:** If output file doesn't exist, creates parent directories and writes file

Warnings and Logging
~~~~~~~~~~~~~~~~~~~~

The extension generates warnings for:

- **Path conversions:** When ``Path`` objects are converted to strings
- **Unsupported types:** When configuration values cannot be serialized to TOML
- **Hash mismatches:** When existing file hash differs from new configuration (if ``needscfg_overwrite = False``)

Info messages are logged for:

- File creation
- File updates (when ``needscfg_overwrite = True``)
- Unchanged configuration (when hashes match)

Example Configurations
----------------------

Minimal Setup
~~~~~~~~~~~~~

.. code-block:: python

   # conf.py
   extensions = [
       "sphinx_needs",
       "needs_config_writer",
   ]

This will write the configuration to ``${outdir}/ubproject.toml`` with hash generation enabled,
but will not overwrite existing files.

Development Setup
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # conf.py
   extensions = [
       "sphinx_needs",
       "needs_config_writer",
   ]

   needscfg_use_hash = True
   needscfg_overwrite = True
   needscfg_outpath = "${srcdir}/ubproject.toml"

This configuration automatically updates the file in the source directory whenever
configuration changes, useful during development.

Full Configuration Export
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # conf.py
   extensions = [
       "sphinx_needs",
       "needs_config_writer",
   ]

   needscfg_write_defaults = True
   needscfg_use_hash = False
   needscfg_outpath = "${outdir}/full_config.toml"

This exports the complete configuration including all defaults, without hash checking.

CI/CD Setup
~~~~~~~~~~~

.. code-block:: python

   # conf.py
   extensions = [
       "sphinx_needs",
       "needs_config_writer",
   ]

   needscfg_use_hash = True
   needscfg_overwrite = False
   needscfg_outpath = "${outdir}/ubproject.toml"

Default settings are appropriate for CI/CD: generates hash for verification but doesn't
overwrite, allowing you to catch configuration drift.
