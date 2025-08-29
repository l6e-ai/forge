---
title: Using Namespaces and Collections
description: Organize memory with namespaces; optionally target specific backend collections when supported.
---

<!-- Imported from repo docs/memory/using-collections.md (condensed) -->

Use namespaces to organize vector and text storage per agent and purpose (e.g., short-term vs long-term). Some backends (e.g., Qdrant) also support multiple collections; you can optionally target a specific collection when upserting or searching.

Common operations:

```bash
# Upsert/search within a namespace
forge memory upsert --ns <namespace> --key <key> --content "text"
forge memory search --ns <namespace> --query "q" --limit 5

# Optionally target a specific backend collection (if supported)
forge memory upsert --collection <collection> --ns <namespace> --key <key> --content "text"
forge memory search --collection <collection> --ns <namespace> --query "q" --limit 5
```

### Bucket pattern

Treat collections as storage buckets and namespaces as logical paths. For example:

```bash
# Short-term bucket, agent-specific namespace
forge memory upsert --collection short_term --ns my-agent:notes --key 1 --content "Draft idea"
forge memory search --collection short_term --ns my-agent:notes --query "idea"

# Long-term bucket, same namespace
forge memory upsert --collection long_term --ns my-agent:notes --key 1 --content "Draft idea"
forge memory search --collection long_term --ns my-agent:notes --query "idea"
```

You can also multi-search across buckets by using the `collection::namespace` form when your backend supports it (Qdrant, InMemory):

```text
short_term::my-agent:notes
long_term::my-agent:notes
```


