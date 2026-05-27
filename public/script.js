const form = document.querySelector("#capsule-form");
const markdown = document.querySelector("#markdown");
const confidence = document.querySelector("#confidence");
const tagList = document.querySelector("#tag-list");
const redactions = document.querySelector("#redactions");
const copyButton = document.querySelector("#copy");
const downloadButton = document.querySelector("#download");
const clearButton = document.querySelector("#clear");
const sampleButton = document.querySelector("#sample");
const generateButton = document.querySelector("#generate");
const modeButtons = document.querySelectorAll(".mode");

let mode = "balanced";

modeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    mode = button.dataset.mode;
    modeButtons.forEach((item) => item.classList.toggle("active", item === button));
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(form).entries());
  payload.mode = mode;

  generateButton.disabled = true;
  generateButton.textContent = "Generating…";
  confidence.textContent = "Scanning and sanitizing…";
  redactions.innerHTML = "<li>Scanning for secrets, identity markers, and internal details.</li>";
  copyButton.disabled = true;
  downloadButton.disabled = true;

  try {
    const response = await fetch("/api/capsule", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.error || `Server error ${response.status}`);
    }

    const capsule = await response.json();
    confidence.textContent = capsule.confidence;
    tagList.textContent = capsule.tags.map((tag) => `#${tag}`).join(" ");
    markdown.value = capsule.markdown;
    copyButton.disabled = false;
    downloadButton.disabled = false;

    if (capsule.redactions.length === 0) {
      redactions.innerHTML = "<li>No redactions were needed. Human review is still required.</li>";
    } else {
      redactions.innerHTML = capsule.redactions
        .map((item) => `<li>${item.type}: ${item.count}</li>`)
        .join("");
    }
  } catch (err) {
    confidence.textContent = "Generation failed";
    redactions.innerHTML = `<li>${err.message || "Unexpected error — check your input and try again."}</li>`;
  } finally {
    generateButton.disabled = false;
    generateButton.textContent = "Generate Draft";
  }
});

copyButton.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(markdown.value);
    copyButton.textContent = "Copied";
    setTimeout(() => {
      copyButton.textContent = "Copy";
    }, 1200);
  } catch {
    copyButton.textContent = "Copy failed";
    setTimeout(() => {
      copyButton.textContent = "Copy";
    }, 1500);
  }
});

downloadButton.addEventListener("click", () => {
  const blob = new Blob([markdown.value], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "resolution-capsule.md";
  anchor.click();
  URL.revokeObjectURL(url);
});

clearButton.addEventListener("click", () => {
  form.reset();
  markdown.value = "";
  confidence.textContent = "Waiting for capsule";
  tagList.textContent = "";
  redactions.innerHTML = "<li>No scan has run yet.</li>";
  copyButton.disabled = true;
  downloadButton.disabled = true;
});

sampleButton.addEventListener("click", () => {
  form.problem.value =
    "The CI build failed after upgrading the Node image. A private repo path and a developer email appeared in the logs.";
  form.environment.value =
    "Node 22, Vite, GitHub Actions, macOS runner. Maintainer: alex@example.com. Ticket PLATFORM-1234.";
  form.error.value =
    "Error: Cannot find module '@vitejs/plugin-react'\n    at /Users/alex/work/internal-app/vite.config.ts\nAuthorization: Bearer abcdefghijklmnopqrstuvwxyz123456";
  form.attempts.value =
    "Cleared node_modules, retried npm ci, and pinned the runner image. The failure persisted because the lockfile was stale.";
  form.rootCause.value =
    "The package lock was generated before the plugin was added, so CI installed the older dependency graph.";
  form.fix.value =
    "Regenerated package-lock.json with the plugin present, committed it, and added a CI check that fails when package.json and the lockfile drift.";
});
