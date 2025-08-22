# Welcome to l6e-forge

l6e forge is a work in progress. The goal of l6e-forge is to allow you to easily deploy completely local AI agent stacks. Giving you true ownership and control of what you build, and where your agent's data lives.

With the increasing availability of VRAM in Apple's unified memory architecture, and better OSS LLM models becoming available everyday, it is now entirely possible to run multi-hundred billion parameter models on your local machine. This means true data-ownership is possible, and fully private-local agents (like your own Jarvis) are now possible.

l6e forge's goal is to enable OSS development of agents without the headaches of configuring an environment for every agent you want to make.

l6e forge can be used with non-local agent's as well, either utilize an existing API implementation like [OpenAI](./l6e_forge/model_providers/openai.py) or implement your own version of the [base client](./l6e_forge/model_providers/base.py). If you do feel free to make a PR! Check out our contributing docs for more information: (./CONTRIBUTING.md).


## Dev Monitoring UI

- When running dev mode via `forge dev`, a lightweight monitoring UI starts at `http://localhost:8123/`.
- It shows active agents, chat logs, and basic performance metrics in real time.

### Docker

- To run only the monitoring UI via Docker:

```bash
docker compose up monitor
```


### Packaging

Example full package
```bash
poetry run forge pkg build examples/example-workspace/agents/test-demo -o examples/example-workspace/dist --ui-git git@github.com:l6e-ai/forge.git --ui-ref main --ui-subdir site/agent-ui --ui-build --ui-dist /examples/example-workspace/dist --ui-git-ssh-key ~/.ssh/$GITHUB_SSH_KEY --bundle-wheels
```
