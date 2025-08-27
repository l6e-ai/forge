---
title: Using Memory Collections
description: Namespaced vector and text storage for agents with upsert and search helpers.
---

<!-- Imported from repo docs/memory/using-collections.md (condensed) -->

Memory collections provide namespaced vector and text storage for agents.

Common operations:

```bash
# Upsert/search within the default collection
forge memory upsert --ns <namespace> --key <key> --content "text"
forge memory search --ns <namespace> --query "q" --limit 5

# Target a specific collection in addition to the namespace
forge memory upsert --collection <collection> --ns <namespace> --key <key> --content "text"
forge memory search --collection <collection> --ns <namespace> --query "q" --limit 5
```


