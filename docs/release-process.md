# Windows Release Process

This repository publishes the packaged Windows executable through GitHub Releases instead of storing the `.exe` in normal Git history.

The executable is large because the desktop app embeds `PySide6 QtWebEngine`, so the packaged binary exceeds GitHub's standard `100 MB` Git object limit.

## When To Run This

Run this process when meaningful application changes affect:

- `dvrs_tool/`
- `dvrs_tool/static/`
- `run_desktop.py`
- `dvrs_tool/desktop.py`
- `dvrs_desktop.spec`
- `requirements-desktop.txt`
- `requirements.txt`
- `build_windows.ps1`

Run the documentation portion of this process when release-ready changes affect:

- `docs/salesperson-user-guide.md`
- `docs/salesperson-quick-reference.md`
- `tools/generate_sales_doc_pdfs.py`
- user-facing workflow, inputs, outputs, statuses, or escalation guidance that should be reflected in the sales handoff documents

## Local Release Checklist

1. Verify the source tree is ready.

```powershell
git status
python run_tests.py
```

2. Regenerate the sales PDF handoff documents when needed.

```powershell
python .\tools\generate_sales_doc_pdfs.py
```

If the release includes user-facing workflow or documentation changes, confirm that these companion files are current and ready to travel alongside the executable:

- `docs\salesperson-user-guide.pdf`
- `docs\salesperson-quick-reference.pdf`

3. Rebuild the Windows package.

```powershell
.\build_windows.ps1 -Clean
```

The build script now writes to versioned output folders derived from the application version in `dvrs_tool/api.py`. For example, version `0.1.2` builds to `dist-release-012\DVRSPlanner.exe` and uses `build-release-012\` for the PyInstaller work tree.

If `-Clean` cannot remove the matching versioned build or dist folder after its retry loop, the script stops and reports that the current versioned output is locked. In that case:

- close the process holding the lock and rerun the build, or
- supply a new version tag in the code before rebuilding so the script targets a new versioned output folder

The script also now fails fast when `pip install` or `PyInstaller` returns a nonzero exit code.

4. Smoke-test the packaged executable.

```powershell
.\dist-release-012\DVRSPlanner.exe
```

Confirm the app opens cleanly before continuing.

5. Commit and push the source changes.

```powershell
git add -A
git commit -m "Describe the release-ready source change"
git push origin main
```

6. Create the release tag on the intended release commit and verify it before publishing.

```powershell
git tag -a v0.1.2 -m "DVRS Planner 0.1.2"
git push origin v0.1.2
git rev-list -n 1 v0.1.2
git ls-remote --tags origin v0.1.2 v0.1.2^{}
```

Confirm that:

- the local tag points to the intended release commit
- the remote tag exists before you create the GitHub Release
- the `^{}` peeled commit shown by `git ls-remote` matches the release-prep commit you intend to publish

Do not rely on `gh release create` to create the tag automatically. If the tag does not already exist on GitHub, GitHub can create it from the current branch tip instead of the intended release commit.

7. Publish the GitHub Release and verify the published metadata.

```powershell
gh release create v0.1.2 .\dist-release-012\DVRSPlanner.exe --title "DVRS Planner 0.1.2" --notes "Windows desktop release 0.1.2"
gh release view v0.1.2
git ls-remote --tags origin v0.1.2 v0.1.2^{}
```

Confirm that the published release shows the expected:

- tag: `v0.1.2`
- title: `DVRS Planner 0.1.2`
- asset: `DVRSPlanner.exe`

If the tag already exists and the release already exists, update the release asset instead:

```powershell
gh release upload v0.1.2 .\dist-release-012\DVRSPlanner.exe --clobber
gh release view v0.1.2
```

## Codex Prompt Sequence

Editors using Codex can use the following prompts directly.

### Prompt 1: Prepare the release build

```text
Regenerate the sales PDF documents if needed, rebuild the Windows desktop package for this repo, run the tests, smoke-test the packaged executable, and tell me if the release artifact and companion user documents are ready for publication. This is DVRS Planner version 0.1.2.
```

### Prompt 2: Commit and push the source changes

```text
Stage, commit, and push the pending source, workflow, documentation, generated sales PDF, and packaging-script changes for the 0.1.2 Windows release, but do not commit the built executable into Git.
```

### Prompt 3: Publish the GitHub Release

```text
Create or update the GitHub Release for DVRS Planner 0.1.2 using the built file at dist-release-012/DVRSPlanner.exe. Create and push the annotated tag first, confirm the remote tag exists and points to the intended release commit before publishing, then summarize the exact tag, title, asset, and final remote tag target that were published.
```

## Notes For Editors

- The local release build artifact is the versioned executable path such as `dist-release-012\DVRSPlanner.exe`, not a normal Git-tracked file.
- The salesperson-facing PDF handoff files under `docs\` are intended to be Git-tracked companion documents when they are updated for a release.
- If the release changes what a salesperson sees or tells a customer, regenerate the sales PDFs and include them in the normal source commit so the release-ready documentation matches the executable.
- A Windows release is not complete until both the remote tag and the GitHub Release page have been verified after publication.
- Prefer an annotated tag created locally and pushed explicitly before running `gh release create`.
- If `gh` is affected by the local proxy wrapper rules in this repo, use:

```powershell
.\gh-safe.ps1 release view v0.1.2
.\gh-safe.ps1 release create v0.1.2 .\dist-release-012\DVRSPlanner.exe --title "DVRS Planner 0.1.2" --notes "Windows desktop release 0.1.2"
```

- If you need to replace an already-published executable for the same tag, use `gh release upload --clobber`.
- If GitHub created the tag on the wrong commit because the tag was missing when the release was created, correct the remote tag deliberately and then rerun the verification commands before calling the release complete.
- The build script currently derives the versioned output suffix from the version string in `dvrs_tool/api.py`. If the repo later adds a dedicated version module, update `build_windows.ps1` and this release playbook to use that shared source of truth instead.
