const vscode = require("vscode");
const cp = require("child_process");
const fs = require("fs");
const path = require("path");

let extensionContext;

function activate(context) {
  extensionContext = context;
  context.subscriptions.push(
    vscode.commands.registerCommand("resolutionCapsule.createFromSelection", createFromSelection),
    vscode.commands.registerCommand("resolutionCapsule.createFromPrompts", createFromPrompts)
  );
}

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

  await generate({
    problem: "Captured from editor selection",
    error: selected,
    rootCause,
    fix,
  });
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
        vscode.window.showErrorMessage(`Resolution Capsule: unexpected output — ${stdout.slice(0, 120)}`);
        return;
      }

      const doc = await vscode.workspace.openTextDocument({
        content: result.markdown,
        language: "markdown",
      });
      await vscode.window.showTextDocument(doc, { preview: false });
      vscode.window.showInformationMessage(`Capsule generated: ${result.confidence}`);
    }
  );
}

function findEnginePath(repoRoot, extensionPath) {
  const candidates = [
    path.join(repoRoot, "capsule_cli.py"),
    path.join(extensionPath, "..", "capsule_cli.py"),
  ];
  return candidates.find((candidate) => fs.existsSync(candidate)) || candidates[0];
}

function deactivate() {}

module.exports = { activate, deactivate };
