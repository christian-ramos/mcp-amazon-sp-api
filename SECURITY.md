# Security Policy

## Reporting a Vulnerability

**Please do not file public issues for security vulnerabilities.**

If you find a security issue in this project, report it privately via [GitHub Private Vulnerability Reporting](https://github.com/christian-ramos/mcp-amazon-sp-api/security/advisories/new).

Include as much detail as possible:

- A description of the issue and its potential impact
- Steps to reproduce
- Affected versions or commits
- Any mitigations or workarounds you have identified

You can expect an initial acknowledgement within 7 days. Triage, fix and disclosure timelines depend on severity.

## Supported Versions

Only the latest commit on `master` is actively supported. Fixes are not backported to older releases.

## Scope

This project wraps the Amazon Selling Partner API and stores production credentials locally. Security-sensitive areas include:

- Credential handling (`config.py`, `.env` loading, macOS Keychain integration)
- Write tools that mutate listings, prices, feeds or buyer messages
- The MCP transport layer (stdio)

Vulnerability reports related to upstream SDKs (`python-amazon-sp-api`, `mcp[cli]`) should be filed directly with those projects.

## Out of Scope

- Issues that require physical access to the user's machine
- Self-XSS or social engineering of the user
- Anything that depends on an attacker already having the user's `.env` file or refresh token

## Disclosure

We follow coordinated disclosure. Once a fix is available, we will publish a GitHub Security Advisory with credit to the reporter (unless anonymity is requested).
