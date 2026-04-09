const form = document.querySelector("#planner-form");
const statusPanel = document.querySelector("#status-panel");
const systemSummary = document.querySelector("#system-summary");
const planResults = document.querySelector("#plan-results");
const orderingSummary = document.querySelector("#ordering-summary");
const downloadPdfButton = document.querySelector("#download-pdf");
const apiBaseUrl = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";
let latestPayload = null;

function numberOrNull(formData, key) {
  const value = formData.get(key);
  if (value === null || String(value).trim() === "") {
    return null;
  }
  return Number(value);
}

function textOrNull(formData, key) {
  const value = formData.get(key);
  if (value === null || String(value).trim() === "") {
    return null;
  }
  return String(value).trim();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatRange(range) {
  if (!range) {
    return "Not available";
  }
  return `${range.low_mhz.toFixed(4)} - ${range.high_mhz.toFixed(4)} MHz`;
}

function formatStatus(value) {
  return String(value || "Not evaluated").replaceAll("_", " ").toLowerCase();
}

function badgeClass(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("valid") && !normalized.includes("invalid")) {
    return "valid";
  }
  if (normalized.includes("invalid")) {
    return "invalid";
  }
  if (normalized.includes("likely_licensable")) {
    return "licensable";
  }
  if (normalized.includes("likely_not_licensable")) {
    return "not-licensable";
  }
  if (normalized.includes("coordination")) {
    return "coordination";
  }
  return "not-evaluated";
}

function setStatus(message, type = "ok") {
  statusPanel.hidden = false;
  statusPanel.className = `status-panel ${type}`;
  statusPanel.textContent = message;
}

function renderError(message) {
  const safeMessage = escapeHtml(message);
  latestPayload = null;
  downloadPdfButton.disabled = true;
  systemSummary.className = "empty-state";
  systemSummary.innerHTML = `Evaluation did not complete. ${safeMessage}`;
  planResults.className = "empty-state";
  planResults.innerHTML = "No plan results were returned.";
  orderingSummary.className = "empty-state";
  orderingSummary.innerHTML = "No ordering summary was returned.";
}

function clearStatus() {
  statusPanel.hidden = true;
  statusPanel.textContent = "";
  statusPanel.className = "status-panel";
}

function isOpenedDirectly() {
  return window.location.protocol === "file:";
}

function buildPayload() {
  const formData = new FormData(form);
  return {
    country: formData.get("country"),
    mobile_tx_low_mhz: numberOrNull(formData, "mobile_tx_low_mhz"),
    mobile_tx_high_mhz: numberOrNull(formData, "mobile_tx_high_mhz"),
    mobile_rx_low_mhz: numberOrNull(formData, "mobile_rx_low_mhz"),
    mobile_rx_high_mhz: numberOrNull(formData, "mobile_rx_high_mhz"),
    use_latest_ordering_ruleset: formData.get("use_latest_ordering_ruleset") === "on",
    agency_notes: textOrNull(formData, "agency_notes"),
    actual_licensed_dvrs_tx_low_mhz: numberOrNull(formData, "actual_licensed_dvrs_tx_low_mhz"),
    actual_licensed_dvrs_tx_high_mhz: numberOrNull(formData, "actual_licensed_dvrs_tx_high_mhz"),
    actual_licensed_dvrs_rx_low_mhz: numberOrNull(formData, "actual_licensed_dvrs_rx_low_mhz"),
    actual_licensed_dvrs_rx_high_mhz: numberOrNull(formData, "actual_licensed_dvrs_rx_high_mhz"),
  };
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function renderMessages(messages) {
  if (!messages || messages.length === 0) {
    return "";
  }
  return `
    <ul class="message-list">
      ${messages.map((message) => `<li>${escapeHtml(message)}</li>`).join("")}
    </ul>
  `;
}

function renderSystemSummary(summary) {
  const warnings = summary.warnings || [];
  systemSummary.className = "summary";
  systemSummary.innerHTML = `
    <div class="metric-grid">
      <div class="metric"><span>Detected band</span><strong>${escapeHtml(summary.detected_band)}</strong></div>
      <div class="metric"><span>Pairing source</span><strong>${escapeHtml(formatStatus(summary.pairing_source))}</strong></div>
      <div class="metric"><span>Mobile TX</span><strong>${escapeHtml(formatRange(summary.mobile_tx_range))}</strong></div>
      <div class="metric"><span>Mobile RX</span><strong>${escapeHtml(formatRange(summary.mobile_rx_range))}</strong></div>
      <div class="metric"><span>System RX</span><strong>${escapeHtml(formatRange(summary.system_rx_range))}</strong></div>
      <div class="metric"><span>System TX</span><strong>${escapeHtml(formatRange(summary.system_tx_range))}</strong></div>
    </div>
    ${renderMessages(warnings)}
  `;
}

function renderPlan(plan) {
  const reasons = [
    ...(plan.failure_reasons || []),
    ...(plan.regulatory_reasons || []),
    ...(plan.warnings || []),
    ...(plan.notes || []),
  ];

  return `
    <article class="plan-card">
      <div class="plan-topline">
        <div>
          <h3>${escapeHtml(plan.display_name)}</h3>
          <div class="plan-id">${escapeHtml(plan.plan_id)}</div>
        </div>
        <strong>${Math.round((plan.confidence || 0) * 100)}%</strong>
      </div>
      <div class="badge-row">
        <span class="badge ${badgeClass(plan.technical_status)}">${escapeHtml(formatStatus(plan.technical_status))}</span>
        <span class="badge ${badgeClass(plan.regulatory_status)}">${escapeHtml(formatStatus(plan.regulatory_status))}</span>
        ${(plan.mount_compatibility || []).map((mount) => `<span class="badge mount">${escapeHtml(mount)}</span>`).join("")}
      </div>
      <div class="range-row">
        <div class="metric"><span>Proposed DVRS TX</span><strong>${escapeHtml(formatRange(plan.proposed_dvrs_tx_range))}</strong></div>
        <div class="metric"><span>Proposed DVRS RX</span><strong>${escapeHtml(formatRange(plan.proposed_dvrs_rx_range))}</strong></div>
      </div>
      <ul class="reason-block">
        ${reasons.length ? reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("") : "<li>No additional rule notes returned.</li>"}
      </ul>
    </article>
  `;
}

function renderPlans(plans) {
  planResults.className = "plan-list";
  planResults.innerHTML = plans.map(renderPlan).join("");
}

function renderOrdering(summary) {
  orderingSummary.className = "ordering";
  orderingSummary.innerHTML = `
    <div class="ordering-grid">
      <div class="order-field"><span>System TX</span><strong>${escapeHtml(formatRange(summary.system_tx_range))}</strong></div>
      <div class="order-field"><span>System RX</span><strong>${escapeHtml(formatRange(summary.system_rx_range))}</strong></div>
      <div class="order-field"><span>Proposed DVRS TX</span><strong>${escapeHtml(formatRange(summary.proposed_dvrs_tx_range))}</strong></div>
      <div class="order-field"><span>Proposed DVRS RX</span><strong>${escapeHtml(formatRange(summary.proposed_dvrs_rx_range))}</strong></div>
      <div class="order-field"><span>Actual licensed DVRS TX</span><strong>${escapeHtml(formatRange(summary.actual_licensed_dvrs_tx_range))}</strong></div>
      <div class="order-field"><span>Actual licensed DVRS RX</span><strong>${escapeHtml(formatRange(summary.actual_licensed_dvrs_rx_range))}</strong></div>
    </div>
    ${renderMessages(summary.notes || [])}
  `;
}

function renderResponse(data) {
  renderSystemSummary(data.system_summary);
  renderPlans(data.plan_results || []);
  renderOrdering(data.ordering_summary);
}

async function evaluatePlans(event) {
  event.preventDefault();
  clearStatus();

  if (isOpenedDirectly()) {
    const message = "Open this app at http://127.0.0.1:8000/ after starting uvicorn. Direct file mode can show the page assets, but the browser blocks the API call.";
    renderError(message);
    setStatus(message, "error");
    return;
  }

  setStatus("Evaluating plans...");

  try {
    const payloadToEvaluate = buildPayload();
    const response = await fetch(`${apiBaseUrl}/v1/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payloadToEvaluate),
    });
    const payload = await response.json();

    if (!response.ok || payload.status !== "ok") {
      const error = payload.error || {};
      const details = error.details?.exception_message || error.details?.hint || "";
      throw new Error([error.message, details].filter(Boolean).join(" "));
    }

    renderResponse(payload.data);
    latestPayload = payloadToEvaluate;
    downloadPdfButton.disabled = false;
    setStatus("Evaluation complete.");
  } catch (error) {
    const message = error.message || "The API returned an error.";
    renderError(message);
    setStatus(message, "error");
  }
}

async function downloadOrderingPdf() {
  if (!latestPayload) {
    setStatus("Run an evaluation before generating the ordering PDF.", "error");
    return;
  }

  downloadPdfButton.disabled = true;
  setStatus("Generating ordering PDF...");

  try {
    const response = await fetch(`${apiBaseUrl}/v1/order-summary.pdf`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(latestPayload),
    });

    if (!response.ok) {
      throw new Error("The PDF export did not complete.");
    }

    const blob = await response.blob();
    downloadBlob(blob, "dvrs-ordering-summary.pdf");
    setStatus("Ordering PDF generated.");
  } catch (error) {
    setStatus(error.message || "The PDF export did not complete.", "error");
  } finally {
    downloadPdfButton.disabled = !latestPayload;
  }
}

form.addEventListener("submit", evaluatePlans);
downloadPdfButton.addEventListener("click", downloadOrderingPdf);
if (isOpenedDirectly()) {
  setStatus("Open this app at http://127.0.0.1:8000/ after starting uvicorn. Direct file mode cannot call the backend API.", "error");
} else {
  form.requestSubmit();
}
