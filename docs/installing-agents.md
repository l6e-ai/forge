# Installying l6e Agents

This guide explains how to install l6e packaged agents from a `.l6e` package file, including optional checksum and signature verification, and outlines the required dependencies such as Docker and Ollama. It also describes current manual setup requirements and notes ongoing efforts to improve the installation experience.

## Prerequisites

Before installing an l6e packaged agent, ensure your environment meets the following requirements:

- **Python 3.13** (Poetry is recommended for dependency management)
- **Node.js 18+** (only required if you plan to build a UI)
- **Ollama** (for local LLMs; must be installed manually)
- **Docker** (required to run the full stack or if the agent uses advanced features like memory)
- **l6e-forge CLI** (install via Poetry)

Official installation instructions:
- [Ollama](https://ollama.com/download)
- [Docker](https://docs.docker.com/get-docker/)

## Workspace Structure

A valid workspace must contain a `forge.toml` configuration file and an `agents/` directory. For example:

```
my-workspace/
├── forge.toml
├── agents/
│   └── my-agent/
│       ├── agent.py
│       ├── config.toml
│       └── ...
└── .forge/
```

## Installing an Agent from a `.l6e` Package

Use the l6e-forge CLI to install a packaged agent:

```bash
forge pkg install <package.l6e> \
  [--workspace|-w <workspace>] [--overwrite] \
  [--verify/--no-verify] [--verify-sig] [--public-key <path>] \
  [--install-wheels/--no-install-wheels] [--venv-path <path>]
```

- `--workspace` specifies the workspace root (default: current directory).
- `--overwrite` replaces an existing agent with the same name.
- `--verify/--no-verify` enables or disables checksum verification (enabled by default).
- `--verify-sig` enables Ed25519 signature verification of the checksums file.
- `--public-key` provides a path to the Ed25519 public key if not embedded in the package.
- `--install-wheels` installs bundled Python wheels into a virtual environment after extraction.
- `--venv-path` specifies the path for the virtual environment (defaults to `<workspace>/.venv_agents/<agent>`).

Example with checksum and signature verification:

```bash
forge pkg install my-agent-1.0.0.l6e --verify --verify-sig --public-key ./public_key.pem
```

During installation, the CLI will:
- Verify file integrity using SHA256 checksums (from `checksums.txt` in the package).
- Optionally verify the authenticity of the checksums file using Ed25519 signatures if `--verify-sig` is specified.
- Extract the agent files into the workspace's `agents/` directory.
- Optionally extract UI assets and bundled Python wheels if present in the package.
- Optionally install dependencies into a virtual environment if `--install-wheels` is used.

For more details, see the [CLI documentation](https://github.com/l6e-ai/forge/blob/a23d7609ed652edab7a9bd1d092d2effcb9f2d33/docs/cli.md).

## Setting Up Ollama and Docker

**Ollama** must be installed and running for agents that use local LLMs. The CLI will prompt you to install Ollama if it is not detected during model bootstrapping. See [Ollama's official guide](https://ollama.com/download) for installation instructions.

**Docker** is required to run the full stack (API, monitor, UI) locally, and is necessary for agents that use advanced features like memory. To start the stack, use:

```bash
poetry run forge up
```

This command starts the API, monitor, and UI services using Docker Compose. For more information, see the [getting started guide](https://github.com/l6e-ai/forge/blob/a23d7609ed652edab7a9bd1d092d2effcb9f2d33/docs/getting-started.md).

## Current Limitations and Future Improvements

At present, users must manually install and configure Ollama and Docker. The l6e-forge team is working to streamline the installation flow, including improved CLI integration and automated dependency management in future releases. For now, ensure all prerequisites are installed and configured before installing or running agents.

## Troubleshooting

- Ensure your workspace contains both `forge.toml` and an `agents/` directory.
- If checksum or signature verification fails, confirm that the `.l6e` package is complete and the correct public key is provided.
- If Docker or Ollama are not detected, verify their installation and that their respective daemons are running.

For further assistance, refer to the [l6e-forge documentation](https://github.com/l6e-ai/forge/blob/a23d7609ed652edab7a9bd1d092d2effcb9f2d33/README.md) or open an issue on the project's repository.