# Security Policy

## Supported versions

Best Seller Studio uses `MAJOR.MINOR` versioning. Security fixes are applied to the latest minor of the current major version.

| Version | Supported |
|---------|-----------|
| V4.2.x  | ✅ current |
| V4.1.x  | ⚠️ critical fixes only |
| V4.0.x  | ⚠️ critical fixes only |
| < V4.0  | ❌ end of life |

## Reporting a vulnerability

**Do not open a public issue for security reports.**

If you find a vulnerability — in the agent prompts, the install scripts, the file I/O contracts, or anywhere else in the pipeline that could compromise a user's system, credentials, or work — please report it privately:

1. Open a private [GitHub Security Advisory](https://github.com/felipelobomotta-blip/book-genesis-studio/security/advisories/new), OR
2. Message the maintainer through the email on the GitHub profile.

**What to include:**
- Version affected
- Steps to reproduce (agent config, input brief, observed behavior)
- Impact assessment (data leak, remote code, credential exposure, etc.)
- Suggested fix if you have one

## Response timeline

- **Acknowledgement:** within 72 hours
- **Initial assessment:** within 7 days
- **Fix or mitigation:** within 30 days for high/critical severity; scheduled for the next minor release for medium/low
- **Public disclosure:** coordinated with the reporter after the fix ships

## What is in scope

- Agent instructions that could be prompt-injected into performing destructive filesystem or shell actions
- Install scripts (`install.sh`, `install.ps1`) and the installer (`runner/`) moving, overwriting or deleting files outside the skills and agents folders it manages
- Instructions that make an agent run a second tool (the cross-family critic recipes) with more access than reading the packet it is given
- File I/O contracts that could leak the user's OS-level secrets or credentials
- Third-party dependencies (the Remotion demo, the landing page's CDN script) if they introduce supply-chain risk

## What is out of scope

- Model behavior of Claude/Codex/Kimi/Antigravity itself (report to the respective vendor)
- User-reported "the book was bad" — that is a quality issue, not security
- Cost of long runs (bounded by three revision passes per gate; a quality issue, not a security bug)

## Hall of fame

Contributors who report valid vulnerabilities are credited by name in the release notes of the fixing version, unless they request anonymity.
