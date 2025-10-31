.. _changelog:

Changelog
=========

.. _`release:0.2.4`:

0.2.4
-----

:Released: 31.10.2025
:Full Changelog: `v0.2.3...v0.2.4 <https://github.com/useblocks/needs-config-writer/compare/0.2.3...a4160cf>`__

- ✨ Convert absolute to relative paths (:pr:`22`)

  A new configuration option :ref:`config_relative_path_fields` was added to
  specify which Sphinx-Needs configuration fields containing file paths
  should be converted to relative paths in the exported TOML file.

  Main use case are generated paths by build systems such as Bazel.

  This allows to create more portable configuration files that can be
  used across different environments or directory structures.
  Committing ``ubproject.toml`` files to Git is only possible with stable paths.

.. _`release:0.2.3`:

0.2.3
-----

:Released: 29.10.2025
:Full Changelog: `v0.2.2...v0.2.3 <https://github.com/useblocks/needs-config-writer/compare/0.2.2...7cae413>`__

- ✨ New config needscfg_exclude_defaults (:pr:`20`)

  A new configuration option :ref:`config_exclude_defaults` was added to
  control whether default Sphinx-Needs configuration values should be
  excluded from the exported TOML file.

  This allows to generate cleaner configuration files by omitting
  settings that are already at their default values.

.. _`release:0.2.2`:

0.2.2
-----

:Released: 29.10.2025
:Full Changelog: `v0.2.1...v0.2.2 <https://github.com/useblocks/needs-config-writer/compare/0.2.1...dafab78>`__

- ✨ New needscfg builder (:pr:`18`)

  A new Sphinx builder called ``needscfg`` was added to generate the
  ``ubproject.toml`` file without building the entire documentation.
  This allows to quickly generate or update the configuration file as needed.

  Additionally, the event for configuration collection was changed
  from ``config-inited`` to ``env-before-read-docs`` to ensure that the Sphinx-Needs
  configuration is fully loaded.

- 👌 Print diff (:pr:`17`)

  When configuration differs and :ref:`config_warn_on_diff` is ``True``,
  the actual differences between the existing and new configuration
  are now printed to the console for easier debugging.

.. _`release:0.2.1`:

0.2.1
-----

:Released: 28.10.2025
:Full Changelog: `v0.2.0...v0.2.1 <https://github.com/useblocks/needs-config-writer/compare/0.2.0...76b32b4>`__

This releases adds quality-of-life improvements and minor fixes.

- 📚 Restructure docs (:pr:`10` and :pr:`11`)

  A ``Motivation`` page was added to explain about problems and use-cases.
  Also an example for complex setups was added to illustrate how this extension
  can be used in real-world scenarios.

- 🔧 Return metadata in setup (:pr:`12`)

  The extension now returns metadata such as version and whether it can be run in parallel
  in the ``setup()`` call.

- 👌 New config needscfg_exclude_vars (:pr:`13`)

  A new configuration option ``needscfg_exclude_vars`` was added to customize
  which Sphinx-Needs configuration variables are excluded from the exported TOML file.
  See :ref:`excluded_configs` for details.

- ✨ Merge additional TOML files (:pr:`14`)

  A new configuration option ``needscfg_merge_toml_files`` was added to specify
  additional TOML files to merge into the exported ``ubproject.toml``.
  This allows to combine static configuration files with the dynamically generated one.

.. _`release:0.2.0`:

0.2.0
-----

:Released: 28.10.2025
:Full Changelog: `v0.1.0...v0.2.0 <https://github.com/useblocks/needs-config-writer/compare/0.1.0...e457d2f>`__

This release reduce the complexity of content comparison and improves the configuration.
It's not backwards compatible as most of the configuration changed. Please check the updated documentation.

- ♻️ Remove hash based comparison (:pr:`8`)

  The configuration ``needscfg_use_hash`` was renamed to :ref:`config_warn_on_diff`.
  Hashing is not required as the content can be compared directly.
  This is simpler with less config and less dependencies.
  Default is ``True``.

  :ref:`config_overwrite` now checks in all cases whether to overwrite differing files.
  Default is ``False`` to prevent accidental overwrites.

  The configuration ``needscfg_write_defaults`` was renamed to :ref:`config_write_all`
  to be more explicit about what it does. If enabled, all known Sphinx-Needs configuration is written,
  including defaults and not only explicitly set values.
  Default is ``False``.

  Fix sorting of ``needs_extra_options`` which maybe given as ``list[str]`` or ``list[dict]``.
  For the latter case it is sorted by the ``name`` key.

.. _`release:0.1.0`:

0.1.0
-----

:Released: 28.10.2025

Initial release of ``Needs-Config-Writer``

This version allows to write Sphinx-Needs TOML
configuration files automatically during Sphinx builds
to a customisable location.

Hash checking is supported to warn about changed configurations.
