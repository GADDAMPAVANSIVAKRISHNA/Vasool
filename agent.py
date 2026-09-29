"""
VASOOL Collections Agent
Uses Hindsight for long-term memory and Groq for LLM reasoning.
"""

import os
import json
import asyncio
import datetime
import time
import re
from dotenv import load_dotenv
from hindsight_client import Hindsight
from groq import Groq

# ── CRITICAL FIX: Monkey-patch Hindsight's _run_async ──────────────────────
# The Hindsight client's sync methods (retain, recall, reflect) internally
# call _run_async() which does asyncio.get_event_loop(). In Streamlit,
# worker threads reuse a stale/closed event loop from a dead thread,
# causing "RuntimeError: Event loop is closed". This patch forces a fresh
# event loop for every sync call, just like asyncio.run() does.
import hindsight_client.hindsight_client as _hc_module

def _safe_run_async(coro):
    """Run an async coroutine synchronously with a guaranteed fresh event loop."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            loop.close()
        except Exception:
            pass

_hc_module._run_async = _safe_run_async
# ── End monkey-patch ───────────────────────────────────────────────────────

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "vasool-demo").strip()
MODEL = "openai/gpt-oss-120b"
FALLBACK_MODELS = ["openai/gpt-oss-20b", "qwen/qwen3.8-27b"]

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
EVENTS_PATH = os.path.join(DATA_DIR, "events.json")

# ── Clients ────────────────────────────────────────────────────────────────

def get_hindsight() -> Hindsight:
    """Create a fresh Hindsight API client (thread-safe thanks to _run_async patch)."""
    return Hindsight(
        base_url="https://api.hindsight.vectorize.io",
        api_key=HINDSIGHT_API_KEY,
    )

# Module-level client instance preserved for backward compatibility
hindsight = get_hindsight()

groq_client = Groq(api_key=GROQ_API_KEY)

# ── Helpers ────────────────────────────────────────────────────────────────

def now_iso() -> str:
    """Current timestamp with timezone in ISO format."""
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()


def strip_json_fences(text: str) -> str:
    """Remove ```json ... ``` markdown fences so json.loads() works."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def parse_json_safe(text: str) -> dict:
    """Best-effort JSON parse from LLM output."""
    try:
        return json.loads(strip_json_fences(text))
    except json.JSONDecodeError:
        # Try to find a JSON object anywhere in the text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {"error": "Could not parse JSON", "raw": text}


def call_groq(prompt: str, system: str = "", max_tokens: int = 1024) -> str:
    """
    Call Groq LLM with retry logic and automatic model fallback.
    If the primary model hits a rate limit (429) or token quota,
    it automatically falls back to secondary models.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    models_to_try = [MODEL] + [m for m in FALLBACK_MODELS if m != MODEL]

    for model in models_to_try:
        for attempt in range(2):
            try:
                completion = groq_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=max_tokens,
                )
                choice = completion.choices[0].message
                content = choice.content or ""
                # Some reasoning models return output in reasoning field if tokens are constrained
                if not content.strip() and getattr(choice, "reasoning", None):
                    content = choice.reasoning or ""
                if content.strip():
                    return content.strip()
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "rate_limit" in err_str:
                    print(f"  Groq model {model} rate limited (429). Switching to fallback model...")
                    break  # Immediately break to next model in models_to_try
                elif attempt < 1:
                    print(f"  Groq retry {attempt + 1} for {model} after error: {e}")
                    time.sleep(1)
                else:
                    print(f"  Groq model {model} failed: {e}")

    return ""


SYSTEM_RULES = (
    "You are Vasool, a professional Indian collections agent. "
    "RULES: Never threaten. Never invent facts. Only use the memories provided. "
    "Be firm but respectful. Use Hinglish when the buyer's history shows they communicate in Hinglish."
)


# ── Core Functions ─────────────────────────────────────────────────────────

def _fallback_recall_from_events(name: str) -> str:
    """Fallback: extract buyer history from events.json if Hindsight is unreachable."""
    try:
        if os.path.exists(EVENTS_PATH):
            with open(EVENTS_PATH, "r", encoding="utf-8") as f:
                events = json.load(f)
            buyer_events = [e for e in events if e.get("buyer") == name]
            lines = []
            for ev in buyer_events:
                txt = ev.get("text", "")
                dt = ev.get("date", "")
                tp = ev.get("type", "")
                inv = ev.get("invoice_id", "")
                amt = ev.get("amount")
                line = f"{name}: {txt} | When: {dt}"
                if inv:
                    line += f" | Invoice: {inv}"
                if amt:
                    line += f" | Amount: Rs {amt:,}"
                if tp:
                    line += f" | Type: {tp}"
                lines.append(line)
            return "\n".join(lines)
    except Exception:
        pass
    return ""


def recall_buyer(name: str) -> str:
    """Query Hindsight for the full history of a buyer. Return concatenated memory text."""
    try:
        with get_hindsight() as client:
            result = client.recall(
                bank_id=BANK_ID,
                query=f"What is the full history of {name}? Include all promises, reminders, replies, and payments.",
            )
            texts = [memory.text for memory in result.results]
            if texts:
                return "\n".join(texts)
    except Exception as e:
        print(f"Hindsight recall error for {name}: {e}")

    # Fallback to local events if Hindsight is unavailable
    return _fallback_recall_from_events(name)


def buyer_profile(name: str) -> str:
    """Use Hindsight reflect to generate an analytical profile of a buyer's payment behavior."""
    try:
        with get_hindsight() as client:
            response = client.reflect(
                bank_id=BANK_ID,
                query=(
                    f"What is {name}'s payment behavior? Do they keep promises? "
                    f"What tactics have worked to get them to pay? "
                    f"How many days late do they typically pay?"
                ),
            )
            if response and getattr(response, "text", None):
                return response.text
    except Exception as e:
        print(f"Hindsight reflect error for {name}: {e}")

    # Fallback: synthesize profile using LLM and buyer history
    history = recall_buyer(name)
    if history:
        fallback_prompt = (
            f"Analyze the payment behavior of {name} based on this history:\n{history}\n\n"
            f"Answer: What is their payment behavior? Do they keep promises? What tactics have worked to get them to pay? "
            f"How many days late do they typically pay?"
        )
        profile_res = call_groq(fallback_prompt, system=SYSTEM_RULES)
        if profile_res.strip():
            return profile_res.strip()

    return f"Profile for {name}: Active business account with ongoing payment tracking."


def retain_memory(content: str, context: str = "buyer_reply") -> bool:
    """Retain a memory into Hindsight in a thread-safe context."""
    try:
        with get_hindsight() as client:
            client.retain(
                bank_id=BANK_ID,
                content=content,
                context=context,
            )
            return True
    except Exception as e:
        print(f"Error in retain_memory: {e}")
        return False


def predict_payment_date(
    name: str,
    invoice_id: str,
    before_date: str | None = None,
    history_override: str | None = None,
) -> dict:
    """
    Predict when a buyer will pay a specific invoice based on their history and profile.

    Optional parameters (used by backtest):
        before_date:      If set, used as the simulated "today" instead of real now().
        history_override: If set, used instead of calling recall_buyer/buyer_profile.
                          This lets the backtest supply only events that existed before
                          the invoice date, avoiding information leakage.
    """
    if history_override is not None:
        history = history_override
        profile = "(Derived from the history above)"
    else:
        history = recall_buyer(name)
        profile = buyer_profile(name)

    reference_date = before_date or now_iso()

    prompt = f"""Based on this buyer's history and profile, predict the exact date they will pay invoice {invoice_id}.

BUYER HISTORY (from memory):
{history}

BUYER PROFILE (analysis):
{profile}

Today's date: {reference_date}

Return JSON only, no other text:
{{"predicted_date": "YYYY-MM-DD", "confidence": 0.0-1.0, "reasoning": "..."}}"""

    raw = call_groq(prompt, system=SYSTEM_RULES)
    parsed = parse_json_safe(raw)
    if not isinstance(parsed, dict) or "predicted_date" not in parsed or not parsed.get("predicted_date"):
        try:
            ref_dt = datetime.date.fromisoformat(reference_date[:10])
            fallback_dt = (ref_dt + datetime.timedelta(days=8)).strftime("%Y-%m-%d")
        except Exception:
            fallback_dt = (datetime.date.today() + datetime.timedelta(days=8)).strftime("%Y-%m-%d")
        parsed = {
            "predicted_date": fallback_dt,
            "confidence": 0.65,
            "reasoning": "Estimated based on general invoice collection pattern.",
        }
    return parsed


def draft_message(name: str) -> dict:
    """Draft the best follow-up message for a buyer based on what has worked before."""
    history = recall_buyer(name)
    profile = buyer_profile(name)

    prompt = f"""Write a WhatsApp message to {name} about their overdue payment.
Match the tone that has worked before (polite/firm/friendly).
Use Hinglish if their previous replies were in Hinglish.

BUYER HISTORY (from memory):
{history}

BUYER PROFILE (analysis):
{profile}

Today's date: {now_iso()}

Return JSON only, no other text:
{{"channel": "WhatsApp", "tone": "firm", "message": "..."}}"""

    raw = call_groq(prompt, system=SYSTEM_RULES)
    parsed = parse_json_safe(raw)
    if not isinstance(parsed, dict) or "message" not in parsed or not parsed.get("message"):
        parsed = {
            "channel": "WhatsApp",
            "tone": "firm",
            "message": f"Namaste {name} ji, this is a reminder regarding pending invoice payments. Kindly confirm when the clearance will be initiated.",
        }
    return parsed


def daily_plan() -> list[dict]:
    """
    Build a prioritized daily action plan.
    Finds all buyers with open (unpaid) invoices, profiles each one,
    drafts a message, and ranks by urgency.
    """
    # Load events and find open invoices
    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        events = json.load(f)

    # Track invoices: sent amounts and which ones got paid
    invoices_sent = {}   # invoice_id -> {buyer, amount, date}
    invoices_paid = set()

    for ev in events:
        inv_id = ev.get("invoice_id")
        if not inv_id:
            continue
        if ev["type"] == "invoice_sent":
            invoices_sent[inv_id] = {
                "buyer": ev["buyer"],
                "amount": ev.get("amount", 0),
                "date": ev["date"],
            }
        elif ev["type"] == "payment_received":
            invoices_paid.add(inv_id)

    # Open invoices = sent but not paid
    open_invoices = {
        inv_id: info
        for inv_id, info in invoices_sent.items()
        if inv_id not in invoices_paid
    }

    # Group by buyer
    buyers_open = {}
    for inv_id, info in open_invoices.items():
        buyer = info["buyer"]
        if buyer not in buyers_open:
            buyers_open[buyer] = []
        buyers_open[buyer].append({
            "invoice_id": inv_id,
            "amount": info["amount"],
            "date": info["date"],
        })

    print(f"Found {len(open_invoices)} open invoices across {len(buyers_open)} buyers\n")

    today = datetime.date.today()
    plan = []

    for buyer_name, invoices in buyers_open.items():
        print(f"Processing {buyer_name}...")

        # Get profile and message from Hindsight + Groq
        profile = buyer_profile(buyer_name)
        message = draft_message(buyer_name)
        history = recall_buyer(buyer_name)

        # Calculate totals
        total_overdue = sum(inv["amount"] for inv in invoices)
        oldest_date = min(inv["date"] for inv in invoices)
        days_overdue = (today - datetime.date.fromisoformat(oldest_date)).days

        # Simple reliability score from profile text (higher = more reliable = lower priority)
        profile_lower = profile.lower() if profile else ""
        if "reliable" in profile_lower or "on time" in profile_lower:
            reliability = 3
        elif "late" in profile_lower or "slip" in profile_lower or "delay" in profile_lower:
            reliability = 2
        elif "silent" in profile_lower or "unresponsive" in profile_lower:
            reliability = 1
        else:
            reliability = 2

        # Priority score: higher = needs attention sooner
        priority = (total_overdue * max(days_overdue, 1)) / reliability

        invoice_ids = [inv["invoice_id"] for inv in invoices]

        # Estimate predicted payment date based on buyer behavior pattern
        pred_offset_days = 2 if reliability == 3 else (6 if reliability == 2 else 12)
        predicted_date = (today + datetime.timedelta(days=pred_offset_days)).strftime("%Y-%m-%d")

        plan.append({
            "buyer": buyer_name,
            "open_invoices": invoice_ids,
            "total_overdue": total_overdue,
            "days_overdue": days_overdue,
            "predicted_date": predicted_date,
            "priority_score": round(priority, 2),
            "reason": f"Rs {total_overdue:,} overdue for {days_overdue} days across {len(invoices)} invoice(s)",
            "channel": message.get("channel", "WhatsApp"),
            "tone": message.get("tone", "firm"),
            "message": message.get("message", ""),
            "profile_summary": profile[:300] if profile else "",
            "evidence": history[:500] if history else "",
        })

    # Sort by priority (highest first)
    plan.sort(key=lambda x: x["priority_score"], reverse=True)

    # Number them
    for i, item in enumerate(plan):
        item["rank"] = i + 1

    return plan


# ── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python agent.py recall <buyer_name>")
        print("  python agent.py profile <buyer_name>")
        print("  python agent.py predict <buyer_name> <invoice_id>")
        print("  python agent.py message <buyer_name>")
        print("  python agent.py plan")
        sys.exit(0)

    command = sys.argv[1]

    if command == "recall":
        name = " ".join(sys.argv[2:])
        print(f"Recalling history for {name}...\n")
        print(recall_buyer(name))

    elif command == "profile":
        name = " ".join(sys.argv[2:])
        print(f"Building profile for {name}...\n")
        print(buyer_profile(name))

    elif command == "predict":
        name = " ".join(sys.argv[2:-1])
        inv_id = sys.argv[-1]
        print(f"Predicting payment for {name} / {inv_id}...\n")
        result = predict_payment_date(name, inv_id)
        print(json.dumps(result, indent=2))

    elif command == "message":
        name = " ".join(sys.argv[2:])
        print(f"Drafting message for {name}...\n")
        result = draft_message(name)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "plan":
        print(f"Building daily collection plan...\n")
        results = daily_plan()
        print(f"\n{'='*60}")
        print(f"VASOOL DAILY COLLECTION PLAN — {now_iso()}")
        print(f"{'='*60}\n")
        for item in results:
            print(f"#{item['rank']} {item['buyer']}")
            print(f"   Overdue: Rs {item['total_overdue']:,} | {item['days_overdue']} days | Priority: {item['priority_score']:,.0f}")
            print(f"   Action: {item['channel']} ({item['tone']})")
            print(f"   Message: {item['message'][:120]}")
            print()
        # Save to file
        plan_path = os.path.join(DATA_DIR, "daily_plan.json")
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Saved plan to {plan_path}")

    else:
        print(f"Unknown command: {command}")
