# Project Proposal: DeepWiki & Vapi Onboarding Assistant – VS Code Extension

## 1. Abstract
This project proposes the development of a **native Visual Studio Code (VS Code) Extension** aimed at streamlining the onboarding process for new developers. Running entirely within the VS Code Extension Host process, this plug-in integrates the **Vapi (Voice AI / Chat)** platform and the **DeepWiki knowledge base** directly into the developer's IDE.

The extension provisions a dedicated VS Code Webview panel that acts as a conversational interface. When a developer asks a question about the codebase, the extension intercepts the query, fetches relevant architectural guidelines and documentation from DeepWiki (using Retrieval-Augmented Generation - RAG), and feeds this context to Vapi's AI models. This ensures the AI provides highly accurate, project-specific answers without the developer ever leaving their code.

## 2. Target Audience & Core Problem
* **Users:** New hires, software developers, and DevOps engineers adapting to a new codebase.
* **The Problem:** Fragmented knowledge and severe context switching. New developers lose hours searching through external wikis (DeepWiki) or generic AI chats that lack project-specific context. 
* **The Solution:** A fully integrated `.vsix` extension that acts as an embedded "Senior Developer." It natively understands the company's internal documentation and code standards, answering questions directly in the IDE.

## 3. Technology Stack & Ecosystem
* **Environment:** Visual Studio Code Extension API (`import * as vscode from 'vscode'`).
* **Runtime:** Node.js (VS Code Extension Host process).
* **Language:** Strict TypeScript.
* **UI Layer:** VS Code Webview API (HTML5, CSS3, Vanilla JS/React), styled using VS Code's native CSS variables (`var(--vscode-*)`).
* **Network & Integrations:** * **DeepWiki API:** HTTP/REST for fetching markdown docs, internal rules, and context retrieval (RAG).
  * **Vapi API:** REST / WebSockets for AI chat and voice generation.
* **Build Tools:** Webpack or esbuild (for fast activation), vsce (for `.vsix` packaging).

## 4. LLM Implementation Context & Directives
*To any AI coding assistant reading this repository: Do not generate code for a standalone React or Next.js app. This is strictly a VS Code Extension. Adhere to the following architectural rules:*

* **Strict Extension Architecture:** Use `package.json` for Manifest definitions (activation events, commands) and `src/extension.ts` as the main entry point.
* **RAG Flow (DeepWiki -> Vapi):** The Extension Host must orchestrate the RAG flow. Before sending a user prompt to Vapi, fetch the relevant context from DeepWiki API, build an *Augmented Prompt*, and then send it to Vapi.
* **Webview Isolation:** UI components MUST live entirely within the Webview context. The Extension Host (`src/extension.ts`, `vapiClient.ts`, `deepWikiClient.ts`) acts as the backend.
* **Message Passing (IPC):** Communication between the Webview UI and the Extension Host must strictly use `acquireVsCodeApi().postMessage()` and `webview.onDidReceiveMessage`. Never manipulate the DOM from the Extension Host.
* **Native VS Code Features:** * Use `vscode.window.showInformationMessage` for alerts.
  * Use `context.secrets` for storing Vapi and DeepWiki API keys.
  * Push all disposables (event listeners, Webviews) to `context.subscriptions` to prevent memory leaks.