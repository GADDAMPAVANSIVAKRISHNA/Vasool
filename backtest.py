"""
VASOOL Backtest — Learning Curve Evaluation
Measured on synthetic data. Not a real-world benchmark.

Demonstrates that prediction error shrinks as the agent accumulates more
buyer interaction history in memory.

Logic:
  1. Load data/events.json, group events by buyer
  2. For buyers with multiple paid invoices, sort invoices by date
  3. For each invoice (skip the first per buyer):
     a. Build history text from ONLY events before that invoice's date
     b. Call agent.predict_payment_date() with the filtered history
     c. Compare predicted date to actual payment date → error in days
     d. Record (history_size, error_days)
  4. Bucket by history_size: 1-5, 6-10, 11-15, 16+
  5. Return mean error per bucket

Samples 5 buyers to stay within Groq rate limits (8 000 TPM on free tier).
"""

import os
import json
import time
import datetime
import random

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
EVENTS_PATH = os.path.join(DATA_DIR, "events.json")
RESULTS_PATH = os.path.join(DATA_DIR, "backtest_results.json")

# How many buyers to sample (keeps Groq calls reasonable)
SAMPLE_SIZE = 5
# Minimum paid invoices a buyer needs to be eligible (need >= 2 so we skip the first)
MIN_PAID_INVOICES = 3

# ── Helpers ────────────────────────────────────────────────────────────────


def _load_events() -> list[dict]:
    """Load the master events list."""
    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _group_by_buyer(events: list[dict]) -> dict[str, list[dict]]:
    """Group events into {buyer_name: [events sorted by date]}."""
    groups: dict[str, list[dict]] = {}
    for ev in events:
        buyer = ev.get("buyer", "")
        if not buyer:
            continue
        groups.setdefault(buyer, []).append(ev)
    # Sort each buyer's events chronologically
    for buyer in groups:
        groups[buyer].sort(key=lambda e: e.get("date", ""))
    return groups


def _build_invoice_lookup(events: list[dict]) -> tuple[dict, dict]:
    """
    Returns:
        sent:     {invoice_id: {buyer, amount, date}}
        payments: {invoice_id: {buyer, date}}
    """
    sent: dict[str, dict] = {}
    payments: dict[str, dict] = {}
    for ev in events:
        inv = ev.get("invoice_id")
        if not inv:
            continue
        if ev["type"] == "invoice_sent":
            sent[inv] = {
                "buyer": ev["buyer"],
                "amount": ev.get("amount", 0),
                "date": ev["date"],
            }
        elif ev["type"] == "payment_received":
            payments[inv] = {
                "buyer": ev["buyer"],
                "date": ev["date"],
            }
    return sent, payments


def _build_history_text(events_before: list[dict]) -> str:
    """
    Convert a list of event dicts into the same text format that
    agent.recall_buyer() would return, so the LLM sees familiar input.
    """
    lines = []
    for ev in events_before:
        buyer = ev.get("buyer", "")
        text = ev.get("text", "")
        date = ev.get("date", "")
        ev_type = ev.get("type", "")
        inv = ev.get("invoice_id", "")
        amount = ev.get("amount")

        # Replicate the "<buyer>: <text> | When: <date> | ..." format
        parts = [f"{buyer}: {text}"]
        if date:
            parts.append(f"When: {date}")
        if inv:
            parts.append(f"Invoice: {inv}")
        if amount:
            parts.append(f"Amount: Rs {amount:,}")
        if ev_type:
            parts.append(f"Type: {ev_type}")
        lines.append(" | ".join(parts))

    return "\n".join(lines)


def _date_error_days(predicted_str: str, actual_str: str) -> float | None:
    """Absolute difference in days between two YYYY-MM-DD strings."""
    try:
        predicted = datetime.date.fromisoformat(predicted_str[:10])
        actual = datetime.date.fromisoformat(actual_str[:10])
        return abs((predicted - actual).days)
    except (ValueError, TypeError):
        return None


# ── Bucket Logic ───────────────────────────────────────────────────────────


BUCKETS = [
    ("1-5", 1, 5),
    ("6-10", 6, 10),
    ("11-15", 11, 15),
    ("16+", 16, 9999),
]


def _bucket_label(history_size: int) -> str:
    for label, lo, hi in BUCKETS:
        if lo <= history_size <= hi:
            return label
    return "16+"


def _bucket_midpoint(label: str) -> int:
    """Representative x-axis value for each bucket."""
    mapping = {"1-5": 3, "6-10": 8, "11-15": 13, "16+": 20}
    return mapping.get(label, 20)


# ── Main Backtest ──────────────────────────────────────────────────────────


def run_backtest() -> list[dict]:
    """
    Run the Vasool learning-curve backtest.

    Returns:
        list[dict] — each dict has {"history_size": int, "error_days": float},
        one entry per bucket (1-5, 6-10, 11-15, 16+).
    """
    # Lazy import so app.py can import backtest without triggering agent
    # initialization until this function is actually called.
    import agent

    print("=" * 60)
    print("VASOOL BACKTEST — Learning Curve Evaluation")
    print("Measured on synthetic data. Not a real-world benchmark.")
    print("=" * 60)

    all_events = _load_events()
    buyer_groups = _group_by_buyer(all_events)
    sent, payments = _build_invoice_lookup(all_events)

    # Find eligible buyers: those with >= MIN_PAID_INVOICES paid invoices
    eligible: list[tuple[str, list[str]]] = []
    for buyer, _ in buyer_groups.items():
        paid_inv_ids = sorted(
            [
                inv_id
                for inv_id, info in sent.items()
                if info["buyer"] == buyer and inv_id in payments
            ],
            key=lambda k: sent[k]["date"],
        )
        if len(paid_inv_ids) >= MIN_PAID_INVOICES:
            eligible.append((buyer, paid_inv_ids))

    if not eligible:
        print("No eligible buyers found with enough paid invoices.")
        return []

    # Sample to keep within rate limits
    random.seed(42)  # Reproducible sampling
    sample = eligible if len(eligible) <= SAMPLE_SIZE else random.sample(eligible, SAMPLE_SIZE)

    print(f"\nSampled {len(sample)} buyers for backtest:")
    for buyer, invs in sample:
        print(f"  {buyer}: {len(invs)} paid invoices")

    # Collect (history_size, error_days) data points
    raw_results: list[dict] = []
    total_predictions = sum(len(invs) - 1 for _, invs in sample)
    completed = 0

    for buyer, paid_inv_ids in sample:
        buyer_events = buyer_groups[buyer]

        for idx, inv_id in enumerate(paid_inv_ids):
            if idx == 0:
                # Skip first invoice — no prior history to test against
                continue

            inv_sent_date = sent[inv_id]["date"]
            actual_paid_date = payments[inv_id]["date"]

            # Build history from ONLY events before this invoice's sent date
            events_before = [e for e in buyer_events if e["date"] < inv_sent_date]
            history_size = len(events_before)
            history_text = _build_history_text(events_before)

            if not history_text.strip():
                print(f"  [{buyer}] {inv_id}: no prior history, skipping")
                continue

            completed += 1
            print(
                f"\n  [{completed}/{total_predictions}] {buyer} / {inv_id}"
                f" | history={history_size} events | sent={inv_sent_date} | actual_paid={actual_paid_date}"
            )

            # Call agent.predict_payment_date with filtered history (no Hindsight calls)
            try:
                prediction = agent.predict_payment_date(
                    name=buyer,
                    invoice_id=inv_id,
                    before_date=inv_sent_date,
                    history_override=history_text,
                )
            except Exception as e:
                print(f"    ⚠ Prediction failed: {e}")
                continue

            predicted_date = prediction.get("predicted_date")
            if not predicted_date or predicted_date == "None":
                print(f"    ⚠ No date predicted: {prediction.get('reasoning', 'unknown')}")
                continue

            error = _date_error_days(predicted_date, actual_paid_date)
            if error is None:
                print(f"    ⚠ Could not compute error for predicted={predicted_date}")
                continue

            print(f"    ✓ Predicted: {predicted_date}  Actual: {actual_paid_date}  Error: {error:.0f} days")

            raw_results.append({
                "buyer": buyer,
                "invoice_id": inv_id,
                "history_size": history_size,
                "predicted_date": predicted_date,
                "actual_date": actual_paid_date,
                "error_days": error,
            })

            # Rate-limit pause between Groq calls
            time.sleep(1.5)

    if not raw_results:
        print("\nNo successful predictions to bucket.")
        return []

    # ── Bucket by history_size and compute mean error ──────────────────────

    bucket_errors: dict[str, list[float]] = {label: [] for label, _, _ in BUCKETS}

    for r in raw_results:
        label = _bucket_label(r["history_size"])
        bucket_errors[label].append(r["error_days"])

    bucketed: list[dict] = []
    print("\n" + "=" * 60)
    print("BUCKETED RESULTS")
    print(f"{'Bucket':<10} {'Samples':>8} {'Mean Error (days)':>18}")
    print("-" * 40)

    for label, _, _ in BUCKETS:
        errors = bucket_errors[label]
        if errors:
            mean_err = sum(errors) / len(errors)
            bucketed.append({
                "history_size": _bucket_midpoint(label),
                "error_days": round(mean_err, 1),
            })
            print(f"{label:<10} {len(errors):>8} {mean_err:>18.1f}")
        else:
            print(f"{label:<10} {'—':>8} {'—':>18}")

    print("=" * 60)

    # Save detailed results alongside bucketed output
    full_output = {
        "bucketed": bucketed,
        "detailed": raw_results,
        "sample_buyers": [b for b, _ in sample],
    }
    try:
        with open(RESULTS_PATH, "w", encoding="utf-8") as f:
            json.dump(full_output, f, indent=2, ensure_ascii=False)
        print(f"\nDetailed results saved to {RESULTS_PATH}")
    except Exception as e:
        print(f"\nCould not save results: {e}")

    return bucketed


# ── CLI Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = run_backtest()
    print("\nFinal output for Learning Curve chart:")
    print(json.dumps(results, indent=2))
