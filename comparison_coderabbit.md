# 🛡️ PR Guard vs. 🐇 CodeRabbit: Comparison

This document provides a detailed comparison between **PR Guard** and **CodeRabbit**. While CodeRabbit is a market leader in AI-driven code reviews, PR Guard is designed as a focused, privacy-first internal tool for teams who prefer local control and minimal overhead.

## 📊 Overview at a Glance

| Feature | CodeRabbit | PR Guard |
| :--- | :--- | :--- |
| **Primary Use Case** | Enterprise-grade automated SaaS reviews | Privacy-first local/internal review tool |
| **Pricing** | $24-$30/month per developer (Pro) | **Free** (MIT Licensed, Pay only for AI tokens) |
| **Local Usage** | Limited (Mainly via IDE/CLI plugins) | **Native CLI first**, built for local terminal use |
| **Data Privacy** | Cloud-based (SOC2 compliant) | **Full Privacy** (Can run with local LLMs) |
| **Setup Complexity**| Configuration via GitHub/GitLab App | **One-liner installation** (minimal setup) |
| **Customizability** | High (via dashboard/yaml) | **Open Source** (Full control over logic & prompts) |

---

## 💰 Pricing Deep Dive

### CodeRabbit
CodeRabbit follows a standard SaaS "per-seat" pricing model:
- **Free Plan**: Only for Open Source projects.
- **Pro Plan**: **$24/month** (billed annually) or **$30/month** (monthly) per developer.
- **Enterprise**: Custom pricing for self-hosting and multi-org support.
- *Cost for a team of 10:* ~**$3,600/year**.

### PR Guard
PR Guard is an internal tool with no per-user licensing fees:
- **Open Source**: $0 licensing cost.
- **Infrastructure**: You only pay for what you use (OpenAI API tokens) or $0 if using a local LLM (like Ollama/Llama 3).
- *Cost for a team of 10:* **Minimal** (Token usage based on PR size).

---

## 🔒 Privacy & Local Use

### CodeRabbit (The Cloud Approach)
While CodeRabbit is highly secure (SOC2 Type II, GDPR), it is fundamentally a **cloud service**. Your code is transmitted to their servers for processing. For organizations with strict data residency requirements or air-gapped environments, this can be a hurdle.

### PR Guard (The Local Approach)
PR Guard is built with **privacy as a core pillar**:
- **Local LLM Support**: Can be configured to use local models (e.g., via Ollama), ensuring that code never leaves your workstation or internal network.
- **CLI-Centric**: Designed for developers who live in the terminal. You can review your changes *before* even pushing to the cloud.
- **Internal Ownership**: Since it is an internal tool, you own the logs, the data, and the execution environment.

---

## 🚀 Setup & Ease of Use

### CodeRabbit
Setting up CodeRabbit usually involves installing a GitHub/GitLab application and configuring repository-level permissions. It provides a polished dashboard for managing reviews across multiple repositories.

### PR Guard
PR Guard prioritizes **speed of adoption**:
- **One-Liner Install**
- **Minimal Setup**: Just add your API key to a `.env` file and run `pr-guard review`.
- **Developer Experience**: Uses the `rich` library to provide beautiful, interactive terminal output that fits perfectly into a developer's existing workflow.

---

## 🎯 Conclusion

**CodeRabbit** is "obviously better" in terms of its vast feature set, commercial support, and deep integrations with platforms like Jira/Linear. It is a polished, "set-and-forget" solution for teams with the budget for SaaS tools.

**PR Guard**, however, fills a critical gap for teams who:
1.  **Prioritize Privacy**: Need to keep code local or use internal LLMs.
2.  **Want a CLI Tool**: Prefer reviewing changes locally before sharing them.
3.  **Minimize Costs**: Want a high-quality AI reviewer without the per-seat monthly subscription.
4.  **Internal Tooling**: Want a tool they can tweak, extend, and own as part of their internal engineering excellence.

*PR Guard is your high-performance, private alternative to the SaaS giants.*
