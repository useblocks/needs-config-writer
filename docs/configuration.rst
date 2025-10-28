Configuration
=============

The ``needs-config-writer`` extension provides several configuration options to control how
Sphinx-Needs configuration is exported to ``ubproject.toml``.

Configuration Options
---------------------

All configuration options are set in your Sphinx ``conf.py`` file.

.. _`config_outpath`:

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

.. _`config_warn_on_diff`:

needscfg_warn_on_diff
~~~~~~~~~~~~~~~~~~~~~

**Type:** ``bool``

**Default:** ``False``

Controls whether to emit a warning when the existing output file content differs from the
new configuration being generated.

When enabled and the output file already exists:

- The extension compares the existing file content with the new content
- If they differ, emits a warning (subtype: ``content_diff``)
- Whether the file is updated depends on :ref:`config_overwrite`

**Behavior:**

- ``False`` (default): No warning is emitted when content changes
- ``True``: Emits a warning when existing file content differs from new configuration

**Examples:**

.. code-block:: python

   # No warning on content changes (default)
   needscfg_warn_on_diff = False

   # Warn when configuration changes
   needscfg_warn_on_diff = True

.. tip:: Enable this in CI/CD pipelines to detect unexpected configuration changes.

.. _`config_overwrite`:

needscfg_overwrite
~~~~~~~~~~~~~~~~~~

**Type:** ``bool``

**Default:** ``True``

Controls whether to overwrite an existing output file when the configuration content differs.

**Behavior:**

- ``True`` (default): Overwrites the file when content differs
- ``False``: Does not overwrite the file when content differs (logs info message instead)

**Examples:**

.. code-block:: python

   # Automatically update when configuration changes (default)
   needscfg_overwrite = True

   # Prevent overwriting existing files
   needscfg_overwrite = False

.. note::

   When :ref:`config_overwrite` is ``False`` and content differs, the extension will log an info
   message but not update the file. This is useful to prevent accidentally overwriting
   manually edited configuration files.

.. _`config_write_all`:

needscfg_write_all
~~~~~~~~~~~~~~~~~~

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
   needscfg_write_all = False

   # Write all configuration including defaults
   needscfg_write_all = True

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

This will write the configuration to ``${outdir}/ubproject.toml``, updating it whenever
the configuration changes.

Development Setup
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # conf.py
   extensions = [
       "sphinx_needs",
       "needs_config_writer",
   ]

   needscfg_outpath = "${srcdir}/ubproject.toml"

This configuration writes the file to the source directory, useful during development
to keep configuration in version control.

Full Configuration Export
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # conf.py
   extensions = [
       "sphinx_needs",
       "needs_config_writer",
   ]

   needscfg_write_all = True
   needscfg_outpath = "${outdir}/full_config.toml"

This exports the complete configuration including all defaults.

CI/CD Setup
~~~~~~~~~~~

.. code-block:: python

   # conf.py
   extensions = [
       "sphinx_needs",
       "needs_config_writer",
   ]

   needscfg_warn_on_diff = True
   needscfg_overwrite = False
   needscfg_outpath = "${outdir}/ubproject.toml"

This configuration emits warnings when configuration changes and prevents overwriting,
allowing you to catch unexpected configuration drift in CI/CD pipelines.

Protected Configuration Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # conf.py
   extensions = [
       "sphinx_needs",
       "needs_config_writer",
   ]

   needscfg_overwrite = False
   needscfg_outpath = "${srcdir}/ubproject.toml"

This configuration prevents overwriting an existing configuration file, useful when you
want to maintain a manually edited configuration file in version control.
