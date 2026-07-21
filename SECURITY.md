# Security policy

## Supported versions

Security fixes target the latest released 1.x version.

## Report a vulnerability

Please use GitHub's private vulnerability reporting flow:

`https://github.com/Amal-David/polyglot/security/advisories/new`

Do not open a public issue for command execution, path traversal, unsafe hook
behavior, package-installation, or other security-sensitive findings. Include
the affected version, host, reproduction steps, impact, and any proposed
mitigation.

Language-content corrections are not security reports; use the Language
correction issue template described in [DATA.md](DATA.md).

## Extension trust

Codex, Claude Code, Pi, and Hermes plugins execute local code with the
permissions of their host process. Review this repository before enabling its
hooks or native adapters. Polyglot does not need credentials or network access
at runtime. Ambient mode is opt-in, and adapter failures are designed to leave
the agent turn unchanged.
