# Vasool

> "Vasool remembers every promise your customers make, so you never chase blindly again."

**AI-powered collections assistant for Indian B2B trade credit** | Built with [Hindsight](https://github.com/vectorize-io/hindsight) agent memory and Groq LLM inference

---

## 🎯 The Problem

In India, small and medium enterprises (MSMEs) operate heavily on informal commercial credit. On paper, credit terms are typically 15 to 30 days. In reality, businesses regularly wait **60 to 120+ days** for payment.

### The Core Issues

- **History lives in the owner's head** — Critical interaction context—who promised to pay on Friday, whose client cheque cleared, who requested an extension for GST filing—is scattered across personal chats and memory.

- **Defaulters exploit statelessness** — Chronic late payers repeat identical excuses ("client payment stuck", "bank server down", "accountant on leave") across weeks without accountability because there's no institutional memory.

- **Dilemma between passivity and damaged relationships** — Sellers either send passive, automated reminders that chronic defaulters ignore, or escalate too aggressively, damaging valuable commercial relationships.

---

## ✅ Solution Overview

Vasool replaces stateless, generic reminders with an **agentic memory architecture**:

1. **Episodic Interaction Tracking** — Every invoice, reminder, WhatsApp reply, excuse, commitment date, and cleared payment is retained as a dated event in customer memory.

2. **Behavioral Profile Synthesis** — Using semantic reflection over past interactions, Vasool deduces the buyer's payment pattern (e.g., "always slips promises by 5–7 days", "requires a phone call before paying").

3. **Calibrated Payment Forecasting** — Rather than relying on static due dates, the system forecasts the expected realization date based on empirical settlement behavior.

4. **Contextual Follow-ups** — The agent drafts personalized WhatsApp messages tailored to the buyer's communication style (including natural Hinglish) while diplomatically referencing prior commitments.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Streamlit Web Interface                       │
│  [Today's Plan] [Buyer Memory] [Simulator] [Backtest]   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│           Vasool Agent Core (agent.py)                  │
│                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ daily_plan() │ │predict_payment│ │draft_message │   │
│  └──────────────┘ └──────────────┘ └──────────────┘   │
│         ↓              ↓                   ↓            │
│         └──────────────┼───────────────────┘            │
│                        ↓                                │
│        ┌───────────────┴──────────────┐                │
│        ↓                              ↓                │
│ ┌─────────────────┐        ┌─────────────────┐        │
│ │ Hindsight Client│        │  Groq Client    │        │
│ └─────────────────┘        └─────────────────┘        │
└─────────────────────────────────────────────────────────┘
        ↓                              ↓
┌─────────────────────┐  ┌──────────────────────────┐
│ Hindsight Memory    │  │ Groq LPU Inference       │
│ (api.hindsight...)  │  │ (openai/gpt-oss-120b)    │
│                     │  │                          │
│ • Retain: Store     │  │ • Context inference      │
│ • Recall: Search    │  │ • Payment date est.      │
│ • Reflect: Synth.   │  │ • Message drafting       │
└─────────────────────┘  └──────────────────────────┘
        ↑
        │
    ┌───┴─────────────┐
    │  Data Layer     │
    │ • events.json   │
    │ • backtest...   │
    └─────────────────┘
```

---

## 🛠️ Tech Stack

| Technology | Role | Details |
|:---|:---|:---|
| **Python 3.10+** | Language & Runtime | Core application logic, async-safe client integration, and data processing. |
| **Streamlit** | Frontend / UI | Multi-tab command center with interactive KPIs, memory timeline, and simulator. |
| **Hindsight Cloud** | Long-Term Agent Memory | Vectorize-managed memory engine supporting `retain`, `recall`, and `reflect` APIs. |
| **Groq** | High-Speed LLM Inference | Ultra-low-latency model execution (`openai/gpt-oss-120b` with fallback to `gpt-oss-20b` and `qwen3.8-27b`). |
| **pandas** | Data Manipulation | Event parsing, invoice state tracking, and tabular aggregation. |
| **Plotly** | Visualization | Interactive aging distribution and empirical learning curve plots. |

---

## 🔄 How Hindsight Is Used

Vasool leverages the three core primitives of [Hindsight Agent Memory](https://vectorize.io/what-is-agent-memory):

| Operation | Hindsight API Call | Implementation in Vasool |
|:---|:---|:---|
| **Retain** | `client.retain(bank_id, content, context)` | Ingests atomic interaction records: invoices dispatched, payment reminders sent, buyer responses (commitments, hardship reasons, delays), and payment clearance confirmations. |
| **Recall** | `client.recall(bank_id, query)` | Fetches relevant chronological history for a specific buyer. Retrieves past promises, specific dates committed, excuse patterns, and communication channels. |
| **Reflect** | `client.reflect(bank_id, query)` | Performs higher-order synthesis over stored memories. Extracts the buyer's true payment behavior, evaluates whether they reliably honor commitments, and infers behavioral archetypes. |

---

## 📖 Setup Instructions

### Prerequisites
- Python 3.10 or higher
- Git installed
- API keys from [Vectorize/Hindsight](https://hindsight.vectorize.io/) and [Groq Console](https://console.groq.com)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/vasool.git
cd vasool
```

### 2. Create and Activate a Virtual Environment

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

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:
```env
HINDSIGHT_API_KEY=your_hindsight_api_key_here
GROQ_API_KEY=your_groq_api_key_here
HINDSIGHT_BANK_ID=vasool-demo
```

Get your API keys from:
- Hindsight: [https://hindsight.vectorize.io/](https://hindsight.vectorize.io/)
- Groq: [https://console.groq.com](https://console.groq.com)

### 5. Generate Synthetic Data

Generates a 6-month interaction history (invoices, reminders, buyer replies, payment events) across 20 simulated Indian business buyers:
```bash
python generate_data.py
```

This produces `data/events.json`.

### 6. Load Memory into Hindsight

Seeds the generated events into your Hindsight memory bank:
```bash
python load_memory.py
```

### 7. Run the Streamlit Application
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501` (or the port displayed in your terminal).

---

## 📁 Project Structure

```
Vasool/
├── .env                     # API keys & environment configuration (not committed)
├── .gitignore               # Ignored files, cache directories, and virtual environments
├── README.md                # Project documentation and specifications
├── requirements.txt         # Core dependencies (streamlit, hindsight-client, groq, etc.)
├── agent.py                 # Core agent logic: memory recall/reflect, Groq inference, planning
├── app.py                   # Streamlit web application (4 interactive tabs)
├── backtest.py              # Quantitative evaluation of memory size vs. prediction error
├── generate_data.py         # Synthetic 6-month event generator for 20 buyer archetypes
├── load_memory.py           # Ingestion script to seed events.json into Hindsight Cloud
├── test_agent.py            # Quick sanity test script for individual agent functions
└── data/
    ├── events.json          # Master event ledger (invoices, reminders, replies, payments)
    └── backtest_results.json# Serialized evaluation results for the Learning Curve tab
```

---

## ⚠️ Honest Limitations

1. **Synthetic Data** — The system is evaluated on a synthetic 6-month event stream representing 20 Indian MSME buyers. While behavior archetypes ("always slips", "pays after call", "pays after 10th") are realistic, real-world precision awaits production data.

2. **No Real WhatsApp API Yet** — Follow-up messages and simulated conversations are generated and formatted for WhatsApp, but are not yet delivered via the Meta WhatsApp Cloud API or an SMS gateway. Currently demonstrates draft copy only.

3. **No Real Accounting Integration** — There is currently no direct connector to ERP or accounting platforms (e.g., TallyPrime, Zoho Books, Busy, QuickBooks). Invoice generation and payment reconciliation use synthetic data.

---

## 🚀 Roadmap

- [ ] **WhatsApp Business API Integration** — Direct two-way messaging with read receipts, delivery tracking, and automatic inbound reply ingestion into Hindsight.
- [ ] **Tally & Zoho Books Import** — One-click synchronization of outstanding bills, debtor ledgers, and bank reconciliation receipts.
- [ ] **Embedded Payment Links** — Generation of dynamic UPI payment links and QR codes (via Razorpay or Cashfree) embedded directly into WhatsApp reminder copy.
- [ ] **Voice Notes & Audio Follow-ups** — Speech-to-text parsing for WhatsApp audio notes and recorded phone call summaries into the memory bank.
- [ ] **Regional Language Generation** — Native message generation and sentiment analysis in Hindi, Gujarati, Marathi, Tamil, Telugu, and Kannada, extending beyond English and Hinglish.
- [ ] **Multi-Client CA Mode** — Multi-tenant memory segmentation allowing Chartered Accountants and outsourced CFO firms to manage collections across multiple client businesses simultaneously.

---

## 📚 References & Links

- **Hindsight Repository** — [https://github.com/vectorize-io/hindsight](https://github.com/vectorize-io/hindsight)
- **Hindsight Documentation** — [https://hindsight.vectorize.io/](https://hindsight.vectorize.io/)
- **Vectorize Agent Memory** — [https://vectorize.io/what-is-agent-memory](https://vectorize.io/what-is-agent-memory)
