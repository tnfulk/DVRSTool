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

## Local Release Checklist

1. Verify the source tree is ready.

```powershell
git status
python run_tests.py
```

2. Rebuild the Windows package.

```powershell
.\build_windows.ps1 -Clean
```

3. Smoke-test the packaged executable.

```powershell
.\dist-release\DVRSPlanner.exe
```

Confirm the app opens cleanly before continuing.

4. Commit and push the source changes.

```powershell
git add -A
git commit -m "Describe the release-ready source change"
git push origin main
```

5. Create the release tag and publish the GitHub Release.

```powershell
git tag v0.1.0
git push origin v0.1.0
gh release create v0.1.0 .\dist-release\DVRSPlanner.exe --title "DVRS Planner 0.1.0" --notes "Windows desktop release 0.1.0"
```

If the tag already exists, update the release asset instead:

```powershell
gh release upload v0.1.0 .\dist-release\DVRSPlanner.exe --clobber
```

## Codex Prompt Sequence

Editors using Codex can use the following prompts directly.

### Prompt 1: Prepare the release build

```text
Rebuild the Windows desktop package for this repo, run the tests, smoke-test the packaged executable, and tell me if the release artifact is ready for publication. This is DVRS Planner version 0.1.0.
```

### Prompt 2: Commit and push the source changes

```text
Stage, commit, and push the pending source, workflow, documentation, and packaging-script changes for the 0.1.0 Windows release, but do not commit the built executable into Git.
```

### Prompt 3: Publish the GitHub Release

```text
Create or update the GitHub Release for DVRS Planner 0.1.0 using the built file at dist-release/DVRSPlanner.exe, and summarize the exact tag, title, and asset that were published.
```

## Notes For Editors

- `dist-release/DVRSPlanner.exe` is a local build artifact and release asset, not a normal Git-tracked file.
- If `gh` is affected by the local proxy wrapper rules in this repo, use:

```powershell
.\gh-safe.ps1 release create v0.1.0 .\dist-release\DVRSPlanner.exe --title "DVRS Planner 0.1.0" --notes "Windows desktop release 0.1.0"
```

- If you need to replace an already-published executable for the same tag, use `gh release upload --clobber`.
