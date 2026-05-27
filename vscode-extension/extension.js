const vscode = require("vscode");
const cp = require("child_process");
const fs = require("fs");
const http = require("http");
const https = require("https");
const path = require("path");
const crypto = require("crypto");
const zlib = require("zlib");
const { URLSearchParams } = require("url");

let extensionContext;

function activate(context) {
  extensionContext = context;
  context.subscriptions.push(
    vscode.commands.registerCommand("resolutionCapsule.createFromSelection", createFromSelection),
    vscode.commands.registerCommand("resolutionCapsule.createFromPrompts", createFromPrompts),
    vscode.commands.registerCommand("resolutionCapsule.connectStackOverflow", () =>
      connectStackOverflow(context).catch((err) =>
        vscode.window.showErrorMessage(`Stack Overflow auth failed: ${err.message}`)
      )
    ),
    vscode.commands.registerCommand("resolutionCapsule.disconnectStackOverflow", () =>
      disconnectStackOverflow(context)
    )
  );
}

// ── Capsule generation ────────────────────────────────────────────────────────

async function createFromSelection() {
  const editor = vscode.window.activeTextEditor;
  const selected = editor ? editor.document.getText(editor.selection) : "";

  if (!selected.trim()) {
    vscode.window.showWarningMessage("Select logs, an error, or RCA notes first.");
    return;
  }

  const rootCause = await vscode.window.showInputBox({ prompt: "Root cause" });
  if (rootCause === undefined) return;
  const fix = await vscode.window.showInputBox({ prompt: "Final fix" });
  if (fix === undefined) return;

  await generate({ problem: "Captured from editor selection", error: selected, rootCause, fix });
}

async function createFromPrompts() {
  const problem = await vscode.window.showInputBox({ prompt: "Problem" });
  if (problem === undefined) return;
  const environment = await vscode.window.showInputBox({ prompt: "Environment" });
  if (environment === undefined) return;
  const error = await vscode.window.showInputBox({ prompt: "Error or symptom" });
  if (error === undefined) return;
  const attempts = await vscode.window.showInputBox({ prompt: "Attempts" });
  if (attempts === undefined) return;
  const rootCause = await vscode.window.showInputBox({ prompt: "Root cause" });
  if (rootCause === undefined) return;
  const fix = await vscode.window.showInputBox({ prompt: "Final fix" });
  if (fix === undefined) return;

  await generate({ problem, environment, error, attempts, rootCause, fix });
}

async function generate(payload) {
  const config = vscode.workspace.getConfiguration("resolutionCapsule");
  payload.mode = config.get("sanitizationMode", "balanced");

  const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  const configuredEnginePath = config.get("enginePath", "");
  const repoRoot = workspaceRoot || path.resolve(extensionContext.extensionPath, "..");
  const script = configuredEnginePath || findEnginePath(repoRoot, extensionContext.extensionPath);
  const pythonPath = config.get("pythonPath", "python3");

  cp.execFile(
    pythonPath,
    [script, "--format", "json", "--json", JSON.stringify(payload)],
    { cwd: repoRoot, maxBuffer: 1024 * 1024 },
    async (error, stdout, stderr) => {
      if (error) {
        vscode.window.showErrorMessage(`Resolution Capsule failed: ${stderr || error.message}`);
        return;
      }

      let result;
      try {
        result = JSON.parse(stdout);
      } catch {
        vscode.window.showErrorMessage(
          `Resolution Capsule: unexpected output — ${stdout.slice(0, 120)}`
        );
        return;
      }

      const doc = await vscode.workspace.openTextDocument({
        content: result.markdown,
        language: "markdown",
      });
      await vscode.window.showTextDocument(doc, { preview: false });

      const hasToken = !!(await extensionContext.secrets.get("soAccessToken"));
      const action = await vscode.window.showInformationMessage(
        `Capsule ready · ${result.confidence}`,
        hasToken ? "Post to Stack Overflow" : "Connect Stack Overflow"
      );

      if (action === "Post to Stack Overflow") {
        postQuestion(extensionContext, result).catch((err) =>
          vscode.window.showErrorMessage(`Post failed: ${err.message}`)
        );
      } else if (action === "Connect Stack Overflow") {
        connectStackOverflow(extensionContext)
          .then(() =>
            vscode.window.showInformationMessage(
              "Connected! Run the command again to post this capsule."
            )
          )
          .catch((err) =>
            vscode.window.showErrorMessage(`Auth failed: ${err.message}`)
          );
      }
    }
  );
}

function findEnginePath(repoRoot, extensionPath) {
  const candidates = [
    path.join(extensionPath, "capsule_cli.py"),
    path.join(repoRoot, "capsule_cli.py"),
    path.join(extensionPath, "..", "capsule_cli.py"),
  ];
  return candidates.find((c) => fs.existsSync(c)) || candidates[0];
}

// ── Stack Overflow OAuth ──────────────────────────────────────────────────────

async function connectStackOverflow(context) {
  const config = vscode.workspace.getConfiguration("resolutionCapsule");
  const clientId = config.get("stackOverflow.clientId", "");
  const clientSecret = config.get("stackOverflow.clientSecret", "");

  if (!clientId || !clientSecret) {
    const action = await vscode.window.showErrorMessage(
      "Set resolutionCapsule.stackOverflow.clientId and clientSecret in settings first.",
      "Open Settings"
    );
    if (action) {
      vscode.commands.executeCommand(
        "workbench.action.openSettings",
        "resolutionCapsule.stackOverflow"
      );
    }
    return;
  }

  const state = crypto.randomBytes(16).toString("hex");
  const port = await findFreePort();
  const redirectUri = `http://localhost:${port}/callback`;

  // Start local server to capture the OAuth callback
  const code = await new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      const reqUrl = new URL(req.url, `http://localhost:${port}`);
      if (reqUrl.pathname !== "/callback") return;

      const returnedState = reqUrl.searchParams.get("state");
      const authCode = reqUrl.searchParams.get("code");
      const authError = reqUrl.searchParams.get("error");

      res.writeHead(200, { "Content-Type": "text/html" });
      res.end(
        "<!doctype html><html><body style='font-family:sans-serif;padding:48px;max-width:480px'>" +
          "<h2 style='color:#0f766e'>&#10003; Connected to Stack Overflow</h2>" +
          "<p>You can close this tab and return to VS Code.</p>" +
          "</body></html>"
      );
      server.close();

      if (authError) {
        reject(new Error(`Stack Overflow denied access: ${authError}`));
        return;
      }
      if (returnedState !== state) {
        reject(new Error("OAuth state mismatch — possible CSRF"));
        return;
      }
      resolve(authCode);
    });

    server.on("error", reject);

    server.listen(port, () => {
      const authUrl = new URL("https://stackoverflow.com/oauth");
      authUrl.searchParams.set("client_id", clientId);
      authUrl.searchParams.set("redirect_uri", redirectUri);
      authUrl.searchParams.set("scope", "write_access,no_expiry");
      authUrl.searchParams.set("state", state);
      vscode.env.openExternal(vscode.Uri.parse(authUrl.toString()));
      vscode.window.showInformationMessage(
        "Browser opened — log in to Stack Overflow to authorise Resolution Capsule."
      );
    });

    // Cancel after 5 minutes
    setTimeout(() => {
      server.close();
      reject(new Error("Auth timed out after 5 minutes"));
    }, 300_000);
  });

  // Exchange the authorisation code for an access token
  const { body: tokenBody } = await httpsPost(
    "https://stackoverflow.com/oauth/access_token",
    { client_id: clientId, client_secret: clientSecret, code, redirect_uri: redirectUri }
  );

  const tokenParams = new URLSearchParams(tokenBody);
  const accessToken = tokenParams.get("access_token");

  if (!accessToken) {
    throw new Error(`Token exchange failed: ${tokenBody}`);
  }

  await context.secrets.store("soAccessToken", accessToken);
  vscode.window.showInformationMessage(
    "Stack Overflow connected! Your next capsule can be posted directly."
  );
}

async function disconnectStackOverflow(context) {
  await context.secrets.delete("soAccessToken");
  vscode.window.showInformationMessage("Stack Overflow disconnected.");
}

// ── Stack Exchange API ────────────────────────────────────────────────────────

async function postQuestion(context, capsule) {
  const accessToken = await context.secrets.get("soAccessToken");

  if (!accessToken) {
    const action = await vscode.window.showErrorMessage(
      "Not connected to Stack Overflow.",
      "Connect Now"
    );
    if (action) {
      await connectStackOverflow(context);
    }
    return;
  }

  const config = vscode.workspace.getConfiguration("resolutionCapsule");
  const apiKey = config.get("stackOverflow.apiKey", "");

  // Stack Overflow tags: max 5, each <= 25 chars, semicolon-delimited
  const tags = capsule.tags
    .map((t) => t.slice(0, 25))
    .slice(0, 5)
    .join(";");

  const params = {
    site: "stackoverflow",
    access_token: accessToken,
    title: capsule.title.slice(0, 150),
    body: capsule.markdown,
    tags,
  };
  if (apiKey) params.key = apiKey;

  const { body } = await httpsPost("https://api.stackexchange.com/2.3/questions/add", params);
  const data = JSON.parse(body);

  if (data.error_id) {
    throw new Error(`Stack Exchange error ${data.error_id}: ${data.error_message}`);
  }

  const question = data.items?.[0];
  if (!question) {
    throw new Error("No question returned from API.");
  }

  const action = await vscode.window.showInformationMessage(
    "Posted to Stack Overflow!",
    "Open Question"
  );
  if (action) {
    vscode.env.openExternal(vscode.Uri.parse(question.link));
  }
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = http.createServer();
    server.listen(0, "127.0.0.1", () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
    server.on("error", reject);
  });
}

function httpsPost(url, bodyObj) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const data = new URLSearchParams(bodyObj).toString();

    const req = https.request(
      {
        hostname: parsed.hostname,
        path: parsed.pathname + parsed.search,
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "Content-Length": Buffer.byteLength(data),
          "Accept-Encoding": "gzip",
        },
      },
      (res) => {
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          const buffer = Buffer.concat(chunks);
          if (res.headers["content-encoding"] === "gzip") {
            zlib.gunzip(buffer, (err, decoded) => {
              if (err) reject(err);
              else resolve({ status: res.statusCode, body: decoded.toString() });
            });
          } else {
            resolve({ status: res.statusCode, body: buffer.toString() });
          }
        });
      }
    );

    req.on("error", reject);
    req.write(data);
    req.end();
  });
}

function deactivate() {}

module.exports = { activate, deactivate };
