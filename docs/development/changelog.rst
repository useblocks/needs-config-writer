.. _changelog:

Changelog
=========

..
   .. _unreleased:

   Unreleased
   ----------

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
