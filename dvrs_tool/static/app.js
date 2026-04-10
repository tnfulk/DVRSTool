const form = document.querySelector("#planner-form");
const statusPanel = document.querySelector("#status-panel");
const systemSummary = document.querySelector("#system-summary");
const planResults = document.querySelector("#plan-results");
const orderingSummary = document.querySelector("#ordering-summary");
const downloadPdfButton = document.querySelector("#download-pdf");
const resetPlannerButton = document.querySelector("#reset-planner");
const resultsLayout = document.querySelector("#results-layout");
const apiBaseUrl = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";
let latestPayload = null;
let latestInputPrecision = null;
let lastSystemBandMode = null;

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

function decimalPlacesFromInput(value) {
  if (value === null || value === undefined) {
    return 4;
  }
  const text = String(value).trim();
  if (!text || !text.includes(".")) {
    return 0;
  }
  return text.split(".")[1].length;
}

function captureInputPrecision(formData) {
  return {
    mobile_tx_range: {
      low: decimalPlacesFromInput(formData.get("mobile_tx_low_mhz")),
      high: decimalPlacesFromInput(formData.get("mobile_tx_high_mhz")),
    },
    mobile_tx_700_range: {
      low: decimalPlacesFromInput(formData.get("mobile_tx_700_low_mhz")),
      high: decimalPlacesFromInput(formData.get("mobile_tx_700_high_mhz")),
    },
    mobile_tx_800_range: {
      low: decimalPlacesFromInput(formData.get("mobile_tx_800_low_mhz")),
      high: decimalPlacesFromInput(formData.get("mobile_tx_800_high_mhz")),
    },
    mobile_rx_range: {
      low: decimalPlacesFromInput(formData.get("mobile_rx_low_mhz")),
      high: decimalPlacesFromInput(formData.get("mobile_rx_high_mhz")),
    },
    actual_dvrs: {
      tx: decimalPlacesFromInput(formData.get("actual_dvrs_tx_mhz")),
      rx: decimalPlacesFromInput(formData.get("actual_dvrs_rx_mhz")),
    },
  };
}

function formatRange(range, precision = null) {
  if (!range) {
    return "Not available";
  }
  const lowPrecision = precision?.low ?? 4;
  const highPrecision = precision?.high ?? 4;
  return `${range.low_mhz.toFixed(lowPrecision)} - ${range.high_mhz.toFixed(highPrecision)} MHz`;
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
  hideResults();
  systemSummary.className = "empty-state";
  systemSummary.innerHTML = `Evaluation did not complete. ${safeMessage}`;
  planResults.className = "empty-state";
  planResults.innerHTML = "No plan results were returned.";
  orderingSummary.className = "empty-state";
  orderingSummary.innerHTML = "No ordering summary was returned.";
}

function formatFieldLabel(field) {
  const labels = {
    country: "Country",
    mobile_tx_low_mhz: "System Frequency Low",
    mobile_tx_high_mhz: "System Frequency High",
    system_band_hint: "System Frequency Configuration",
    mobile_rx_low_mhz: "System TX Low",
    mobile_rx_high_mhz: "System TX High",
    actual_dvrs_tx_mhz: "DVRS TX",
    actual_dvrs_rx_mhz: "DVRS RX",
  };
  return labels[field] || String(field || "Input");
}

function buildUserFriendlyError(error) {
  if (!error) {
    return "The API returned an error.";
  }

  const parts = [];
  if (error.message) {
    parts.push(error.message);
  }

  const fieldErrors = error.details?.field_errors || [];
  if (fieldErrors.length) {
    const fieldMessages = fieldErrors.map((fieldError) => {
      const hint = fieldError.hint ? ` ${fieldError.hint}` : "";
      return `${formatFieldLabel(fieldError.field)}: ${fieldError.message}.${hint}`.trim();
    });
    parts.push(fieldMessages.join(" "));
  }

  const violationMessages = (error.rule_violations || [])
    .map((violation) => violation.message)
    .filter(Boolean);
  if (!fieldErrors.length && violationMessages.length) {
    parts.push(violationMessages.slice(0, 2).join(" "));
  }

  if (error.details?.field && String(error.details.field).startsWith("actual_dvrs_")) {
    parts.push("Confirm the optional DVRS frequency values are correct, or clear those fields and re-run the evaluation.");
  }

  if (error.details?.hint) {
    parts.push(error.details.hint);
  }

  return parts.filter(Boolean).join(" ");
}

function clearStatus() {
  statusPanel.hidden = true;
  statusPanel.textContent = "";
  statusPanel.className = "status-panel";
}

function getEvaluationStatus(data) {
  const notes = data?.ordering_summary?.notes || [];
  const warningNote = notes.find((note) =>
    note.includes("Consult a Motorola Presale Engineer")
    || note.includes("No technically valid standard plan proposal was produced.")
  );
  if (warningNote) {
    return { message: warningNote, type: "warning" };
  }
  return null;
}

function showResults() {
  resultsLayout.hidden = false;
}

function hideResults() {
  resultsLayout.hidden = true;
}

function resetRenderedResults() {
  systemSummary.className = "empty-state";
  systemSummary.innerHTML = "Run an evaluation to see the selected system configuration, detected band, and derived system pairing.";
  planResults.className = "empty-state";
  planResults.innerHTML = "The standard plans for the selected system configuration will appear here.";
  orderingSummary.className = "empty-state";
  orderingSummary.innerHTML = "The best preliminary standard plan will populate this summary.";
}

function isOpenedDirectly() {
  return window.location.protocol === "file:";
}

function buildPayload() {
  const formData = new FormData(form);
  latestInputPrecision = captureInputPrecision(formData);
  return {
    country: formData.get("country"),
    mobile_tx_low_mhz: numberOrNull(formData, "mobile_tx_low_mhz"),
    mobile_tx_high_mhz: numberOrNull(formData, "mobile_tx_high_mhz"),
    system_band_hint: textOrNull(formData, "system_band_hint"),
    mobile_tx_700_low_mhz: numberOrNull(formData, "mobile_tx_700_low_mhz"),
    mobile_tx_700_high_mhz: numberOrNull(formData, "mobile_tx_700_high_mhz"),
    mobile_tx_800_low_mhz: numberOrNull(formData, "mobile_tx_800_low_mhz"),
    mobile_tx_800_high_mhz: numberOrNull(formData, "mobile_tx_800_high_mhz"),
    mobile_rx_low_mhz: numberOrNull(formData, "mobile_rx_low_mhz"),
    mobile_rx_high_mhz: numberOrNull(formData, "mobile_rx_high_mhz"),
    use_latest_ordering_ruleset: formData.get("use_latest_ordering_ruleset") === "on",
    agency_name: textOrNull(formData, "agency_name"),
    quote_date: textOrNull(formData, "quote_date"),
    mobile_radio_type: textOrNull(formData, "mobile_radio_type"),
    control_head_type: textOrNull(formData, "control_head_type"),
    msu_antenna_type: textOrNull(formData, "msu_antenna_type"),
    agency_notes: textOrNull(formData, "agency_notes"),
    actual_dvrs_tx_mhz: numberOrNull(formData, "actual_dvrs_tx_mhz"),
    actual_dvrs_rx_mhz: numberOrNull(formData, "actual_dvrs_rx_mhz"),
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

function formatInputValue(value) {
  if (value === null || value === undefined || value === "") {
    return "Not provided";
  }
  return String(value);
}

function buildVisualizationSegments(plan, summary) {
  const hasMixedSegments = summary.detected_band === "700 and 800"
    && (summary.mobile_tx_700_range || summary.mobile_tx_800_range);
  const segments = hasMixedSegments
    ? [
      { label: "700 System RX", range: summary.mobile_tx_700_range, className: "mobile-700" },
      { label: "800 System RX", range: summary.mobile_tx_800_range, className: "mobile-800" },
      { label: "700 System TX", range: summary.system_tx_700_range, className: "system-700" },
      { label: "800 System TX", range: summary.system_tx_800_range, className: "system-800" },
      { label: "DVRS RX", range: plan.proposed_dvrs_rx_range, className: "dvrs-rx" },
      { label: "DVRS TX", range: plan.proposed_dvrs_tx_range, className: "dvrs-tx" },
    ]
    : [
      { label: "System RX", range: plan.mobile_tx_range, className: "mobile" },
      { label: "System TX", range: plan.system_tx_range, className: "system" },
      { label: "DVRS RX", range: plan.proposed_dvrs_rx_range, className: "dvrs-rx" },
      { label: "DVRS TX", range: plan.proposed_dvrs_tx_range, className: "dvrs-tx" },
    ];

  const numericRanges = segments
    .map((segment) => segment.range)
    .filter(Boolean);

  if (!numericRanges.length) {
    return segments.map((segment) => ({
      ...segment,
      startPercent: 0,
      widthPercent: 0,
      unavailable: true,
    }));
  }

  const minValue = Math.min(...numericRanges.map((range) => range.low_mhz));
  const maxValue = Math.max(...numericRanges.map((range) => range.high_mhz));
  const rawSpan = Math.max(maxValue - minValue, 0.01);
  const axisPadding = Math.max(rawSpan * 0.12, 0.05);
  const paddedMin = minValue - axisPadding;
  const paddedMax = maxValue + axisPadding;
  const span = paddedMax - paddedMin;

  return segments.map((segment) => {
    if (!segment.range) {
      return {
        ...segment,
        startPercent: 0,
        widthPercent: 0,
        unavailable: true,
      };
    }

    const startPercent = ((segment.range.low_mhz - paddedMin) / span) * 100;
    const widthPercent = ((segment.range.high_mhz - segment.range.low_mhz) / span) * 100;
    return {
      ...segment,
      axisLow: paddedMin,
      axisHigh: paddedMax,
      startPercent,
      widthPercent,
      unavailable: false,
    };
  });
}

function buildVisualizationTicks(segments) {
  const axisSegment = segments.find((segment) => !segment.unavailable);
  if (!axisSegment) {
    return [];
  }

  const axisLow = axisSegment.axisLow;
  const axisHigh = axisSegment.axisHigh;
  const span = axisHigh - axisLow;
  if (span <= 0) {
    return [];
  }

  const targetTickCount = 7;
  const rawStep = span / (targetTickCount - 1);
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const normalized = rawStep / magnitude;
  const niceNormalized = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 2.5 ? 2.5 : normalized <= 5 ? 5 : 10;
  const step = niceNormalized * magnitude;
  const start = Math.ceil(axisLow / step) * step;
  const ticks = [];

  ticks.push({ value: axisLow, percent: 0 });
  for (let value = start; value < axisHigh; value += step) {
    const roundedValue = Number(value.toFixed(5));
    const percent = ((roundedValue - axisLow) / span) * 100;
    if (percent > 1 && percent < 99) {
      ticks.push({ value: roundedValue, percent });
    }
  }
  ticks.push({ value: axisHigh, percent: 100 });

  return ticks;
}

function renderPlanVisualization(plan, summary) {
  const segments = buildVisualizationSegments(plan, summary);
  const axisSegments = segments.filter((segment) => !segment.unavailable);
  const ticks = buildVisualizationTicks(segments);

  return `
    <div class="plan-visualization" aria-label="${escapeHtml(plan.display_name)} frequency visualization">
      <div class="visualization-title">${escapeHtml(plan.plan_id)} frequency layout</div>
      <div class="viz-single-view ${!axisSegments.length ? "is-empty" : ""}">
        <div class="viz-axis-grid">
          ${!axisSegments.length ? '<div class="viz-empty">No evaluated ranges available</div>' : `
            <div class="viz-track viz-track-large">
              ${ticks.map((tick) => `
                <span class="viz-tick" style="left:${tick.percent.toFixed(2)}%"></span>
              `).join("")}
              <div class="viz-axis-line"></div>
              ${segments.map((segment, index) => segment.unavailable
                ? ""
                : `
                  <div class="viz-bar ${segment.className}" style="left:${segment.startPercent.toFixed(2)}%;width:${Math.max(segment.widthPercent, 0.8).toFixed(2)}%"></div>
                `).join("")}
            </div>
            <div class="viz-axis-head viz-axis-foot">
              ${ticks.map((tick) => `
                <span class="viz-axis-label" style="left:${tick.percent.toFixed(2)}%">
                  ${escapeHtml(tick.value.toFixed(4))}
                </span>
              `).join("")}
            </div>
          `}
        </div>
      </div>
      <div class="viz-legend">
        ${segments.map((segment) => `
          <div class="viz-legend-item ${segment.unavailable ? "is-unavailable" : ""}">
            <span class="viz-swatch ${segment.className}"></span>
            <span class="viz-legend-label">${escapeHtml(segment.label)}</span>
            <span class="viz-legend-value">${escapeHtml(formatRange(segment.range))}</span>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

function renderSystemSummary(summary) {
  const warnings = summary.warnings || [];
  const mobileTxPrecision = latestInputPrecision?.mobile_tx_range;
  const mobile700Precision = latestInputPrecision?.mobile_tx_700_range;
  const mobile800Precision = latestInputPrecision?.mobile_tx_800_range;
  const mobileRxPrecision = latestInputPrecision?.mobile_rx_range || mobileTxPrecision;
  const isMixedBand = summary.detected_band === "700 and 800";
  const baseMetrics = isMixedBand ? "" : `
      <div class="metric"><span>Entered System Frequencies</span><strong>${escapeHtml(formatRange(summary.system_rx_range, mobileTxPrecision))}</strong></div>
      <div class="metric"><span>System TX</span><strong>${escapeHtml(formatRange(summary.system_tx_range, mobileRxPrecision))}</strong></div>
  `;
  const mixedSystemMetrics = summary.detected_band === "700 and 800" ? `
      <div class="metric"><span>700 System RX</span><strong>${escapeHtml(formatRange(summary.mobile_tx_700_range, mobile700Precision))}</strong></div>
      <div class="metric"><span>700 System TX</span><strong>${escapeHtml(formatRange(summary.system_tx_700_range, mobile700Precision))}</strong></div>
      <div class="metric"><span>800 System RX</span><strong>${escapeHtml(formatRange(summary.mobile_tx_800_range, mobile800Precision))}</strong></div>
      <div class="metric"><span>800 System TX</span><strong>${escapeHtml(formatRange(summary.system_tx_800_range, mobile800Precision))}</strong></div>
  ` : "";
  systemSummary.className = "summary";
  systemSummary.innerHTML = `
    <div class="metric-grid">
      <div class="metric"><span>Detected band</span><strong>${escapeHtml(summary.detected_band)}</strong></div>
      <div class="metric"><span>Pairing source</span><strong>${escapeHtml(formatStatus(summary.pairing_source))}</strong></div>
      ${baseMetrics}
      ${mixedSystemMetrics}
    </div>
    ${isMixedBand ? "" : renderMessages(warnings)}
  `;
}

function renderPlan(plan, summary) {
  const isTechnicallyValid = plan.technical_status === "TECHNICALLY_VALID";
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
      </div>
      <div class="badge-row">
        <span class="badge ${badgeClass(plan.technical_status)}">${escapeHtml(formatStatus(plan.technical_status))}</span>
        <span class="badge ${badgeClass(plan.regulatory_status)}">${escapeHtml(formatStatus(plan.regulatory_status))}</span>
      </div>
      <div class="range-row">
        <div class="metric"><span>Proposed DVRS TX</span><strong>${escapeHtml(isTechnicallyValid ? formatRange(plan.proposed_dvrs_tx_range) : "Not shown for invalid plans")}</strong></div>
        <div class="metric"><span>Proposed DVRS RX</span><strong>${escapeHtml(isTechnicallyValid ? formatRange(plan.proposed_dvrs_rx_range) : "Not shown for invalid plans")}</strong></div>
      </div>
      ${isTechnicallyValid ? renderPlanVisualization(plan, summary) : ""}
      <ul class="reason-block">
        ${reasons.length ? reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("") : "<li>No additional rule notes returned.</li>"}
      </ul>
    </article>
  `;
}

function renderPlans(plans, summary) {
  planResults.className = "plan-list";
  planResults.innerHTML = plans.map((plan) => renderPlan(plan, summary)).join("");
}

function getVisiblePlans(data) {
  const plans = data.plan_results || [];
  const hasActualDvrs = (
    (data.request?.actual_dvrs_tx_mhz !== null && data.request?.actual_dvrs_tx_mhz !== undefined)
    || (data.request?.actual_dvrs_rx_mhz !== null && data.request?.actual_dvrs_rx_mhz !== undefined)
  );
  if (!hasActualDvrs) {
    return plans;
  }

  const validPlans = plans.filter((plan) => plan.technical_status === "TECHNICALLY_VALID");
  return validPlans.length ? validPlans : plans;
}

function renderOrdering(data) {
  const summary = data.ordering_summary;
  const request = data.request;
  const actualPrecision = latestInputPrecision?.actual_dvrs || {};
  orderingSummary.className = "ordering";
  orderingSummary.innerHTML = `
    <div class="ordering-grid">
      <div class="order-field"><span>System TX</span><strong>${escapeHtml(formatRange(summary.system_tx_range))}</strong></div>
      <div class="order-field"><span>System RX</span><strong>${escapeHtml(formatRange(summary.system_rx_range))}</strong></div>
      <div class="order-field"><span>Proposed DVRS TX</span><strong>${escapeHtml(formatRange(summary.proposed_dvrs_tx_range))}</strong></div>
      <div class="order-field"><span>Proposed DVRS RX</span><strong>${escapeHtml(formatRange(summary.proposed_dvrs_rx_range))}</strong></div>
      <div class="order-field"><span>DVRS TX</span><strong>${escapeHtml(formatRange(summary.actual_dvrs_tx_range, summary.actual_dvrs_tx_range ? { low: actualPrecision.tx ?? 4, high: actualPrecision.tx ?? 4 } : null))}</strong></div>
      <div class="order-field"><span>DVRS RX</span><strong>${escapeHtml(formatRange(summary.actual_dvrs_rx_range, summary.actual_dvrs_rx_range ? { low: actualPrecision.rx ?? 4, high: actualPrecision.rx ?? 4 } : null))}</strong></div>
      <div class="order-field"><span>Agency name</span><strong>${escapeHtml(formatInputValue(request.agency_name))}</strong></div>
      <div class="order-field"><span>Date</span><strong>${escapeHtml(formatInputValue(request.quote_date))}</strong></div>
      <div class="order-field"><span>Mobile radio type</span><strong>${escapeHtml(formatInputValue(request.mobile_radio_type))}</strong></div>
      <div class="order-field"><span>Control head type</span><strong>${escapeHtml(formatInputValue(request.control_head_type))}</strong></div>
      <div class="order-field"><span>Antenna type</span><strong>${escapeHtml(formatInputValue(request.msu_antenna_type))}</strong></div>
    </div>
    ${renderMessages(summary.notes || [])}
  `;
}

function renderResponse(data) {
  showResults();
  renderSystemSummary(data.system_summary);
  renderPlans(getVisiblePlans(data), data.system_summary);
  renderOrdering(data);
}

function applyDefaultDate() {
  const dateInput = form.querySelector('input[name="quote_date"]');
  if (dateInput && !dateInput.value) {
    dateInput.value = new Date().toISOString().slice(0, 10);
  }
}

function resetPlanner() {
  form.reset();
  latestPayload = null;
  latestInputPrecision = null;
  downloadPdfButton.disabled = true;
  clearStatus();
  resetRenderedResults();
  hideResults();
  applyDefaultDate();
  syncSystemBandFields();
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
      throw new Error(buildUserFriendlyError(error));
    }

    renderResponse(payload.data);
    latestPayload = payloadToEvaluate;
    downloadPdfButton.disabled = false;
    const evaluationStatus = getEvaluationStatus(payload.data);
    if (evaluationStatus) {
      setStatus(evaluationStatus.message, evaluationStatus.type);
    } else {
      clearStatus();
    }
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
resetPlannerButton?.addEventListener("click", resetPlanner);

function syncSystemBandFields() {
  const systemBandSelect = form.querySelector('select[name="system_band_hint"]');
  const mixedBandFields = form.querySelectorAll(".mixed-band-field");
  const singleBandLowLabel = form.querySelector("[data-single-band-low-label]");
  const singleBandHighLabel = form.querySelector("[data-single-band-high-label]");
  const baseMobileFields = [
    form.querySelector('input[name="mobile_tx_low_mhz"]').closest("label"),
    form.querySelector('input[name="mobile_tx_high_mhz"]').closest("label"),
  ];
  const baseMobileInputs = [
    form.querySelector('input[name="mobile_tx_low_mhz"]'),
    form.querySelector('input[name="mobile_tx_high_mhz"]'),
  ];
  const selectedMode = systemBandSelect?.value || "800 only";
  const mixedMode = selectedMode === "700 and 800";
  const singleBandPrefix = selectedMode === "700 only" ? "700 MHz System Frequency" : "800 MHz System Frequency";
  const modeChanged = lastSystemBandMode !== null && lastSystemBandMode !== selectedMode;

  if (singleBandLowLabel) {
    singleBandLowLabel.textContent = `${singleBandPrefix} Low (MHz)`;
  }
  if (singleBandHighLabel) {
    singleBandHighLabel.textContent = `${singleBandPrefix} High (MHz)`;
  }

  mixedBandFields.forEach((field) => {
    field.hidden = !mixedMode;
    field.classList.toggle("is-hidden", !mixedMode);
    const input = field.querySelector("input");
    if (input) {
      input.required = mixedMode;
      input.disabled = !mixedMode;
      if (!mixedMode && modeChanged) {
        input.value = "";
      }
    }
  });

  baseMobileFields.forEach((field) => {
    if (field) {
      field.hidden = mixedMode;
      field.classList.toggle("is-hidden", mixedMode);
    }
  });
  baseMobileInputs.forEach((input) => {
    if (input) {
      input.required = !mixedMode;
      input.disabled = mixedMode;
      if (mixedMode || modeChanged) {
        input.value = "";
      }
    }
  });

  lastSystemBandMode = selectedMode;
}

form.querySelector('select[name="system_band_hint"]')?.addEventListener("change", syncSystemBandFields);
syncSystemBandFields();

applyDefaultDate();
resetRenderedResults();
hideResults();
if (isOpenedDirectly()) {
  setStatus("Open this app at http://127.0.0.1:8000/ after starting uvicorn. Direct file mode cannot call the backend API.", "error");
}
