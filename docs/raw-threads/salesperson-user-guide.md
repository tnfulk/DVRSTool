# Raw Thread Archive: Salesperson User Guide

## User Request

Look at all of the contents in this repo, specifically focused on the original artifacts referenced in the spec, as well as the development documentation. Develop and add a user guide that is targeted at a salesperson as a separate document. Emphasize in the user guide that when the tool cannot find a technically valid plan, they should first confirm that the information provided is accurate, then contact Motorola Solutions presales engineering for additional support. The presales engineering teams may involve the DVRS product management and development engineering teams to either make additional recommendations, or validate a custom design for that customer. Since this is a documentation change, there is no need to rebuild the windows executable.

## Assistant Work Summary

### Repository Review

Reviewed the repository root, current specification, README, and development documentation to ground the requested guide in existing project artifacts.

Reviewed or confirmed the following source basis:

- `README.md`
- `dvrs_desktop.spec`
- `dvrs-web-app-design.md`
- `docs/dev-log.md`
- `docs/release-process.md`
- `docs/DVRS_product_management_paper.md`
- bundled reference PDFs listed in the specification

### Key Implementation Decision

Added a new standalone documentation file for sales users rather than modifying the engineering specification or developer README.

### Documentation Added

- `docs/salesperson-user-guide.md`
- `docs/salesperson-quick-reference.md`
- `docs/salesperson-user-guide.pdf`
- `docs/salesperson-quick-reference.pdf`
- `docs/dev-history/salesperson-user-guide-summary.md`
- `docs/raw-threads/salesperson-user-guide.md`

### Additional Follow-up Work

Added direct README links to the sales documents and created `tests/test_documentation.py` so the repository now checks that both guides exist, include the required escalation workflow, and are reviewed during documentation passes when tracked tool files change. Added `tools/generate_sales_doc_pdfs.py` to render styled PDF versions of both sales documents and verified that the generated PDFs are text-extractable. A later refinement added direct PDF links in the README, tightened the generated PDF design with a more formal revision-block treatment, and audited `requirements.txt` plus `requirements-desktop.txt`, resulting in the addition of `pypdf` to the base requirements while leaving the desktop requirements structure unchanged. The release playbook in `docs/release-process.md` was then updated so future Windows release preparation explicitly includes regenerating and checking the salesperson-facing PDFs when those user documents are intended to ship alongside the executable. The README was also updated one more time so the repo front page now explicitly mirrors that companion-release-doc expectation.

### Development Log Update

Appended a new entry to `docs/dev-log.md` summarizing the documentation change and explicitly noting that the Windows executable was not rebuilt because the task did not change application behavior.

### Build Decision

No Windows rebuild was performed because the request was documentation-only and did not modify shipped application code, UI behavior, desktop packaging, or release assets.
