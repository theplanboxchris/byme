# 🧠 Claude Code – Setup Guide (PowerShell + VS Code)

## 1. Open PowerShell
Optional: navigate to your project folder  
```powershell
cd C:\path\to\project
```

## 2. Launch Claude Code CLI
```powershell
claude
```

This opens the interactive Claude Code CLI.

## 3. Log in to Anthropic
```powershell
claude login
```
A browser window will open. Sign in to your Anthropic account and approve access.  
Your credentials will be stored locally for future use.

## 4. Authorize VS Code
```powershell
claude auth vscode
```
This connects your Anthropic credentials with VS Code.

## 5. Launch VS Code
```powershell
code .
```
Run this from the same terminal so VS Code inherits the environment.

## 6. Use Claude in VS Code
- Open the **Claude Code** extension panel.
- Start chatting or use inline completions (e.g. `Ctrl+Shift+I`).
- You’re ready to code with Claude!


We will assume that Claude is available for assistance inside VS code

Use it for code generation rather than terminal execution (you can use a lot of credits running terminal commands)