# Packaging & Signing l6e Agents

The l6e-forge CLI provides a flexible and powerful way to package agents for distribution. The main command for packaging is `build` under the `package` CLI group. This command creates a `.l6e` package from an agent directory, bundling code, dependencies, UI assets, and optional cryptographic signatures for integrity verification. 

### Basic Usage

```bash
forge package build /path/to/agent \
  --out dist \
  --name myagent \
  --version 1.0.0 \
  --description "My agent description"
```

The above command packages the agent located at `/path/to/agent`, outputs the package to the `dist` directory, and sets the name, version, and description in the manifest.

### CLI Options Reference

#### General Options

- `agent_path` (argument): Path to the agent directory (must contain `agent.py`).
- `--out`, `-o`: Output directory for the `.l6e` package (default: `dist`).
- `--name`: Package name (defaults to agent directory name).
- `--version`, `-v`: Package version (default: `0.1.0`).
- `--description`, `-d`: Description for the package manifest.

#### Package Profile

- `--profile`: Package profile, controls included artifacts. Options: `thin`, `medium`, `fat` (default: `thin`).

#### Compose Overlay

- `--include-compose`: Include a minimal compose overlay in the package.
- `--compose-services`: Comma-separated list of services to include in compose, or `auto` to infer from agent config.

#### Wheel Inclusions

- `--requirements`: Path to a `requirements.txt` to include in the package.
- `--bundle-wheels/--no-bundle-wheels`: Include a wheelhouse built from requirements for offline install.
- `--poetry-config/--no-poetry-config`: Generate requirements from `pyproject.toml` via `poetry export` if `--requirements` is not provided.
- `--poetry-root`: Directory to run `poetry export` in (defaults to agent directory if auto-detected).

**Example: Bundle dependencies as wheels for offline installation**
```bash
forge package build /path/to/agent \
  --bundle-wheels \
  --requirements /path/to/requirements.txt
```
If you use Poetry, you can omit `--requirements` and use `--poetry-config`:
```bash
forge package build /path/to/agent \
  --bundle-wheels \
  --poetry-config \
  --poetry-root /path/to/poetry/project
```

#### UI Inclusions

You can include a UI in your agent package either from a local directory or from a git repository.

- `--ui-dir`: Path to a local UI project (will be packaged under `artifacts/ui`).
- `--ui-build/--no-ui-build`: Run UI build (`npm ci && npm run build`) before packaging.
- `--ui-dist`: Relative path of build output within `--ui-dir` (default: `dist`).

**Example: Include a locally built UI**
```bash
forge package build /path/to/agent \
  --ui-dir /path/to/ui \
  --ui-build \
  --ui-dist dist
```

- `--ui-git`: Git URL to fetch UI from (preferred over `--ui-dir` if provided).
- `--ui-ref`: Git ref (branch, tag, or commit) for `--ui-git` (default: `main`).
- `--ui-subdir`: Optional subdirectory within the cloned repo for the UI project.
- `--ui-git-ssh-key`: Path to SSH private key for cloning (sets `GIT_SSH_COMMAND`).
- `--ui-git-insecure-host/--no-ui-git-insecure-host`: Disable strict host key checking for git clone.
- `--ui-git-username`: Basic auth username for HTTPS git clone.
- `--ui-git-password`: Basic auth password for HTTPS git clone (or pass token here).
- `--ui-git-token`: Personal access token for HTTPS git clone (used as password; username can be anything).

**Example: Include a UI from a git repository**
```bash
forge package build /path/to/agent \
  --ui-git https://github.com/example/ui-repo.git \
  --ui-ref main \
  --ui-subdir frontend \
  --ui-build \
  --ui-dist dist
```

If both `--ui-dir` and `--ui-git` are provided, the UI will be fetched from git.

#### Default Forge UI Inclusion

If no UI is specified via `--ui-dir` or `--ui-git`, no UI assets are included by default. To include the default Forge UI, you must provide its location explicitly using the above options.

#### Key Signature Verification

To ensure package authenticity and integrity, you can sign your package using an Ed25519 private key. This signs the `checksums.txt` file, which contains SHA256 checksums for all package files. The signature and public key are included in the package as `signature.sig`, `signature.pub`, and `signature.meta`.

**Signing a package**
```bash
forge package build /path/to/agent \
  --sign-key /path/to/ed25519_private.key
```

The private key file can be in hex or base64 format. The CLI uses the PyNaCl library for signing.

**Verifying a package signature (during install)**
```bash
forge package install /path/to/package.l6e \
  --verify-sig \
  --public-key /path/to/ed25519_public.key
```

If the public key is embedded in the package, you may omit `--public-key`.

**Key Generation Example (using PyNaCl in Python)**
```python
from nacl.signing import SigningKey
sk = SigningKey.generate()
with open("ed25519_private.key", "wb") as f:
    f.write(sk.encode())
with open("ed25519_public.key", "wb") as f:
    f.write(sk.verify_key.encode())
```

### Manifest and Artifacts

The package manifest (`package.toml`) includes metadata, runtime entrypoint, agent config, artifacts metadata, and optional compose metadata. All included files (agent code, UI assets, wheels, requirements) are listed in the manifest and checksummed for integrity verification.

### Packaging Scenarios

**Minimal agent package**
```bash
forge package build /path/to/agent
```

**Agent with bundled wheels and UI**
```bash
forge package build /path/to/agent \
  --bundle-wheels \
  --requirements /path/to/requirements.txt \
  --ui-dir /path/to/ui \
  --ui-build
```

**Agent with compose overlay and signature**
```bash
forge package build /path/to/agent \
  --include-compose \
  --sign-key /path/to/ed25519_private.key
```

### Installation Guide

For instructions on installing `.l6e` agent packages, see the installation guide (TODO: link to installation guide).

---

For further details, refer to the [l6e-forge CLI source code](https://github.com/l6e-ai/forge/blob/main/l6e_forge/cli/package.py).
