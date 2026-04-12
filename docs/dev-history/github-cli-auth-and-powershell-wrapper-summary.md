# GitHub CLI Authentication And PowerShell Wrapper Setup

## 1. Context
This thread focused on improving local GitHub tooling for the `DVRSTool` repository so Codex could better support branch, push, pull request, and GitHub inspection workflows. The work was done on Windows in a PowerShell-based development environment that already had `git` configured and a GitHub remote pointing to `tnfulk/DVRSTool`.

## 2. Problem Statement
The local environment did not have GitHub CLI (`gh`) installed, which limited Codex's ability to assist with GitHub-native operations such as authentication checks, push-related workflows, current-branch PR discovery, and GitHub Actions log inspection. After installing `gh`, a second problem appeared: API calls failed because the Codex process injected invalid proxy environment variables pointing to `127.0.0.1:9`. PowerShell profile loading was also blocked by the machine's default execution-policy behavior, which prevented a simpler auto-wrapper approach from working initially.

## 3. Key Decisions
- Decision: Install GitHub CLI using `winget` and the official `GitHub.cli` package.
  Rationale: `winget` was already available on the machine, while `choco` and `scoop` were not. Using the official package kept installation simple and aligned with the Windows environment.
  Alternatives considered (if any): Other Windows package managers were checked but not available.

- Decision: Use GitHub CLI mainly for the gaps not covered cleanly by the GitHub connector.
  Rationale: The plugin guidance in this environment is connector-first for structured PR, issue, label, comment, and repository metadata. `gh` is most useful here for auth, push, branch/PR workflows, current-branch PR discovery, and Actions logs.
  Alternatives considered (if any): None adopted; the connector-first model remained the primary approach.

- Decision: Authenticate `gh` with the browser/device flow over HTTPS.
  Rationale: This is the least-friction setup on Windows and aligns `gh` with the existing HTTPS Git remote.
  Alternatives considered (if any): None were needed after the user approved the browser/device login path.

- Decision: Create a repo-local wrapper script, `gh-safe.ps1`, that clears proxy variables only for the lifetime of a single `gh` command.
  Rationale: The invalid proxy values were present only in the current process environment, not in global Git config or WinHTTP settings. A narrow wrapper avoided changing broader machine networking configuration while making `gh` reliable inside Codex.
  Alternatives considered (if any): Re-authenticating `gh` was tested implicitly but did not solve the proxy issue; changing system proxy settings was unnecessary because they were not the source of the problem.

- Decision: Add a PowerShell profile function named `gh` that delegates to the repo-local wrapper when the current directory is inside this repository, and otherwise falls back to the installed `gh.exe`.
  Rationale: The user requested a simpler workflow. This preserved normal `gh` behavior elsewhere while making this repository work transparently.
  Alternatives considered (if any): Continuing to invoke `.\gh-safe.ps1 ...` manually was functional but less convenient.

- Decision: Set the current-user PowerShell execution policy to `RemoteSigned`.
  Rationale: The newly created profile could not load under the default restrictive behavior. `RemoteSigned` was the smallest practical change that allowed local profile scripts while still protecting downloaded scripts.
  Alternatives considered (if any): Leaving the profile disabled would have forced continued manual wrapper usage.

## 4. Implementation Summary
The thread first verified that `gh` was not installed and that `git` was present. It confirmed that `winget` was available and then installed GitHub CLI version `2.89.0` from the official `GitHub.cli` package. The CLI was authenticated successfully as `tnfulk` using the browser/device login flow with HTTPS Git operations.

Follow-up verification exposed failing API access caused by process-level proxy environment variables (`HTTP_PROXY`, `HTTPS_PROXY`, and related lowercase variants) pointing at `http://127.0.0.1:9`. A repo-local script, `gh-safe.ps1`, was added to temporarily clear those proxy variables, invoke the installed `gh.exe`, and restore the prior process environment afterward. `README.md` was updated with a short usage section showing how to use that wrapper.

To simplify usage further, a new PowerShell profile was created at `C:\Users\k1ld4\OneDrive\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`. It defines a `gh` function that routes through `gh-safe.ps1` only when the current working directory is inside `DVRSTool`; otherwise it calls the installed GitHub CLI directly. Because the profile initially failed to load under the default policy, the thread set `CurrentUser` execution policy to `RemoteSigned` and then re-verified that plain `gh auth status` and `gh repo view tnfulk/DVRSTool` worked from a fresh PowerShell session.

## 5. Challenges & Iterations
- After installation, `gh` was not immediately available in the current shell `PATH`, so the installed executable path was used directly for authentication.
- `gh auth status` initially reported an invalid token because API requests were being routed through a broken proxy configuration inherited from the Codex process, not because authentication had actually failed.
- An attempt to set the repo default with `gh repo set-default tnfulk/DVRSTool` failed due to a `.git/config` lock/permission issue, so that step was treated as optional and not required for core functionality.
- The first attempt to validate the PowerShell-profile approach failed because profile scripts were blocked by execution policy. This was corrected by setting `RemoteSigned` for the current user and then testing in a fresh shell.
- A JSON-field verification command for `gh repo view` had quoting issues in PowerShell, so verification was simplified to a plain `gh repo view tnfulk/DVRSTool` call.

## 6. Final Outcome
The machine now has GitHub CLI installed and authenticated as `tnfulk`. Within this repository, `gh` can be used normally from new PowerShell sessions without manually clearing proxy variables or invoking the wrapper script by name. The repository also contains a documented fallback wrapper, `gh-safe.ps1`, for explicit use or troubleshooting.

## 7. Open Questions / Follow-ups
- The cause of the invalid proxy variables inside the Codex process was identified, but this thread did not change the parent environment that injects them.
- `gh repo set-default tnfulk/DVRSTool` was not made persistent because `.git/config` could not be locked for writing during the attempt.
- The PowerShell profile lives outside the repository, so future environment rebuilds may need that profile recreated if the machine or OneDrive-backed shell configuration changes.

## 8. Affected Files / Components
- `gh-safe.ps1`
- `README.md`
- `docs/dev-history/github-cli-auth-and-powershell-wrapper-summary.md`
- `docs/raw-threads/github-cli-auth-and-powershell-wrapper.md`
- `docs/dev-log.md`
- `C:\Users\k1ld4\OneDrive\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`
- Windows PowerShell `CurrentUser` execution policy
- GitHub CLI installation (`GitHub.cli` via `winget`)
