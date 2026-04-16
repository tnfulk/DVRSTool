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

4. Smoke-test the packaged executable.

```powershell
.\dist-release\DVRSPlanner.exe
```

Confirm the app opens cleanly before continuing.

5. Commit and push the source changes.

```powershell
git add -A
git commit -m "Describe the release-ready source change"
git push origin main
```

6. Create the release tag and publish the GitHub Release.

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
Regenerate the sales PDF documents if needed, rebuild the Windows desktop package for this repo, run the tests, smoke-test the packaged executable, and tell me if the release artifact and companion user documents are ready for publication. This is DVRS Planner version 0.1.0.
```

### Prompt 2: Commit and push the source changes

```text
Stage, commit, and push the pending source, workflow, documentation, generated sales PDF, and packaging-script changes for the 0.1.0 Windows release, but do not commit the built executable into Git.
```

### Prompt 3: Publish the GitHub Release

```text
Create or update the GitHub Release for DVRS Planner 0.1.0 using the built file at dist-release/DVRSPlanner.exe, and summarize the exact tag, title, and asset that were published.
```

## Notes For Editors

- `dist-release/DVRSPlanner.exe` is a local build artifact and release asset, not a normal Git-tracked file.
- The salesperson-facing PDF handoff files under `docs\` are intended to be Git-tracked companion documents when they are updated for a release.
- If the release changes what a salesperson sees or tells a customer, regenerate the sales PDFs and include them in the normal source commit so the release-ready documentation matches the executable.
- If `gh` is affected by the local proxy wrapper rules in this repo, use:

```powershell
.\gh-safe.ps1 release create v0.1.0 .\dist-release\DVRSPlanner.exe --title "DVRS Planner 0.1.0" --notes "Windows desktop release 0.1.0"
```

- If you need to replace an already-published executable for the same tag, use `gh release upload --clobber`.
