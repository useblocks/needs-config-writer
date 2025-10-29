needs-config-writer
===================

Sphinx-Needs can be fully configured via ``conf.py``, but can also load configuration from a
``ubproject.toml`` file. This file can be created and updated automatically via the
``needs-config-writer`` Sphinx extension.

Many Sphinx projects want to generate a part of the Sphinx-Needs configuration automatically.
Tools like ubCode / ubc require a declarative format to ingest configuration.
This extension tries to bridge the gap between Sphinx's dynamic Python configuration and
the need for a static configuration file.

The extension provides:

- Automatic generation during documentation builds via the ``env-before-read-docs`` event.
- A dedicated ``needscfg`` builder for standalone configuration file generation.

**Contents**

.. toctree::
   :maxdepth: 2

   motivation
   configuration
   behavior

.. toctree::
   :maxdepth: 1
   :caption: Development

   changelog
   contributing
