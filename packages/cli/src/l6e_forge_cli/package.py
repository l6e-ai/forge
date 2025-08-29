from __future__ import annotations

from pathlib import Path
from typing import Iterable
import io
import os
import zipfile
from datetime import datetime
from datetime import timezone
import hashlib
import base64
import shutil
import tempfile
import subprocess
from urllib.parse import urlparse, urlunparse, quote
from rich.table import Table

import typer
from rich import print as rprint
from l6e_forge.infra.compose import ComposeTemplateService, ComposeServiceSpec


app = typer.Typer(help="Package (.l6e) commands")


def _iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file():
            # Skip common junk
            parts = set(p.parts)
            if any(x in parts for x in {".git", "__pycache__", ".venv", "venv"}):
                continue
            yield p


def _quote_toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(value, list):
        return "[" + ", ".join(_quote_toml_value(v) for v in value) + "]"
    return '"' + str(value) + '"'


def _emit_toml_from_dict(root_table: str, data: dict) -> str:
    lines: list[str] = []

    def emit(prefix: list[str], obj: object) -> None:
        if isinstance(obj, dict):
            scalars: dict[str, object] = {}
            tables: dict[str, dict] = {}
            for k, v in obj.items():
                if isinstance(v, dict):
                    tables[k] = v
                else:
                    scalars[k] = v
            if prefix:
                lines.append("[" + ".".join(prefix) + "]")
            for k, v in scalars.items():
                lines.append(f"{k} = {_quote_toml_value(v)}")
            if scalars and tables:
                lines.append("")
            for k, v in tables.items():
                emit(prefix + [k], v)
        else:
            return

    emit([root_table], data)
    return "\n".join(lines) + ("\n" if lines else "")


def _write_manifest(
    name: str,
    version: str,
    description: str | None,
    agent_cfg: dict | None,
    artifacts: dict | None = None,
    compose_meta: dict | None = None,
) -> str:
    created = datetime.now(timezone.utc).isoformat() + "Z"
    desc = description or ""
    parts: list[str] = []
    parts.append("[metadata]")
    parts.append(f'name = "{name}"')
    parts.append(f'version = "{version}"')
    parts.append(f'description = "{desc}"')
    parts.append('package_format_version = "1.0"')
    parts.append(f'created_at = "{created}"')
    parts.append("")
    parts.append("[runtime]")
    parts.append('entrypoint = "agent.py:Agent"')
    parts.append("")
    if agent_cfg:
        parts.append(_emit_toml_from_dict("agent_config", agent_cfg).rstrip())
        parts.append("")
    if artifacts:
        parts.append(_emit_toml_from_dict("artifacts", artifacts).rstrip())
        parts.append("")
    if compose_meta:
        parts.append(_emit_toml_from_dict("compose", compose_meta).rstrip())
        parts.append("")
    return "\n".join(parts)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _compute_checksums(
    manifest_bytes: bytes,
    agent_dir: Path,
    extra_files: list[tuple[str, bytes]] | None = None,
) -> tuple[str, list[tuple[str, str]]]:
    """Return (checksums_text, entries) where entries are (path, sha256hex)."""
    entries: list[tuple[str, str]] = []
    entries.append(("package.toml", _sha256_hex(manifest_bytes)))
    base_len = len(str(agent_dir)) + 1
    for file_path in _iter_files(agent_dir):
        with file_path.open("rb") as f:
            data = f.read()
        arcname = os.path.join("agent", str(file_path)[base_len:])
        entries.append((arcname, _sha256_hex(data)))
    # Include extra artifacts (e.g., compose, requirements, wheels placeholder)
    if extra_files:
        for arcname, content in extra_files:
            entries.append((arcname, _sha256_hex(content)))
    lines = [f"sha256 {path} {digest}" for path, digest in entries]
    return "\n".join(lines) + "\n", entries


async def _generate_compose_yaml(services: list[str]) -> str:
    svc = ComposeTemplateService()
    specs = [ComposeServiceSpec(name=s, context={}) for s in services]
    return await svc.generate(specs)


# ==============================
# Ed25519 signing / verification
# ==============================


def _b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64decode(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def _read_key_bytes(path: Path) -> bytes:
    raw_text = path.read_text(encoding="utf-8").strip()
    # Prefer hex if it looks like hex
    is_hex = len(raw_text) % 2 == 0 and all(
        c in "0123456789abcdefABCDEF" for c in raw_text
    )
    if is_hex:
        try:
            return bytes.fromhex(raw_text)
        except Exception:
            pass
    # Try strict base64
    try:
        import base64 as _b64

        return _b64.b64decode(raw_text.encode("ascii"), validate=True)
    except Exception:
        pass
    # Fallback: read raw bytes
    return path.read_bytes()


def _ed25519_sign(data: bytes, private_key_bytes: bytes) -> tuple[bytes, bytes]:
    try:
        from nacl.signing import SigningKey  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "PyNaCl is required for signing. Install with poetry group 'cli'."
        ) from exc
    sk = SigningKey(private_key_bytes)
    signed = sk.sign(data)
    sig = signed.signature
    pub = sk.verify_key.encode()
    return sig, pub


def _ed25519_verify(data: bytes, signature: bytes, public_key_bytes: bytes) -> bool:
    try:
        from nacl.signing import VerifyKey  # type: ignore
        from nacl.exceptions import BadSignatureError  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "PyNaCl is required for verification. Install with poetry group 'cli'."
        ) from exc
    vk = VerifyKey(public_key_bytes)
    try:
        vk.verify(data, signature)
        return True
    except BadSignatureError:
        return False


def _key_fingerprint(public_key_bytes: bytes) -> str:
    return hashlib.sha256(public_key_bytes).hexdigest()[:40]


@app.command()
def build(
    agent_path: str = typer.Argument(
        ..., help="Path to the agent directory (contains agent.py)"
    ),
    out_dir: str = typer.Option(
        "dist", "--out", "-o", help="Output directory for .l6e"
    ),
    name: str | None = typer.Option(
        None, "--name", help="Package name (defaults to agent dir name)"
    ),
    version: str = typer.Option("0.1.0", "--version", "-v", help="Package version"),
    description: str | None = typer.Option(
        None, "--description", "-d", help="Description for manifest"
    ),
    sign_key: str | None = typer.Option(
        None, "--sign-key", help="Path to Ed25519 private key to sign checksums"
    ),
    profile: str = typer.Option(
        "thin", "--profile", help="Package profile: thin | medium | fat"
    ),
    include_compose: bool = typer.Option(
        False, "--include-compose", help="Include a minimal compose overlay in package"
    ),
    compose_services: str = typer.Option(
        "auto",
        "--compose-services",
        help="Comma-separated services to include in compose or 'auto' to infer",
    ),
    requirements: str | None = typer.Option(
        None,
        "--requirements",
        help="Path to requirements.txt to include (for fat or bundling)",
    ),
    bundle_wheels: bool = typer.Option(
        False,
        "--bundle-wheels/--no-bundle-wheels",
        help="Include a wheelhouse built from requirements.txt for offline install",
    ),
    poetry_config: bool = typer.Option(
        False,
        "--poetry-config/--no-poetry-config",
        help="Generate requirements from pyproject via 'poetry export' when --requirements is not provided",
    ),
    poetry_root: str | None = typer.Option(
        None,
        "--poetry-root",
        help="Directory to run 'poetry export' in (defaults to agent dir when auto-detected)",
    ),
    ui_dir: str | None = typer.Option(
        None,
        "--ui-dir",
        help="Path to a UI project (will be packaged under artifacts/ui)",
    ),
    ui_build: bool = typer.Option(
        False,
        "--ui-build/--no-ui-build",
        help="Run UI build (npm ci && npm run build) before packaging",
    ),
    ui_dist: str = typer.Option(
        "dist", "--ui-dist", help="Relative path of build output within --ui-dir"
    ),
    ui_git: str | None = typer.Option(
        None,
        "--ui-git",
        help="Git URL to fetch UI from (prefered over --ui-dir if provided)",
    ),
    ui_ref: str = typer.Option(
        "main", "--ui-ref", help="Git ref (branch|tag|commit) for --ui-git"
    ),
    ui_subdir: str | None = typer.Option(
        None,
        "--ui-subdir",
        help="Optional subdirectory within the cloned repo for the UI project",
    ),
    ui_git_ssh_key: str | None = typer.Option(
        None,
        "--ui-git-ssh-key",
        help="Path to SSH private key for cloning (sets GIT_SSH_COMMAND)",
    ),
    ui_git_insecure_host: bool = typer.Option(
        False,
        "--ui-git-insecure-host/--no-ui-git-insecure-host",
        help="Disable strict host key checking for git clone",
    ),
    ui_git_username: str | None = typer.Option(
        None, "--ui-git-username", help="Basic auth username for HTTPS git clone"
    ),
    ui_git_password: str | None = typer.Option(
        None,
        "--ui-git-password",
        help="Basic auth password for HTTPS git clone (or pass token here)",
    ),
    ui_git_token: str | None = typer.Option(
        None,
        "--ui-git-token",
        help="Personal access token for HTTPS git clone (used as password; username can be anything)",
    ),
    prompts_dir: str | None = typer.Option(
        None,
        "--prompts-dir",
        help="Path to a directory of prompt templates to include under artifacts/prompts",
    ),
) -> None:
    """Create a minimal public .l6e from an agent directory."""
    agent_dir = Path(agent_path).expanduser().resolve()
    if not agent_dir.exists() or not agent_dir.is_dir():
        rprint(f"[red]Agent path not found or not a directory:[/red] {agent_dir}")
        raise typer.Exit(code=1)
    if not (agent_dir / "agent.py").exists():
        rprint(f"[red]agent.py not found in:[/red] {agent_dir}")
        raise typer.Exit(code=1)

    pkg_name = name or agent_dir.name
    out = Path(out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    pkg_file = out / f"{pkg_name}-{version}.l6e"

    # Load agent config (if present) to embed in manifest
    agent_cfg: dict | None = None
    cfg_path = agent_dir / "config.toml"
    if cfg_path.exists():
        try:
            import tomllib as _tomllib

            with cfg_path.open("rb") as _f:
                agent_cfg = _tomllib.load(_f) or {}
            if not description:
                try:
                    _desc = agent_cfg.get("agent", {}).get("description")  # type: ignore[assignment]
                    if isinstance(_desc, str):
                        description = _desc
                except Exception:
                    pass
        except Exception:
            agent_cfg = None

    artifacts_meta: dict | None = None
    compose_meta: dict | None = None
    extras: list[tuple[str, bytes]] = []

    # Validate wheel bundling input early (auto-detect poetry if not provided)
    poetry_root_for_export: Path | None = None
    if bundle_wheels and not (requirements or poetry_config or poetry_root):
        # Only auto-detect Poetry if pyproject.toml exists in the agent directory itself
        if (agent_dir / "pyproject.toml").exists():
            poetry_config = True
            poetry_root_for_export = agent_dir
            rprint(
                f"[cyan]Using Poetry project at agent dir:[/cyan] {poetry_root_for_export}"
            )
        else:
            rprint(
                "[red]--bundle-wheels requires --requirements or a Poetry project (use --poetry-config)\n[yellow]Tip:[/yellow] Provide --requirements or run in an agent with its own pyproject.toml."
            )
            raise typer.Exit(code=1)
    if poetry_root:
        p = Path(poetry_root).expanduser().resolve()
        if not (p / "pyproject.toml").exists():
            rprint(f"[red]--poetry-root does not contain pyproject.toml:[/red] {p}")
            raise typer.Exit(code=1)
        poetry_config = True
        poetry_root_for_export = p
    if requirements:
        req_path_check = Path(requirements).expanduser().resolve()
        if not req_path_check.exists():
            rprint(f"[red]Requirements file not found:[/red] {req_path_check}")
            raise typer.Exit(code=1)

    # Optional compose overlay
    if include_compose:

        def _infer_services_from_config(cfg: dict | None) -> list[str]:
            inferred: list[str] = []
            if not cfg:
                return ["monitor"]
            try:
                # Memory provider
                mem = cfg.get("memory", {})
                mem_provider = (mem or {}).get("provider")
                if isinstance(mem_provider, str):
                    if mem_provider.lower() == "qdrant":
                        inferred.append("qdrant")
                    elif mem_provider.lower() == "redis":
                        inferred.append("redis")
                # Model provider
                model = cfg.get("model", {})
                mod_provider = (model or {}).get("provider")
                if isinstance(mod_provider, str) and mod_provider.lower() == "ollama":
                    inferred.append("ollama")
            except Exception:
                pass
            # Always include monitor for local dev stacks
            if "monitor" not in inferred:
                inferred.append("monitor")
            return inferred

        if compose_services.strip().lower() == "auto":
            svcs = _infer_services_from_config(agent_cfg)
        else:
            svcs = [s.strip() for s in compose_services.split(",") if s.strip()]
        # Render asynchronously
        import asyncio as _asyncio

        compose_yaml = _asyncio.run(_generate_compose_yaml(svcs))
        extras.append(("compose/stack.yaml", compose_yaml.encode("utf-8")))
        compose_meta = {"file": "compose/stack.yaml", "services": svcs}

    # Optional artifacts metadata
    artifacts_meta = {"profile": profile}
    # Include requirements.txt (provided or exported via poetry)
    temp_req_path: Path | None = None
    req_path_for_wheels: Path | None = None
    if requirements:
        req_path = Path(requirements).expanduser().resolve()
        if req_path.exists():
            extras.append(("artifacts/requirements.txt", req_path.read_bytes()))
            artifacts_meta["requirements"] = "artifacts/requirements.txt"
            req_path_for_wheels = req_path
    elif poetry_config:
        # Attempt to export requirements from poetry
        try:
            import shutil as _shutil

            if _shutil.which("poetry") is None:
                rprint(
                    "[red]Poetry is not installed or not on PATH. Install Poetry or pass --requirements.[/red]"
                )
                raise typer.Exit(code=1)
            proc = subprocess.run(
                ["poetry", "export", "-f", "requirements.txt", "--without-hashes"],
                cwd=str(poetry_root_for_export or agent_dir),
                capture_output=True,
                check=True,
                text=False,
            )
            exported = proc.stdout or b""
            if not exported.strip():
                rprint("[red]poetry export produced no output[/red]")
                raise typer.Exit(code=1)
            extras.append(("artifacts/requirements.txt", exported))
            artifacts_meta["requirements"] = "artifacts/requirements.txt"
            # Write to temp file for wheel download step
            temp_dir = Path(tempfile.mkdtemp(prefix="req_export_"))
            temp_req_path = temp_dir / "requirements.txt"
            temp_req_path.write_bytes(exported)
            req_path_for_wheels = temp_req_path
        except subprocess.CalledProcessError as exc:  # type: ignore[name-defined]
            stderr = (exc.stderr or b"").decode("utf-8", errors="replace")
            rprint(
                f"[red]Failed to export requirements via poetry (exit {exc.returncode}):[/red]\n{stderr}"
            )
            raise typer.Exit(code=1)
        except Exception as exc:  # noqa: BLE001
            rprint(f"[red]Failed to export requirements via poetry:[/red] {exc}")
            raise typer.Exit(code=1)
    # Optional wheel bundling (wheelhouse)
    if bundle_wheels and req_path_for_wheels:
        wheel_tmp = Path(tempfile.mkdtemp(prefix="wheelhouse_"))
        try:
            # Use pip download to collect wheels/sdists; prefer wheels where possible
            cmd = [
                "python",
                "-m",
                "pip",
                "download",
                "-r",
                str(req_path_for_wheels),
                "-d",
                str(wheel_tmp),
                "--only-binary=:all:",
            ]
            subprocess.run(cmd, check=False)
            # Fallback: allow sdists if wheels not available
            if not any(wheel_tmp.iterdir()):
                subprocess.run(
                    [
                        "python",
                        "-m",
                        "pip",
                        "download",
                        "-r",
                        str(req_path_for_wheels),
                        "-d",
                        str(wheel_tmp),
                    ],
                    check=False,
                )
            wheel_files = list(wheel_tmp.iterdir())
            if wheel_files:
                for wf in wheel_files:
                    if wf.is_file():
                        arcname = os.path.join("artifacts", "wheels", wf.name)
                        extras.append((arcname, wf.read_bytes()))
                artifacts_meta["wheels"] = "artifacts/wheels"
        finally:
            try:
                if temp_req_path and temp_req_path.exists():
                    shutil.rmtree(temp_req_path.parent, ignore_errors=True)
                shutil.rmtree(wheel_tmp, ignore_errors=True)
            except Exception:
                pass

    # Optional Prompt templates packaging
    if prompts_dir:
        pr_dir = Path(prompts_dir).expanduser().resolve()
        if pr_dir.exists() and pr_dir.is_dir():
            base_len_pr = len(str(pr_dir)) + 1
            count_prompts = 0
            for p in pr_dir.rglob("*"):
                if p.is_file():
                    arcname = os.path.join("artifacts", "prompts", str(p)[base_len_pr:])
                    extras.append((arcname, p.read_bytes()))
                    count_prompts += 1
            if count_prompts:
                artifacts_meta["prompts"] = "artifacts/prompts"
        else:
            rprint(
                f"[yellow]Prompts dir not found or not a directory:[/yellow] {pr_dir}"
            )

    # Optional UI packaging from git (preferred) or local directory
    def _package_ui_from_path(root: Path) -> None:
        if ui_build:
            try:
                subprocess.run(
                    [
                        "bash",
                        "-lc",
                        f"cd '{root}' && npm ci --no-audit --no-fund && npm run build",
                    ],
                    check=False,
                )
            except Exception as exc:  # noqa: BLE001
                rprint(f"[yellow]UI build command failed:[/yellow] {exc}")
        dist_dir_path = root / ui_dist
        if dist_dir_path.exists() and dist_dir_path.is_dir():
            base_len_ui = len(str(dist_dir_path)) + 1
            for p in dist_dir_path.rglob("*"):
                if p.is_file():
                    arcname = os.path.join("artifacts", "ui", str(p)[base_len_ui:])
                    extras.append((arcname, p.read_bytes()))
            artifacts_meta["ui_dir"] = "artifacts/ui"
        else:
            rprint(f"[yellow]UI dist directory not found:[/yellow] {dist_dir_path}")

    if ui_git:
        tmp_repo = Path(tempfile.mkdtemp(prefix="ui_repo_"))
        try:
            # Shallow clone
            # If HTTPS and credentials provided, embed them in the URL to avoid interactive prompts
            clone_url = ui_git
            try:
                parsed = urlparse(ui_git)
                if parsed.scheme in ("http", "https"):
                    if ui_git_token:
                        user = quote(ui_git_username or "oauth2")
                        pwd = quote(ui_git_token)
                        netloc = f"{user}:{pwd}@{parsed.hostname or ''}"
                        if parsed.port:
                            netloc += f":{parsed.port}"
                        clone_url = urlunparse(
                            (
                                parsed.scheme,
                                netloc,
                                parsed.path,
                                parsed.params,
                                parsed.query,
                                parsed.fragment,
                            )
                        )
                    elif ui_git_username and ui_git_password:
                        user = quote(ui_git_username)
                        pwd = quote(ui_git_password)
                        netloc = f"{user}:{pwd}@{parsed.hostname or ''}"
                        if parsed.port:
                            netloc += f":{parsed.port}"
                        clone_url = urlunparse(
                            (
                                parsed.scheme,
                                netloc,
                                parsed.path,
                                parsed.params,
                                parsed.query,
                                parsed.fragment,
                            )
                        )
            except Exception:
                pass

            clone_cmd = [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                ui_ref,
                clone_url,
                str(tmp_repo),
            ]
            env = os.environ.copy()
            # Disable interactive terminal prompts (fail fast if creds missing)
            env["GIT_TERMINAL_PROMPT"] = "0"
            if ui_git_ssh_key or ui_git_insecure_host:
                ssh_parts = ["ssh"]
                if ui_git_ssh_key:
                    ssh_parts += ["-i", ui_git_ssh_key, "-o", "IdentitiesOnly=yes"]
                if ui_git_insecure_host:
                    ssh_parts += [
                        "-o",
                        "StrictHostKeyChecking=no",
                        "-o",
                        "UserKnownHostsFile=/dev/null",
                    ]
                env["GIT_SSH_COMMAND"] = " ".join(ssh_parts)
            subprocess.run(clone_cmd, check=False, env=env)
            repo_ui_root: Path = tmp_repo
            if ui_subdir:
                repo_ui_root = tmp_repo / ui_subdir
            if not repo_ui_root.exists():
                rprint(f"[yellow]UI subdir not found in repo:[/yellow] {repo_ui_root}")
            else:
                _package_ui_from_path(repo_ui_root)
                artifacts_meta["ui_git"] = {
                    "url": ui_git,
                    "ref": ui_ref,
                    "subdir": ui_subdir or "",
                }
        finally:
            try:
                shutil.rmtree(tmp_repo, ignore_errors=True)
            except Exception:
                pass
    elif ui_dir:
        ui_root = Path(ui_dir).expanduser().resolve()
        if not ui_root.exists() or not ui_root.is_dir():
            rprint(
                f"[yellow]UI directory not found or not a directory:[/yellow] {ui_root}"
            )
        else:
            _package_ui_from_path(ui_root)

    manifest_text = _write_manifest(
        pkg_name, version, description, agent_cfg, artifacts_meta, compose_meta
    )
    manifest_bytes = manifest_text.encode("utf-8")

    try:
        # First compute checksums with manifest and agent files
        checksums_text, _ = _compute_checksums(manifest_bytes, agent_dir, extras)
        with zipfile.ZipFile(
            pkg_file, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as zf:
            # Write manifest
            zf.writestr("package.toml", manifest_bytes)
            # Write checksums
            zf.writestr("checksums.txt", checksums_text)
            # Write extras
            for arcname, content in extras:
                zf.writestr(arcname, content)
            # Optional signature of checksums.txt
            if sign_key:
                try:
                    key_path = Path(sign_key).expanduser().resolve()
                    sk_bytes = _read_key_bytes(key_path)
                    sig_bytes, pub_bytes = _ed25519_sign(
                        checksums_text.encode("utf-8"), sk_bytes
                    )
                    zf.writestr("signature.sig", _b64encode(sig_bytes))
                    zf.writestr("signature.pub", _b64encode(pub_bytes))
                    zf.writestr(
                        "signature.meta",
                        f"algo=ed25519\nfpr={_key_fingerprint(pub_bytes)}\n",
                    )
                except Exception as exc:  # noqa: BLE001
                    rprint(f"[red]Signing failed:[/red] {exc}")
                    raise typer.Exit(code=1)
            # Include agent files under agent/
            base_len = len(str(agent_dir)) + 1
            for file_path in _iter_files(agent_dir):
                arcname = os.path.join("agent", str(file_path)[base_len:])
                zf.write(file_path, arcname)
        rprint(f"[green]Built package:[/green] {pkg_file}")
    except Exception as exc:  # noqa: BLE001
        rprint(f"[red]Failed to build package:[/red] {exc}")
        raise typer.Exit(code=1)


@app.command()
def inspect(
    package_path: str = typer.Argument(..., help="Path to .l6e file"),
    show_config: bool = typer.Option(
        False,
        "--show-config",
        help="Display embedded [agent_config] from manifest if present",
    ),
    manifest_only: bool = typer.Option(
        False, "--manifest-only", help="Print only raw package.toml and exit (debug)"
    ),
) -> None:
    """Display basic metadata from a .l6e package."""
    pkg = Path(package_path).expanduser().resolve()
    if not pkg.exists():
        rprint(f"[red]Package not found:[/red] {pkg}")
        raise typer.Exit(code=1)
    try:
        import tomllib

        with zipfile.ZipFile(pkg, mode="r") as zf:
            with zf.open("package.toml") as f:
                raw_bytes = f.read()
                if manifest_only:
                    # Print raw TOML and exit
                    typer.echo(raw_bytes.decode("utf-8", errors="replace"))
                    return
                data = tomllib.load(io.BytesIO(raw_bytes))
        meta = data.get("metadata", {})
        rprint("[cyan]Package Metadata[/cyan]")
        for key in (
            "name",
            "version",
            "description",
            "package_format_version",
            "created_at",
        ):
            rprint(f"  {key}: {meta.get(key, '')}")
        # Try to show checksum summary
        try:
            with zipfile.ZipFile(pkg, mode="r") as zf2:
                with zf2.open("checksums.txt") as c2:
                    lines = (
                        c2.read().decode("utf-8", errors="replace").strip().splitlines()
                    )
                    rprint(f"[cyan]Checksums[/cyan] ({len(lines)} entries)")
        except Exception:
            pass
        if show_config:
            cfg = data.get("agent_config")
            if cfg:
                rprint("\n[cyan]Agent Config[/cyan]")
                toml_text = _emit_toml_from_dict("agent_config", cfg)
                for line in toml_text.strip().splitlines():
                    typer.echo(line)
            else:
                # Fallback: try to read agent/config.toml from the archive
                try:
                    with zipfile.ZipFile(pkg, mode="r") as zf2:
                        with zf2.open("agent/config.toml") as f2:
                            import tomllib as _tomllib2

                            parsed = _tomllib2.load(io.BytesIO(f2.read()))
                            rprint(
                                "\n[cyan]Agent Config (from agent/config.toml)[/cyan]"
                            )
                            toml_text = _emit_toml_from_dict("agent_config", parsed)
                            for line in toml_text.strip().splitlines():
                                typer.echo(line)
                except Exception:
                    rprint("[yellow]No agent_config found in manifest[/yellow]")
    except KeyError:
        rprint("[red]package.toml missing in archive[/red]")
        raise typer.Exit(code=1)
    except Exception as exc:  # noqa: BLE001
        rprint(f"[red]Failed to inspect package:[/red] {exc}")
        raise typer.Exit(code=1)


@app.command()
def contents(
    package_path: str = typer.Argument(..., help="Path to .l6e file"),
    tree: bool = typer.Option(True, "--tree/--no-tree", help="Show archive contents"),
    limit: int = typer.Option(
        0, "--limit", help="Limit number of displayed entries (0 = all)"
    ),
    stats: bool = typer.Option(True, "--stats/--no-stats", help="Show size statistics"),
    artifacts: bool = typer.Option(
        True, "--artifacts/--no-artifacts", help="Show artifacts summary"
    ),
) -> None:
    """List files contained in a .l6e bundle and summarize artifacts."""
    pkg = Path(package_path).expanduser().resolve()
    if not pkg.exists():
        rprint(f"[red]Package not found:[/red] {pkg}")
        raise typer.Exit(code=1)
    try:
        with zipfile.ZipFile(pkg, mode="r") as zf:
            names = zf.namelist()
            if tree:
                tbl = Table(title="Archive Contents")
                tbl.add_column("Path")
                tbl.add_column("Size (KB)")
                tbl.add_column("Compressed (KB)")
                count = 0
                total_size = 0
                total_csize = 0
                for info in zf.infolist():
                    # skip directories
                    if info.is_dir() or info.filename.endswith("/"):
                        continue
                    total_size += int(info.file_size or 0)
                    total_csize += int(info.compress_size or 0)
                    if limit and count >= limit:
                        continue
                    tbl.add_row(
                        info.filename,
                        f"{(info.file_size or 0) / 1024:.1f}",
                        f"{(info.compress_size or 0) / 1024:.1f}",
                    )
                    count += 1
                rprint(tbl)
                if limit and count < (
                    len(
                        [
                            i
                            for i in zf.infolist()
                            if not (i.is_dir() or i.filename.endswith("/"))
                        ]
                    )
                ):
                    rprint(
                        f"[yellow]Showing first {count} files (use --limit 0 for all).[/yellow]"
                    )
                if stats:
                    rprint(
                        f"[cyan]Sizes[/cyan] total={total_size / 1024 / 1024:.2f} MB, compressed={total_csize / 1024 / 1024:.2f} MB"
                    )

            if artifacts:
                has_ui = any(n.startswith("artifacts/ui/") for n in names)
                has_prompts = any(n.startswith("artifacts/prompts/") for n in names)
                has_wheels = any(n.startswith("artifacts/wheels/") for n in names)
                ui_count = sum(
                    1
                    for n in names
                    if n.startswith("artifacts/ui/") and not n.endswith("/")
                )
                wheel_files = [
                    n
                    for n in names
                    if n.startswith("artifacts/wheels/") and n.endswith(".whl")
                ]
                rprint("\n[cyan]Artifacts Summary[/cyan]")
                rprint(f"  UI: {'present' if has_ui else 'absent'}  files={ui_count}")
                rprint(f"  Prompts: {'present' if has_prompts else 'absent'}")
                rprint(
                    f"  Wheels: {'present' if has_wheels else 'absent'}  count={len(wheel_files)}"
                )
                if wheel_files and (not limit or limit > 0):
                    show = wheel_files[: min(10, len(wheel_files))]
                    for w in show:
                        rprint(f"    - {w.split('/')[-1]}")
                    if len(wheel_files) > len(show):
                        rprint(f"    (+{len(wheel_files) - len(show)} more)")
    except Exception as exc:  # noqa: BLE001
        rprint(f"[red]Failed to read contents:[/red] {exc}")
        raise typer.Exit(code=1)


@app.command()
def install(
    package_path: str = typer.Argument(..., help="Path to .l6e file"),
    workspace: str = typer.Option(
        ".",
        "--workspace",
        "-w",
        help="Workspace root (contains forge.toml and agents/)",
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite existing agent directory if present"
    ),
    verify: bool = typer.Option(
        True, "--verify/--no-verify", help="Verify checksums before install"
    ),
    verify_sig: bool = typer.Option(
        False, "--verify-sig", help="Verify Ed25519 signature of checksums if present"
    ),
    public_key: str | None = typer.Option(
        None, "--public-key", help="Path to Ed25519 public key (if not embedded)"
    ),
    install_wheels: bool = typer.Option(
        False,
        "--install-wheels/--no-install-wheels",
        help="Install bundled wheels into a venv after extraction",
    ),
    venv_path: str | None = typer.Option(
        None,
        "--venv-path",
        help="Path to create/use a virtual environment for installing wheels (defaults to <workspace>/.venv_agents/<agent>)",
    ),
) -> None:
    """Install a package into a workspace's agents directory."""
    pkg = Path(package_path).expanduser().resolve()
    root = Path(workspace).expanduser().resolve()
    if not (root / "forge.toml").exists() or not (root / "agents").exists():
        rprint(f"[red]Not a workspace (missing forge.toml or agents/):[/red] {root}")
        raise typer.Exit(code=1)
    try:
        import tomllib

        with zipfile.ZipFile(pkg, mode="r") as zf:
            # Read manifest for name
            with zf.open("package.toml") as f:
                pkg_data = tomllib.load(io.BytesIO(f.read()))
            meta = pkg_data.get("metadata", {})
            artifacts_section = pkg_data.get("artifacts", {})
            agent_name = meta.get("name")
            if not agent_name:
                rprint("[red]Manifest missing metadata.name[/red]")
                raise typer.Exit(code=1)
            if verify:
                # Verify checksums if present
                try:
                    with zf.open("checksums.txt") as cf:
                        checks_lines = (
                            cf.read().decode("utf-8", errors="replace").splitlines()
                        )
                    for line in checks_lines:
                        parts = line.strip().split()
                        if len(parts) != 3 or parts[0] != "sha256":
                            continue
                        _, path, expected = parts
                        with zf.open(path) as rf:
                            actual = hashlib.sha256(rf.read()).hexdigest()
                        if actual != expected:
                            rprint(f"[red]Checksum mismatch for {path}[/red]")
                            raise typer.Exit(code=1)
                    rprint("[green]Checksum verification passed[/green]")
                except KeyError:
                    # No checksums.txt; proceed
                    pass
            if verify_sig:
                # Verify signature against checksums.txt
                try:
                    with zf.open("checksums.txt") as cf:
                        cbytes = cf.read()
                    sig_b64 = None
                    pub_b64 = None
                    try:
                        with zf.open("signature.sig") as sf:
                            sig_b64 = sf.read().decode("utf-8").strip()
                        with zf.open("signature.pub") as pf:
                            pub_b64 = pf.read().decode("utf-8").strip()
                    except KeyError:
                        pass
                    if public_key and not pub_b64:
                        pub_b64 = _b64encode(
                            _read_key_bytes(Path(public_key).expanduser().resolve())
                        )
                    if not sig_b64 or not pub_b64:
                        rprint(
                            "[red]Missing signature or public key for verification[/red]"
                        )
                        raise typer.Exit(code=1)
                    ok = _ed25519_verify(
                        cbytes, _b64decode(sig_b64), _b64decode(pub_b64)
                    )
                    if not ok:
                        rprint("[red]Signature verification failed[/red]")
                        raise typer.Exit(code=1)
                    rprint("[green]Signature verification passed[/green]")
                except Exception as exc:  # noqa: BLE001
                    rprint(f"[red]Signature verification error:[/red] {exc}")
                    raise typer.Exit(code=1)
            target = root / "agents" / agent_name
            if target.exists():
                if not overwrite:
                    rprint(
                        f"[red]Agent already exists:[/red] {target} (use --overwrite to replace)"
                    )
                    raise typer.Exit(code=1)
            else:
                target.mkdir(parents=True, exist_ok=True)

            # Extract agent/** into target
            for info in zf.infolist():
                if not info.filename.startswith("agent/"):
                    continue
                rel = info.filename[len("agent/") :]
                if not rel:
                    continue
                dest = target / rel
                if info.is_dir() or info.filename.endswith("/"):
                    dest.mkdir(parents=True, exist_ok=True)
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info.filename) as src, dest.open("wb") as dst:
                    dst.write(src.read())
            # Optionally extract UI assets to workspace-level directory
            try:
                has_ui = any(n.startswith("artifacts/ui/") for n in zf.namelist())
                if has_ui:
                    ui_root = root / "ui" / str(agent_name)
                    for info in zf.infolist():
                        if not info.filename.startswith("artifacts/ui/"):
                            continue
                        rel = info.filename[len("artifacts/ui/") :]
                        if not rel:
                            continue
                        dest = ui_root / rel
                        if info.is_dir() or info.filename.endswith("/"):
                            dest.mkdir(parents=True, exist_ok=True)
                            continue
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(info.filename) as src, dest.open("wb") as dst:
                            dst.write(src.read())
                    rprint(f"[green]Extracted UI assets to:[/green] {ui_root}")
                    rprint(
                        "[cyan]To serve UI via API, set AF_UI_DIR to this path or mount it in compose (defaults to /app/static/ui in compose template).[/cyan]"
                    )
            except Exception:
                pass
            # Optionally extract prompts to workspace-level directory
            try:
                has_prompts = any(
                    n.startswith("artifacts/prompts/") for n in zf.namelist()
                )
                if has_prompts:
                    prompts_root = root / "prompts" / str(agent_name)
                    for info in zf.infolist():
                        if not info.filename.startswith("artifacts/prompts/"):
                            continue
                        rel = info.filename[len("artifacts/prompts/") :]
                        if not rel:
                            continue
                        dest = prompts_root / rel
                        if info.is_dir() or info.filename.endswith("/"):
                            dest.mkdir(parents=True, exist_ok=True)
                            continue
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(info.filename) as src, dest.open("wb") as dst:
                            dst.write(src.read())
                    rprint(
                        f"[green]Extracted prompt templates to:[/green] {prompts_root}"
                    )
            except Exception:
                pass
            # Optionally extract wheels to workspace and (optionally) install into a venv
            try:
                has_wheels = any(
                    n.startswith("artifacts/wheels/") for n in zf.namelist()
                )
                wheelhouse_dir = None
                if has_wheels:
                    wheelhouse_dir = root / "wheels" / str(agent_name)
                    for info in zf.infolist():
                        if not info.filename.startswith("artifacts/wheels/"):
                            continue
                        rel = info.filename[len("artifacts/wheels/") :]
                        if not rel:
                            continue
                        dest = wheelhouse_dir / rel
                        if info.is_dir() or info.filename.endswith("/"):
                            dest.mkdir(parents=True, exist_ok=True)
                            continue
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(info.filename) as src, dest.open("wb") as dst:
                            dst.write(src.read())
                    rprint(
                        f"[green]Extracted wheel bundle to:[/green] {wheelhouse_dir}"
                    )
                # Install wheels if requested
                if install_wheels and wheelhouse_dir and wheelhouse_dir.exists():
                    # Resolve requirements file if present (inside package)
                    req_rel = artifacts_section.get("requirements")
                    req_tmp_path = None
                    if isinstance(req_rel, str):
                        try:
                            with zf.open(req_rel) as rf:
                                req_bytes = rf.read()
                            req_tmp_path = (
                                root / "wheels" / str(agent_name) / "requirements.txt"
                            )
                            req_tmp_path.parent.mkdir(parents=True, exist_ok=True)
                            req_tmp_path.write_bytes(req_bytes)
                        except Exception:
                            req_tmp_path = None
                    # Create or use venv
                    venv_dir = (
                        Path(venv_path).expanduser().resolve()
                        if venv_path
                        else (root / ".venv_agents" / str(agent_name))
                    )
                    if not venv_dir.exists():
                        rprint(f"[cyan]Creating virtual environment:[/cyan] {venv_dir}")
                        subprocess.run(
                            ["python", "-m", "venv", str(venv_dir)], check=False
                        )
                    bin_dir = "Scripts" if os.name == "nt" else "bin"
                    python_exe = (
                        venv_dir
                        / bin_dir
                        / ("python.exe" if os.name == "nt" else "python")
                    )
                    subprocess.run(
                        [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"],
                        check=False,
                    )
                    if req_tmp_path and req_tmp_path.exists():
                        cmd = [
                            str(python_exe),
                            "-m",
                            "pip",
                            "install",
                            "--no-index",
                            "--find-links",
                            str(wheelhouse_dir),
                            "-r",
                            str(req_tmp_path),
                        ]
                        rprint(
                            "[cyan]Installing from requirements with wheelhouse...[/cyan]"
                        )
                        subprocess.run(cmd, check=False)
                    else:
                        wheels = [str(p) for p in wheelhouse_dir.glob("*.whl")]
                        if wheels:
                            cmd = [
                                str(python_exe),
                                "-m",
                                "pip",
                                "install",
                                "--no-index",
                                "--find-links",
                                str(wheelhouse_dir),
                            ] + wheels
                            rprint("[cyan]Installing wheel files...[/cyan]")
                            subprocess.run(cmd, check=False)
                    rprint(
                        f"[green]Dependencies installed into venv:[/green] {venv_dir}"
                    )
            except Exception as exc:  # noqa: BLE001
                rprint(
                    f"[yellow]Wheel extraction/installation skipped or errored:[/yellow] {exc}"
                )
        rprint(f"[green]Installed agent to:[/green] {root / 'agents' / agent_name}")
    except Exception as exc:  # noqa: BLE001
        rprint(f"[red]Failed to install package:[/red] {exc}")
        raise typer.Exit(code=1)


def main() -> None:  # pragma: no cover
    app()
