<div align="center">

# 💼 Vasool
### AI-Powered Collections Assistant for Indian B2B Trade Credit

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Hindsight](https://img.shields.io/badge/Hindsight-Memory-6F42C1?logoColor=white)](https://vectorize.io/)
[![Groq](https://img.shields.io/badge/Groq-LLM-000000?logoColor=white)](https://groq.com/)

> *"Vasool remembers every promise your customers make, so you never chase blindly again."*

**[📖 Documentation](#-setup-instructions) • [🏗️ Architecture](#-architecture) • [🛠️ Tech Stack](#-tech-stack) • [📋 Roadmap](#-roadmap)**

</div>

---

## 🎯 The Problem

<table>
  <tr>
    <td width="50%">

In India, small and medium enterprises (MSMEs) operate heavily on informal commercial credit. On paper, credit terms are typically 15 to 30 days. In reality, businesses regularly wait **60 to 120+ days** for payment.

**The core failure mode is informational:**

    </td>
    <td width="50%">
      <img src="https://img.shields.io/badge/💔-60%20to%20120%20day%20delays-red?style=flat-square" />
    </td>
  </tr>
</table>

### Key Pain Points

🧠 **History lives in the owner's head**  
Critical interaction context—who promised to pay on Friday, whose client cheque cleared, who requested an extension for GST filing—is scattered across personal chats, notebooks, and memory.

😤 **Defaulters exploit statelessness**  
Chronic late payers repeat identical excuses ("client payment stuck", "bank server down", "accountant on leave") across weeks without accountability because there's no institutional memory.

⚖️ **Dilemma between passivity and damaged relationships**  
Sellers either send passive, automated reminders that chronic defaulters ignore, or escalate too aggressively, damaging valuable commercial relationships.

---

## 💡 Solution Overview

<div align="center">

**Vasool replaces stateless, generic reminders with an agentic memory architecture:**

</div>

| # | Feature | Description |
|---|---------|-------------|
| 📊 | **Episodic Interaction Tracking** | Every invoice, reminder, WhatsApp reply, excuse, commitment date, and cleared payment is retained as a dated event in customer memory. |
| 🧬 | **Behavioral Profile Synthesis** | Using semantic reflection over past interactions, Vasool deduces the buyer's payment pattern (e.g., "always slips promises by 5–7 days", "requires a phone call before paying"). |
| 📈 | **Calibrated Payment Forecasting** | Rather than relying on static due dates, the system forecasts the expected realization date based on empirical settlement behavior. |
| 💬 | **Contextual Follow-ups** | The agent drafts personalized WhatsApp messages tailored to the buyer's communication style (including natural Hinglish) while diplomatically referencing prior commitments. |

---

## 🏗️ Architecture

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                      📱 Streamlit Web Interface                            ║
║  [Today's Plan] [Buyer Memory] [Simulator] [Learning Curve Backtest]      ║
╚═══════════════════════════════════════════════════════════════════════════╝
                                    │
                                    ▼
╔═══════════════════════════════════════════════════════════════════════════╗
║                         🤖 Vasool Agent Core                              ║
║                            (agent.py)                                      ║
║                                                                            ║
║  ┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐          ║
║  │  daily_plan()  │  │predict_payment() │  │ draft_message()  │          ║
║  └────────────────┘  └──────────────────┘  └──────────────────┘          ║
║         │                    │                       │                    ║
║         └────────────────────┼───────────────────────┘                    ║
║                              │                                             ║
║                ┌─────────────┴─────────────┐                              ║
║                │                           │                              ║
║                ▼                           ▼                              ║
║     ┌──────────────────────┐    ┌────────────────────┐                   ║
║     │ Hindsight Client     │    │   Groq Client      │                   ║
║     │ (hindsight-client)   │    │  (groq-python)     │                   ║
║     └──────────┬───────────┘    └────────┬───────────┘                   ║
╚────────────────┼────────────────────────┼──────────────────────────────╝
                 │                        │
                 ▼                        ▼
╔════════════════════════════╗  ╔═══════════════════════════════════╗
║ 🧠 Hindsight Memory Bank   ║  ║ ⚡ Groq LPU Inference             ║
║ (api.hindsight.vectorize)  ║  ║ (openai/gpt-oss-120b)             ║
║                            ║  ║                                   ║
║ • Retain: Store events     ║  ║ • Context-conditioned inference   ║
║ • Recall: Search history   ║  ║ • Payment date estimation         ║
║ • Reflect: Synthesize      ║  ║ • Tone-adaptive messaging         ║
╚════════════════════════════╝  ╚═══════════════════════════════════╝
                 ▲
                 │
╔════════════════┴───────────────────────╗
║       💾 Data Layer                     ║
║  • data/events.json                    ║
║  • data/backtest_results.json          ║
╚────────────────────────────────────────╝
```

---

## 🛠️ Tech Stack

| Technology | Role | Details |
|:---|:---|:---|
| ![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white) | **Language & Runtime** | Core application logic, async-safe client integration, and data processing. |
| ![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?logo=streamlit&logoColor=white) | **Frontend / UI** | Multi-tab command center with interactive KPIs, memory timeline, and simulator. |
| ![Hindsight](https://img.shields.io/badge/Hindsight-Memory-6F42C1) | **Long-Term Agent Memory** | Vectorize-managed memory engine supporting `retain`, `recall`, and `reflect` APIs. |
| ![Groq](https://img.shields.io/badge/Groq-LLM-000000) | **High-Speed LLM Inference** | Ultra-low-latency model execution with fallbacks. |
| ![pandas](https://img.shields.io/badge/pandas-Data-150458?logo=pandas&logoColor=white) | **Data Manipulation** | Event parsing, invoice state tracking, and tabular aggregation. |
| ![Plotly](https://img.shields.io/badge/Plotly-Visualization-239DAD?logo=plotly&logoColor=white) | **Visualization** | Interactive aging distribution and empirical learning curve plots. |

---

## 🔄 How Hindsight Is Used

Vasool leverages the **three core primitives** of [Hindsight Agent Memory](https://vectorize.io/what-is-agent-memory):

| Operation | Hindsight API | Implementation in Vasool |
|:---|:---|:---|
| **🔖 Retain** | `client.retain(bank_id, content, context)` | Ingests atomic interaction records: invoices dispatched, payment reminders sent, buyer responses (commitments, hardship reasons, delays), and payment clearance confirmations. |
| **🔍 Recall** | `client.recall(bank_id, query)` | Fetches relevant chronological history for a specific buyer. Retrieves past promises, specific dates committed, excuse patterns, and communication channels. |
| **💭 Reflect** | `client.reflect(bank_id, query)` | Performs higher-order synthesis over stored memories. Extracts the buyer's true payment behavior, evaluates whether they reliably honor commitments, and infers behavioral archetypes. |

---

## 📖 Setup Instructions

### ✅ Prerequisites
- **Python 3.10+** installed
- **Git** installed
- API Keys: [Hindsight](https://hindsight.vectorize.io/) & [Groq](https://console.groq.com)

---

### 📝 Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/vasool.git
cd vasool
```

### 🐍 Step 2: Create and Activate a Virtual Environment

**On Linux / macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 📦 Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### 🔑 Step 4: Configure Environment Variables

Create a `.env` file in the project root:
```env
HINDSIGHT_API_KEY=your_hindsight_api_key_here
GROQ_API_KEY=your_groq_api_key_here
HINDSIGHT_BANK_ID=vasool-demo
```
> 💡 Get a Hindsight key from [Vectorize](https://hindsight.vectorize.io/) and a Groq key from [Groq Console](https://console.groq.com)

### 🎲 Step 5: Generate Synthetic Data
Generates a 6-month interaction history across 20 simulated Indian business buyers:
```bash
python generate_data.py
```
✨ This produces `data/events.json`

### 💾 Step 6: Load Memory into Hindsight
Seeds the generated events into your Hindsight memory bank:
```bash
python load_memory.py
```

### 🚀 Step 7: Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501` (or the port displayed in your terminal).

---

## 📁 Project Structure

```
Vasool/
│
├── 📄 README.md                    # Project documentation
├── 📋 requirements.txt             # Python dependencies
├── 🔑 .env                         # API keys (not committed)
├── ❌ .gitignore                   # Git ignore rules
│
├── 🤖 Core Modules
│   ├── agent.py                    # Agent logic: memory recall/reflect, Groq inference
│   ├── app.py                      # Streamlit web application (4 interactive tabs)
│   └── backtest.py                 # Quantitative evaluation of memory vs. prediction error
│
├── ⚙️ Setup & Utilities
│   ├── generate_data.py            # Synthetic 6-month event generator
│   ├── load_memory.py              # Ingestion script to seed Hindsight Cloud
│   └── test_agent.py               # Quick sanity tests
│
└── 💾 data/
    ├── events.json                 # Master event ledger
    └── backtest_results.json       # Evaluation results for Learning Curve tab
```

---

## ⚠️ Honest Limitations

| Limitation | Impact | Future |
|:---|:---|:---|
| **📊 Synthetic Data** | The system is evaluated on a synthetic 6-month event stream representing 20 Indian MSME buyers. While behavior archetypes ("always slips", "pays after call", "pays after 10th") are realistic, real-world precision awaits production data. | Real-world validation required |
| **💬 No Real WhatsApp API Yet** | Follow-up messages and simulated conversations are generated and formatted for WhatsApp, but are not yet delivered via the Meta WhatsApp Cloud API or an SMS gateway. Only demonstrates draft copy. | Q3-Q4 2024 |
| **🏦 No Real Accounting Integration** | There is currently no direct connector to ERP or accounting platforms (e.g., TallyPrime, Zoho Books, Busy, QuickBooks). Invoice generation and payment reconciliation use synthetic data. | Q4 2024 - Q1 2025 |

---

## 🚀 Roadmap

- [ ] **📱 WhatsApp Business API Integration** — Direct two-way messaging with read receipts, delivery tracking, and automatic inbound reply ingestion into Hindsight.
- [ ] **📊 Tally & Zoho Books Import** — One-click synchronization of outstanding bills, debtor ledgers, and bank reconciliation receipts.
- [ ] **💳 Embedded Payment Links** — Generation of dynamic UPI payment links and QR codes (via Razorpay or Cashfree) embedded directly into WhatsApp reminder copy.
- [ ] **🎙️ Voice Notes & Audio Follow-ups** — Speech-to-text parsing for WhatsApp audio notes and recorded phone call summaries into the memory bank.
- [ ] **🌐 Regional Language Generation** — Native message generation and sentiment analysis in Hindi, Gujarati, Marathi, Tamil, Telugu, and Kannada, extending beyond English and Hinglish.
- [ ] **👥 Multi-Client CA Mode** — Multi-tenant memory segmentation allowing Chartered Accountants and outsourced CFO firms to manage collections across multiple client businesses simultaneously.

---

## 📚 References & Links

<div align="center">

| Resource | Link |
|:---|:---|
| **Hindsight Repository** | [🔗 vectorize-io/hindsight](https://github.com/vectorize-io/hindsight) |
| **Hindsight Docs** | [📖 hindsight.vectorize.io](https://hindsight.vectorize.io/) |
| **Vectorize Agent Memory** | [🧠 vectorize.io/what-is-agent-memory](https://vectorize.io/what-is-agent-memory) |

</div>

---

<div align="center">

### 🎉 Built with ❤️ for Indian MSMEs

**Questions? Issues? Feedback?** Open a GitHub issue or contribute a pull request!

[![GitHub Issues](https://img.shields.io/badge/GitHub-Issues-blue?logo=github)](https://github.com/GADDAMPAVANSIVAKRISHNA/Vasool/issues)
[![GitHub Pull Requests](https://img.shields.io/badge/GitHub-PRs-green?logo=github)](https://github.com/GADDAMPAVANSIVAKRISHNA/Vasool/pulls)

</div>