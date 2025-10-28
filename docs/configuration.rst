Configuration
=============

The ``needs-config-writer`` extension provides several configuration options to control how
Sphinx-Needs configuration is exported to ``ubproject.toml``.

All configuration options are set in your Sphinx ``conf.py`` file.

.. _`config_outpath`:

needscfg_outpath
----------------

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
---------------------

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
------------------

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
------------------

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

Examples
--------

Minimal setup
~~~~~~~~~~~~~

.. code-block:: python

   # conf.py
   extensions = [
       "sphinx_needs",
       "needs_config_writer",
   ]

This will write the configuration to ``${outdir}/ubproject.toml``, updating it whenever
the configuration changes. The file contents can be manually copied over to a new primary
``ubproject.toml`` to migrate existing conf.py configuration.

Development setup
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # conf.py
   extensions = [
       "sphinx_needs",
       "needs_config_writer",
   ]

   needscfg_outpath = "ubproject.toml"
   needscfg_overwrite = True
   needscfg_warn_on_diff = False

This configuration writes the file to the directory holding the ``conf.py`` file,
useful during development to keep configuration in version control.
Allow overwriting as the original is version controlled. Any diffs will show up.

Full configuration export
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

CI/CD setup
~~~~~~~~~~~

.. code-block:: python

   # conf.py
   extensions = [
       "sphinx_needs",
       "needs_config_writer",
   ]

   needscfg_warn_on_diff = True
   needscfg_overwrite = False
   needscfg_outpath = "ubproject.toml"

This configuration emits warnings when configuration changes and prevents overwriting,
allowing you to catch unexpected configuration drift in CI/CD pipelines.
