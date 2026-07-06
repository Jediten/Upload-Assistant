// =========================================================
// terminal.js — SSE terminal streaming for upload.py output
// =========================================================

let currentEventSource = null;
let isRunningUpload = false;

function setRunButtonState(running) {
    const btn = document.getElementById("runBtn");
    const labelSpan = btn ? btn.querySelector('span[data-lang="btn_run"]') : null;
    if (!btn || !labelSpan) return;

    isRunningUpload = running;
    const stdinRow = document.getElementById("stdinRow");
    const stdinInput = document.getElementById("stdinInput");
    if (stdinRow) stdinRow.style.display = running ? "block" : "none";
    if (stdinInput) {
        stdinInput.disabled = !running;
        if (!running) stdinInput.value = "";
    }

    if (running) {
        btn.classList.remove("btn-success");
        btn.classList.add("btn-danger");
        labelSpan.textContent = LANG_DICT[CURRENT_LANG]["btn_stop"];
    } else {
        btn.classList.remove("btn-danger");
        btn.classList.add("btn-success");
        labelSpan.textContent = LANG_DICT[CURRENT_LANG]["btn_run"];
    }
}

function sendStdin() {
    const inp = document.getElementById("stdinInput");
    if (!inp || inp.disabled) return;
    const line = inp.value.trim();
    if (!line) return;
    inp.value = "";
    fetch("/upload_stdin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: line }),
    })
    .then((r) => r.json())
    .then((res) => {
        if (res.status !== "ok" && res.error) console.warn("stdin:", res.error);
    })
    .catch(() => {});
}
