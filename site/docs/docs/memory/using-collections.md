---
title: Using Memory Collections
description: Namespaced vector and text storage for agents with upsert and search helpers.
---

<!-- Imported from repo docs/memory/using-collections.md (condensed) -->

Memory collections provide namespaced vector and text storage for agents.

Common operations:

```bash
forge memory upsert --ns <namespace> --key <key> --content "text"
forge memory search --ns <namespace> --query "q" --limit 5
```


