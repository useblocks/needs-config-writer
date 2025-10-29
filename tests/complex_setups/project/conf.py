project = "Basic Project"

extensions = ["sphinx_needs", "needs_config_writer"]

needs_from_toml = "../generated_config/ubproject.toml"
needs_schema_definitions_from_json = "../generated_config/schemas.json"
needs_import_keys = {"dep1": "../generated_deps/needs_test.json"}

needscfg_outpath = "ubproject.toml"
"""Write to this directory."""

needscfg_overwrite = True
"""Any changes to the shared/local configuration shall update the generated config file."""

needscfg_write_all = True
"""Write full config, so the final configuration is visible in one file."""

needscfg_warn_on_diff = True
"""Be sure to update this - running Sphinx with -W will fail the CI, that's wanted."""

needscfg_exclude_defaults = True
"""Do not write default values into the generated config file."""
