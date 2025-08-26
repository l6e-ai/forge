# Inspecting & Debugging `.l6e` Agent Packages

This document provides an overview of how to use the `inspect` and `contents` CLI commands to assist with debugging package building and installations in Forge. It is intended to complement the existing installation and packaging documentation by focusing on workflows for viewing and validating packages before installation, and for troubleshooting during package creation or export.

The `inspect` and `contents` commands are designed to help you catch issues early, confirm package structure, and share package details with your team.

## Inspecting Package Metadata

Use `forge pkg inspect` to display metadata and configuration embedded in a `.l6e` package file. This command is especially useful for verifying package details before installation, checking the manifest during development, and confirming exported packages for your team.

**Basic usage:**
```bash
forge pkg inspect <package.l6e>
```

This prints key metadata fields such as name, version, description, package format version, and creation date. It also attempts to summarize the checksums included in the package, which helps verify integrity.

**Show embedded agent config:**
```bash
forge pkg inspect <package.l6e> --show-config
```
This option displays the `[agent_config]` section from the manifest if present, or attempts to read `agent/config.toml` from the archive. Use this to confirm that agent configuration is correctly embedded in the package.

**Debug manifest issues:**
```bash
forge pkg inspect <package.l6e> --manifest-only
```
This prints the raw `package.toml` manifest, which is useful for troubleshooting manifest formatting or content problems during package building.

See the [CLI documentation](https://github.com/l6e-ai/forge/blob/a23d7609ed652edab7a9bd1d092d2effcb9f2d33/docs/cli.md) for more details.

## Viewing Package Contents

Use `forge pkg contents` to list files inside a `.l6e` package and summarize included artifacts. This command helps you inspect the internal structure of a package before installation, verify that all expected files and artifacts are present, and debug issues during package export.

**Basic usage:**
```bash
forge pkg contents <package.l6e>
```
This displays a table of file paths, sizes, and compressed sizes for all files in the package.

**Show as a tree or flat list:**
```bash
forge pkg contents <package.l6e> --tree
forge pkg contents <package.l6e> --no-tree
```
The default is tree view; use `--no-tree` for a flat list.

**Limit displayed entries:**
```bash
forge pkg contents <package.l6e> --limit 10
```
Shows only the first 10 files, which is useful for large packages.

**Show size statistics:**
```bash
forge pkg contents <package.l6e> --stats
forge pkg contents <package.l6e> --no-stats
```
Displays total and compressed size statistics.

**Summarize artifacts:**
```bash
forge pkg contents <package.l6e> --artifacts
forge pkg contents <package.l6e> --no-artifacts
```
Shows a summary of UI files and Python wheels included in the package, helping you confirm that all necessary build outputs are present.

See the [CLI documentation](https://github.com/l6e-ai/forge/blob/a23d7609ed652edab7a9bd1d092d2effcb9f2d33/docs/cli.md) for option details.

## Recommended Workflows

During package development, use `inspect` to verify that your manifest and agent configuration are correct before installation. Use `contents` to confirm that all required files and artifacts are present in the package, and to check size and structure before sharing or deploying.

When exporting packages for your team, run both commands to generate a summary of package contents and metadata. Share this output to help others understand what is included and to catch potential issues before installation.

If you encounter installation problems, use `inspect` to check for manifest or configuration errors, and `contents` to verify that all expected files are present.

For more information on building and installing packages, refer to the installation and packaging documentation. The `inspect` and `contents` commands bridge the gap between these workflows by providing visibility into package internals and metadata at every stage of development and deployment.