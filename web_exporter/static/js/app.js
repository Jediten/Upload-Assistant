// =========================================================
// app.js — Main application logic for web_exporter
// =========================================================

// ── Helper: convert size value + unit to bytes ──
function sizeToBytes(value, unit) {
    if (!value || isNaN(value)) return null;
    const v = parseFloat(value);
    if (v <= 0) return null;
    if (unit === "GB") return Math.round(v * 1024 * 1024 * 1024);
    if (unit === "MB") return Math.round(v * 1024 * 1024);
    return Math.round(v);
}

// ── Helper: convert date string to Unix timestamp ──
function dateToTimestamp(dateStr) {
    if (!dateStr) return null;
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return null;
    return Math.floor(d.getTime() / 1000);
}

// ────────────────── Config Form ──────────────────
document.getElementById("configForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    try {
        const response = await fetch("/save_config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        if (response.ok) {
            window.location.reload();
        } else {
            alert(LANG_DICT[CURRENT_LANG]["save_err"]);
        }
    } catch (err) {
        alert(LANG_DICT[CURRENT_LANG]["status_err"] + " " + err);
    }
});

// ────────────────── Test API ──────────────────
document.getElementById("testApiBtn")?.addEventListener("click", async () => {
    const form = document.getElementById("configForm");
    const data = Object.fromEntries(new FormData(form).entries());
    const btn = document.getElementById("testApiBtn");
    const spinner = document.getElementById("testLoading");
    const resultDiv = document.getElementById("testResult");

    btn.disabled = true;
    spinner.style.display = "inline-block";
    resultDiv.style.display = "none";

    try {
        const response = await fetch("/test_api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const resData = await response.json();
        resultDiv.style.display = "block";

        if (resData.status === "ok") {
            resultDiv.className = "alert alert-success p-2 mb-0";
            resultDiv.textContent = `${LANG_DICT[CURRENT_LANG]["test_ok"]} ${resData.cats_count} ${LANG_DICT[CURRENT_LANG]["cat_found"]}`;
        } else {
            resultDiv.className = "alert alert-danger p-2 mb-0";
            resultDiv.textContent = `❌ ${LANG_DICT[CURRENT_LANG]["status_err"]} ${resData.error}`;
        }
    } catch (err) {
        resultDiv.style.display = "block";
        resultDiv.className = "alert alert-danger p-2 mb-0";
        resultDiv.textContent = `❌ ${LANG_DICT[CURRENT_LANG]["sys_err"]} ${err}`;
    } finally {
        btn.disabled = false;
        spinner.style.display = "none";
    }
});

// ────────────────── Queue Name → Update UI ──────────────────
const queueNameInput = document.querySelector('input[name="queue_name"]');
const queueArgText = document.getElementById("queueArgText");
if (queueNameInput && queueArgText) {
    queueNameInput.addEventListener("input", (e) => {
        const val = e.target.value.trim() || "vmf";
        queueArgText.textContent = `--queue ${val}`;
    });
}

// ────────────────── Export Form ──────────────────
document.getElementById("exportForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("exportBtn");
    const spinner = document.getElementById("exportLoading");
    const resultBox = document.getElementById("resultBox");
    const resultText = document.getElementById("resultText");

    btn.disabled = true;
    spinner.style.display = "inline-block";
    resultBox.style.display = "none";

    const formData = new FormData(e.target);

    // Build export payload
    const data = {};
    data.queue_name = formData.get("queue_name") || "vmf";
    data.status_filter = formData.get("status_filter") || "all";
    data.sort = formData.get("sort") || "added_on";
    data.reverse = document.getElementById("reverseSort")?.checked || false;
    data.name_pattern = formData.get("name_pattern") || "";

    // Multi-select fields + modes
    const catSelect = document.getElementById("categoriesSelect");
    data.categories = catSelect ? Array.from(catSelect.selectedOptions).map((o) => o.value) : [];
    data.category_mode = document.querySelector('input[name="category_mode"]:checked')?.value || "include";

    const trackerSelect = document.getElementById("trackersSelect");
    data.trackers = trackerSelect ? Array.from(trackerSelect.selectedOptions).map((o) => o.value) : [];
    data.tracker_mode = document.querySelector('input[name="tracker_mode"]:checked')?.value || "exclude";

    const tagSelect = document.getElementById("tagsSelect");
    if (tagSelect) {
        data.tags = Array.from(tagSelect.selectedOptions).map((o) => o.value);
    } else {
        data.tags = [];
    }
    data.tag_mode = document.querySelector('input[name="tag_mode"]:checked')?.value || "include";

    // Size filters
    data.min_size = sizeToBytes(
        formData.get("min_size_value"),
        formData.get("min_size_unit")
    );
    data.max_size = sizeToBytes(
        formData.get("max_size_value"),
        formData.get("max_size_unit")
    );

    // Date filter
    data.added_after = dateToTimestamp(formData.get("added_after_date"));

    // Limit
    const limitVal = formData.get("limit");
    data.limit = limitVal ? parseInt(limitVal, 10) : null;

    try {
        const response = await fetch("/export", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });

        const resData = await response.json();
        resultBox.style.display = "block";

        if (response.ok) {
            resultText.className = "alert alert-success";
            let excludedInfo =
                resData.excluded > 0
                    ? `\n🚫 ${resData.excluded} ${LANG_DICT[CURRENT_LANG]["msg_excluded"]}`
                    : "";
            resultText.textContent =
                `${LANG_DICT[CURRENT_LANG]["status_ok"]} ${LANG_DICT[CURRENT_LANG]["msg_added"]} ${resData.added} ${LANG_DICT[CURRENT_LANG]["msg_ignored"]} ${resData.queue_name}_queue.log. (${resData.dupes} ${LANG_DICT[CURRENT_LANG]["msg_dupes"]})${excludedInfo}`;
        } else {
            resultText.className = "alert alert-danger";
            resultText.textContent = `${LANG_DICT[CURRENT_LANG]["status_err"]} ${resData.error}`;
        }
    } catch (err) {
        resultBox.style.display = "block";
        resultText.className = "alert alert-danger";
        resultText.textContent = `${LANG_DICT[CURRENT_LANG]["sys_err"]} ${err}`;
    } finally {
        btn.disabled = false;
        spinner.style.display = "none";
    }
});

// ────────────────── Run Upload Form ──────────────────
document.getElementById("runForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("runBtn");
    const spinner = document.getElementById("runLoading");
    const resultBox = document.getElementById("resultBox");
    const resultText = document.getElementById("resultText");
    const termBox = document.getElementById("terminalBox");
    const openExternal = document.getElementById("openExternalCmd")?.checked;

    // If running, this click is to STOP
    if (!openExternal && isRunningUpload) {
        try {
            btn.disabled = true;
            spinner.style.display = "inline-block";
            if (currentEventSource) {
                currentEventSource.close();
                currentEventSource = null;
            }
            const resp = await fetch("/stop_upload", { method: "POST" });
            const resJson = await resp.json();

            resultBox.style.display = "block";
            if (resp.ok && resJson.status === "stopped") {
                resultText.className = "alert alert-warning";
                resultText.textContent = `⚠️ ${LANG_DICT[CURRENT_LANG]["status_ok"]} ${LANG_DICT[CURRENT_LANG]["stop_ok"]}`;
            } else {
                resultText.className = "alert alert-danger";
                resultText.textContent = `${LANG_DICT[CURRENT_LANG]["status_err"]} ${resJson.error || "Stop failed"}`;
            }
        } catch (err) {
            resultBox.style.display = "block";
            resultText.className = "alert alert-danger";
            resultText.textContent = `${LANG_DICT[CURRENT_LANG]["sys_err"]} ${err}`;
        } finally {
            setRunButtonState(false);
            btn.disabled = false;
            spinner.style.display = "none";
        }
        return;
    }

    btn.disabled = true;
    spinner.style.display = "inline-block";
    resultBox.style.display = "none";
    termBox.style.display = openExternal ? "none" : "block";
    termBox.innerHTML = "";
    if (!openExternal) {
        const initSpan = document.createElement("span");
        initSpan.style.color = "#0dcaf0";
        initSpan.textContent = "> Khởi tạo tiến trình Upload Assistant...\n";
        termBox.appendChild(initSpan);
    }

    if (currentEventSource) {
        currentEventSource.close();
        currentEventSource = null;
    }

    let queueName = "vmf";
    if (queueNameInput) {
        queueName = queueNameInput.value.trim() || "vmf";
    }
    const argsList = document.getElementById("customArgs").value.trim();
    const argsBase = "queue-mode " + argsList + " --queue " + queueName;
    const fullStr = encodeURIComponent(argsBase);

    try {
        // External CMD window
        if (openExternal) {
            const resp = await fetch("/run_upload_detached", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ args: argsBase }),
            });
            const resJson = await resp.json();
            resultBox.style.display = "block";
            if (resp.ok && resJson.status === "success") {
                resultText.className = "alert alert-success";
                resultText.textContent = `🌟 ${LANG_DICT[CURRENT_LANG]["status_ok"]} ${LANG_DICT[CURRENT_LANG]["run_ok_ext"]}`;
            } else {
                resultText.className = "alert alert-danger";
                resultText.textContent = `${LANG_DICT[CURRENT_LANG]["status_err"]} ${resJson.error || "Unknown error"}`;
            }
            btn.disabled = false;
            spinner.style.display = "none";
            return;
        }

        // SSE streaming
        currentEventSource = new EventSource("/stream_upload?args=" + fullStr);
        setRunButtonState(true);
        btn.disabled = false;
        spinner.style.display = "none";

        currentEventSource.onmessage = function (event) {
            if (event.data === "[PROCESS_COMPLETE]") {
                const doneSpan = document.createElement("span");
                doneSpan.style.color = "#198754";
                doneSpan.textContent = "> Tiến trình Upload Assistant đã HOÀN TẤT.\n";
                termBox.appendChild(doneSpan);
                currentEventSource.close();
                currentEventSource = null;
                setRunButtonState(false);
                btn.disabled = false;
                spinner.style.display = "none";
                return;
            }
            if (event.data === "[PROCESS_ERROR]") {
                const errSpan = document.createElement("span");
                errSpan.style.color = "#dc3545";
                errSpan.textContent = "> Xảy ra lỗi khi chạy tiến trình.\n";
                termBox.appendChild(errSpan);
                currentEventSource.close();
                currentEventSource = null;
                setRunButtonState(false);
                btn.disabled = false;
                spinner.style.display = "none";
                return;
            }

            const msg = decodeURIComponent(event.data);

            // Color coding
            let color = "#d4d4d4";
            if (msg.includes("ERROR:") || msg.includes("Exception") || msg.includes("Traceback")) {
                color = "#f44336";
            } else if (msg.includes("WARNING:")) {
                color = "#ffeb3b";
            } else if (msg.includes("INFO:") || msg.includes("SUCCESS:")) {
                color = "#4caf50";
            }

            const span = document.createElement("span");
            span.style.color = color;
            span.textContent = msg + "\n";
            termBox.appendChild(span);
            termBox.scrollTop = termBox.scrollHeight;
        };

        currentEventSource.onerror = function () {
            const errSpan = document.createElement("span");
            errSpan.style.color = "#f44336";
            errSpan.textContent = "> Mất kết nối luồng Terminal. Sẽ tự động thử lại...\n";
            termBox.appendChild(errSpan);
        };

        resultBox.style.display = "block";
        resultText.className = "alert alert-success";
        resultText.textContent = `🌟 ${LANG_DICT[CURRENT_LANG]["status_ok"]} ${LANG_DICT[CURRENT_LANG]["run_ok"]}`;
    } catch (err) {
        resultBox.style.display = "block";
        resultText.className = "alert alert-danger";
        resultText.textContent = `${LANG_DICT[CURRENT_LANG]["sys_err"]} ${err}`;
        setRunButtonState(false);
        btn.disabled = false;
        spinner.style.display = "none";
    }
});

// ────────────────── Stdin Handlers ──────────────────
document.getElementById("stdinSendBtn")?.addEventListener("click", sendStdin);
document.getElementById("stdinInput")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        sendStdin();
    }
});
