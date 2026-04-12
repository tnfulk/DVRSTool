# Raw Thread: UI Error Message Deduplication

## Topic
Diagnose and fix a duplicated validation message in the DVRS web UI for invalid 700 MHz mobile TX range input, then document the work as reusable project history.

## Conversation

### User
In the UI, when given 700low of 995 and 700 high of 804, I get this error: Lowest 700 MHz mobile TX must be lower than highest 700 MHz mobile TX. Lowest 700 MHz mobile TX must be lower than highest 700 MHz mobile TX.
I only need to see that sentence once, not duplicated. Why the duplicate message?

### Assistant
Explained the plan to trace where that validation message was generated in the UI and backend path, then patch the duplication while preserving validation behavior.

### Assistant Work Summary
Inspected the repository root and searched for the duplicated message text.

Findings:
- `dvrs_tool/engine.py` contained the validation label and range validation path for `700 MHz mobile TX`.
- `dvrs_tool/static/app.js` contained frontend error formatting logic.
- `rg.exe` could not run in the environment due to an access error, so the search switched to PowerShell `Get-ChildItem` and `Select-String`.

### Assistant
Reported that `rg` was unavailable in this environment and that PowerShell search would be used instead to continue the investigation.

### Assistant Work Summary
Opened the relevant backend and frontend files.

Relevant backend observation from `dvrs_tool/engine.py`:
- The engine validates the 700 MHz low/high range once through `_validate_required_range(...)`.
- The backend error object includes a top-level `message` and a `rule_violations` array.

Relevant frontend observation from `dvrs_tool/static/app.js`:
- `buildUserFriendlyError(error)`:
  - pushed `error.message`
  - collected `error.rule_violations[*].message`
  - appended those violation messages when no field-specific request-body errors existed

This meant that when the top-level message and the first rule-violation message were identical, the UI concatenated the same sentence twice.

### Assistant
Explained that the backend validator itself appeared to raise one error object, and the likely duplication source was the frontend formatting layer.

### Assistant Work Summary
Inspected `dvrs_tool/api.py` to confirm the API error shape.

Relevant API observation:
- The FastAPI exception handling preserves structured errors and returns:
  - `error.message`
  - `error.rule_violations`

This confirmed the overall root cause:
- The API returned both the top-level message and the detailed rule violation.
- The frontend merged both without deduplication.

### Assistant
Announced the fix: patch the frontend formatter so identical message fragments only appear once.

### Assistant Code Change
Updated `dvrs_tool/static/app.js`.

Implementation details:
- Added `const seenParts = new Set();`
- Added a local helper:

```js
const pushPart = (value) => {
  const normalized = String(value || "").trim();
  if (!normalized || seenParts.has(normalized)) {
    return;
  }
  seenParts.add(normalized);
  parts.push(normalized);
};
```

- Replaced direct `parts.push(...)` calls in `buildUserFriendlyError()` with `pushPart(...)` for:
  - `error.message`
  - joined field error messages
  - joined rule violation messages
  - the optional DVRS correction hint
  - `error.details?.hint`

Effect:
- Duplicate fragments are now suppressed.
- Distinct error messages are still preserved.

### Assistant
Reported that the fix was in place and performed a quick sanity check of the edited function to confirm the dedupe logic was localized and compatible with existing behavior.

### Assistant Final Explanation
Explained the root cause to the user:

- The duplicate happened because the API returned the same validation text twice in different fields of the same error payload:
  - once as `error.message`
  - once as `error.rule_violations[0].message`
- The UI concatenated both, producing the repeated sentence.
- The fix was applied in `dvrs_tool/static/app.js` so repeated fragments are deduplicated before rendering.

Also noted:
- No browser-based verification was run during the thread.
- The fix was limited to frontend formatting and targeted the exact duplication path.

## Follow-up Documentation Request

### User
Requested that the conversation be converted into structured project documentation by creating:

- `docs/dev-history/<thread-slug>-summary.md`
- `docs/raw-threads/<thread-slug>.md`

The user also requested a 3 to 5 sentence append to `docs/dev-log.md` summarizing the thread's contribution.

### Assistant
Inspected the existing `docs/` structure and the current `docs/dev-log.md` format to match repository conventions before writing new documentation files.

Repository observations:
- `docs/dev-history/` already contained thread summaries
- `docs/raw-threads/` already contained cleaned raw transcripts
- `docs/dev-log.md` already maintained short chronological thread summaries

### Assistant
Prepared to add:
- a focused thread summary
- a cleaned raw transcript
- a short `dev-log` entry reflecting the investigation and final frontend dedupe fix

## Technical Outcome

### Root Cause
The duplicated UI validation sentence was not caused by repeated backend validation. It was caused by the frontend combining:

- the top-level API error message
- the same text repeated in `rule_violations`

### Final Fix
Frontend error-message assembly in `dvrs_tool/static/app.js` now deduplicates repeated message parts before rendering them.

### Files Mentioned
- `dvrs_tool/static/app.js`
- `dvrs_tool/engine.py`
- `dvrs_tool/api.py`
- `docs/dev-history/ui-error-message-deduplication-summary.md`
- `docs/raw-threads/ui-error-message-deduplication.md`
- `docs/dev-log.md`
