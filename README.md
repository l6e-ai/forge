# Welcome to agent-forge

Agent Forge is a work in progress. The goal of agent-forge is to allow you to easily deploy completely local AI agent stacks. Giving you true ownership and control of what you build, and where your agent's data lives.

With the increasing availability of VRAM in Apple's unified memory architecture, and better OSS LLM models becoming available everyday, it is now entirely possible to run multi-hundred billion parameter models on your local machine. This means true data-ownership is possible, and fully private-local agents (like your own Jarvis) are now possible.

Agent Forge's goal is to enable OSS development of agents without the headaches of configuring an environment for every agent you want to make.

Agent Forge can be used with non-local agent's as well, either utilize an existing API implementation like [OpenAI](./agent_forge/model_providers/openai.py) or implement your own version of the [base client](./agent_forge/model_providers/base.py). If you do feel free to make a PR! Check out our contributing docs for more information: (./CONTRIBUTING.md).

