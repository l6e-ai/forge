---
sidebar_position: 5
title: Inspecting Packages
description: Use inspect and contents to view manifests, configs, and artifacts in `.l6e` packages.
---

<!-- Adapted from repo docs/inspecting-l6e-packages.md -->

Use `inspect` and `contents` to debug `.l6e` packages.

## Inspect Metadata

```bash
forge pkg inspect <package.l6e>
forge pkg inspect <package.l6e> --show-config
forge pkg inspect <package.l6e> --manifest-only
```

## View Contents

```bash
forge pkg contents <package.l6e> [--tree] [--limit 10] [--stats] [--artifacts]
```

Helpful to confirm UI assets and wheels are present before install.


