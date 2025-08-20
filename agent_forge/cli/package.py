from __future__ import annotations

from pathlib import Path
from typing import Iterable
import io
import os
import zipfile
from datetime import datetime
from datetime import timezone
import hashlib
import hmac
import base64

import typer
from rich import print as rprint


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
        return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\""
    if isinstance(value, list):
        return "[" + ", ".join(_quote_toml_value(v) for v in value) + "]"
    return "\"" + str(value) + "\""


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


def _write_manifest(name: str, version: str, description: str | None, agent_cfg: dict | None) -> str:
    created = datetime.now(timezone.utc).isoformat() + "Z"
    desc = description or ""
    parts: list[str] = []
    parts.append("[metadata]")
    parts.append(f"name = \"{name}\"")
    parts.append(f"version = \"{version}\"")
    parts.append(f"description = \"{desc}\"")
    parts.append("package_format_version = \"1.0\"")
    parts.append(f"created_at = \"{created}\"")
    parts.append("")
    parts.append("[runtime]")
    parts.append("entrypoint = \"agent.py:Agent\"")
    parts.append("")
    if agent_cfg:
        parts.append(_emit_toml_from_dict("agent_config", agent_cfg).rstrip())
        parts.append("")
    return "\n".join(parts)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _compute_checksums(manifest_bytes: bytes, agent_dir: Path) -> tuple[str, list[tuple[str, str]]]:
    """Return (checksums_text, entries) where entries are (path, sha256hex)."""
    entries: list[tuple[str, str]] = []
    entries.append(("package.toml", _sha256_hex(manifest_bytes)))
    base_len = len(str(agent_dir)) + 1
    for file_path in _iter_files(agent_dir):
        with file_path.open("rb") as f:
            data = f.read()
        arcname = os.path.join("agent", str(file_path)[base_len:])
        entries.append((arcname, _sha256_hex(data)))
    lines = [f"sha256 {path} {digest}" for path, digest in entries]
    return "\n".join(lines) + "\n", entries


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
    is_hex = len(raw_text) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in raw_text)
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
        raise RuntimeError("PyNaCl is required for signing. Install with poetry group 'cli'.") from exc
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
        raise RuntimeError("PyNaCl is required for verification. Install with poetry group 'cli'.") from exc
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
    agent_path: str = typer.Argument(..., help="Path to the agent directory (contains agent.py)"),
    out_dir: str = typer.Option("dist", "--out", "-o", help="Output directory for .l6e"),
    name: str | None = typer.Option(None, "--name", help="Package name (defaults to agent dir name)"),
    version: str = typer.Option("0.1.0", "--version", "-v", help="Package version"),
    description: str | None = typer.Option(None, "--description", "-d", help="Description for manifest"),
    sign_key: str | None = typer.Option(None, "--sign-key", help="Path to Ed25519 private key to sign checksums"),
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

    manifest_text = _write_manifest(pkg_name, version, description, agent_cfg)
    manifest_bytes = manifest_text.encode("utf-8")

    try:
        # First compute checksums with manifest and agent files
        checksums_text, _ = _compute_checksums(manifest_bytes, agent_dir)
        with zipfile.ZipFile(pkg_file, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Write manifest
            zf.writestr("package.toml", manifest_bytes)
            # Write checksums
            zf.writestr("checksums.txt", checksums_text)
            # Optional signature of checksums.txt
            if sign_key:
                try:
                    key_path = Path(sign_key).expanduser().resolve()
                    sk_bytes = _read_key_bytes(key_path)
                    sig_bytes, pub_bytes = _ed25519_sign(checksums_text.encode("utf-8"), sk_bytes)
                    zf.writestr("signature.sig", _b64encode(sig_bytes))
                    zf.writestr("signature.pub", _b64encode(pub_bytes))
                    zf.writestr("signature.meta", f"algo=ed25519\nfpr={_key_fingerprint(pub_bytes)}\n")
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
    show_config: bool = typer.Option(False, "--show-config", help="Display embedded [agent_config] from manifest if present"),
    manifest_only: bool = typer.Option(False, "--manifest-only", help="Print only raw package.toml and exit (debug)"),
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
        for key in ("name", "version", "description", "package_format_version", "created_at"):
            rprint(f"  {key}: {meta.get(key, '')}")
        # Try to show checksum summary
        try:
            with zipfile.ZipFile(pkg, mode="r") as zf2:
                with zf2.open("checksums.txt") as c2:
                    lines = c2.read().decode("utf-8", errors="replace").strip().splitlines()
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
                            rprint("\n[cyan]Agent Config (from agent/config.toml)[/cyan]")
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
def install(
    package_path: str = typer.Argument(..., help="Path to .l6e file"),
    workspace: str = typer.Option(".", "--workspace", "-w", help="Workspace root (contains forge.toml and agents/)"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing agent directory if present"),
    verify: bool = typer.Option(True, "--verify/--no-verify", help="Verify checksums before install"),
    verify_sig: bool = typer.Option(False, "--verify-sig", help="Verify Ed25519 signature of checksums if present"),
    public_key: str | None = typer.Option(None, "--public-key", help="Path to Ed25519 public key (if not embedded)"),
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
                meta = tomllib.load(io.BytesIO(f.read())).get("metadata", {})
            agent_name = meta.get("name")
            if not agent_name:
                rprint("[red]Manifest missing metadata.name[/red]")
                raise typer.Exit(code=1)
            if verify:
                # Verify checksums if present
                try:
                    with zf.open("checksums.txt") as cf:
                        checks_lines = cf.read().decode("utf-8", errors="replace").splitlines()
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
                        pub_b64 = _b64encode(_read_key_bytes(Path(public_key).expanduser().resolve()))
                    if not sig_b64 or not pub_b64:
                        rprint("[red]Missing signature or public key for verification[/red]")
                        raise typer.Exit(code=1)
                    ok = _ed25519_verify(cbytes, _b64decode(sig_b64), _b64decode(pub_b64))
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
                    rprint(f"[red]Agent already exists:[/red] {target} (use --overwrite to replace)")
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
        rprint(f"[green]Installed agent to:[/green] {root / 'agents' / agent_name}")
    except Exception as exc:  # noqa: BLE001
        rprint(f"[red]Failed to install package:[/red] {exc}")
        raise typer.Exit(code=1)


def main() -> None:  # pragma: no cover
    app()



