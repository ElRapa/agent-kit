# Global agent rules

Rules for every project and every harness. Projects add their own AGENTS.md on top.

- Links to something running on this machine (a preview, a dashboard): give a Tailscale link
  (`tailscale serve --bg --https=<port> <port>`), never `localhost`, and open it once yourself first.
- Notes: read only the vault in `$AP_VAULT` (the loaded context's vault). Never copy content between vaults.
- Secrets: never print, log or commit a key. Ask for it by name; it lives in the keychain.
- Paths: use `~/…` or repo-relative paths, never `/Users/<name>/…`.
