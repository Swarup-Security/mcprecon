# mcprecon

**AI / MCP Reconnaissance & Security Audit Framework**

mcprecon is a reconnaissance and auditing tool designed to map the attack surface of modern AI environments, including **Model Context Protocol (MCP) servers**, agent frameworks, and local LLM runtimes.

> **AI is no longer just a model—it is an execution layer.**

---

## 🔍 Overview

Modern AI systems are rapidly evolving into **connected execution environments**.

With MCP and agent frameworks, LLMs can:

* Execute tools and scripts
* Access local files and system resources
* Interact with APIs and remote services

However, there is often **limited visibility into granted permissions and capabilities**.

**mcprecon helps answer:**

* What AI components exist on this system?
* What capabilities do they expose?
* Where are the potential security risks?

---

## ⚡ Features

### 🖥️ System Reconnaissance

* OS and host information discovery
* GPU detection
* Installed tools enumeration

### 🤖 AI Environment Discovery

* LLM runtimes (e.g., Ollama)
* Agent frameworks (e.g., LangChain)
* MCP servers (local and remote)

### 🌐 MCP Enumeration

* Detect exposed MCP endpoints
* Identify exposed tools and potential execution capabilities

### 🔐 Security Auditing

* Over-permissioned MCP configurations
* Agent capability analysis
* System-level privilege exposure

### 🔑 Secret Detection

* API key discovery (environment + config)
* Sensitive data exposure risks

### 📊 Reporting

* Colorized terminal output
* HTML report generation

---

## 🧠 How It Works

mcprecon follows a **two-phase approach**:

### 1. Reconnaissance

Identify AI components and infrastructure:

* MCP servers
* Agent frameworks
* LLM runtimes

### 2. Security Audit

Analyze risk and exposure:

* Permissions and capabilities
* Secret leakage
* Trust relationships

> Clear separation between *what exists* and *what is potentially dangerous*

---

## 🛠️ Installation

```bash
git clone https://github.com/Swarup-Security/mcprecon.git
cd mcprecon
pip install -r requirements.txt
```

---
Installation of requirements.txt is optional unless you want to perform a GPU detection

## ▶️ Usage

Run a full scan:

```bash
python3 main.py
```

Generate an HTML report:

```bash
python3 main.py --html report.html
```

---

## 📸 Example Findings

mcprecon can identify:

* Unauthenticated MCP servers exposing tool interfaces without authentication
* AI agents with filesystem and network access
* Leaked API keys in environment variables or configuration files
* Over-privileged execution environments
* Implicit trust relationships between AI components

---

## ⚠️ Why This Matters

AI agents are increasingly integrated into development and production environments.

In many cases:

> Installing an MCP server is equivalent to installing an **unmonitored plugin with system-level access**

Without proper auditing, this can lead to:

* Potential arbitrary command execution depending on tool configuration
* Data exfiltration risks
* Privilege escalation opportunities

---

## 🔍 Detection vs Exploitation

mcprecon focuses on **reconnaissance and security auditing**.

* ✔ Identifies exposed MCP endpoints and capabilities
* ✔ Highlights potential security risks
* ❌ Does not perform active exploitation by default

> This design ensures safe usage in development and assessment environments.

---

## 🧪 Demo Scenario (Conference Use)

A typical mcprecon assessment may reveal:

1. An MCP server running locally or on a reachable network port
2. Tool interfaces exposed without authentication
3. Agent frameworks with access to filesystem or external APIs
4. Sensitive API keys present in environment or config files

These findings demonstrate how AI environments can introduce **implicit trust chains** and **expanded attack surfaces**, even without active exploitation.

---

## 🧪 Use Cases

* 🔴 Red Team: Reconnaissance of AI environments
* 🔵 Blue Team: Security auditing and validation
* 🧑‍💻 Developers: Understanding AI system capabilities
* 🔬 Researchers: Exploring MCP and AI attack surfaces

---

## 🚀 Roadmap

* Safe validation of tool execution boundaries
* Active attack simulation (prompt injection, tool misuse)
* Risk scoring (CVSS-style)
* CI/CD integration
* Advanced secret scanning
* MCP fuzzing and exploitation modules

---

## 📢 Research & Conference Work

This project is part of ongoing research into **AI execution-layer security** and MCP ecosystems.

**Core Idea:**

> AI systems should be treated as **attack surfaces**, not just applications.

---

## 🤝 Contributing

Contributions and research discussions are welcome.

Feel free to:

* Open issues
* Suggest features
* Share security findings

---

## ⚖️ Disclaimer

This tool is intended for **educational and authorized security testing purposes only**.

Do not use it on systems without proper permission.

---

## 👤 Author

**Swarup N**
Security Researcher | AI Security

---
