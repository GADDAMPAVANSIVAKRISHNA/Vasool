"""
VASOOL Synthetic Data Generator
Creates a realistic 6-month collections event history for 20 Indian business buyers.
Each buyer has a hidden behavior type that governs how and when they pay.
Output: data/events.json
"""

import os
import json
import random
import datetime

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Buyers & Hidden Behaviors ──────────────────────────────────────────────

BUYERS = [
    ("Sharma Traders",      "reliable"),
    ("Gupta Steels",        "always_slips"),
    ("Patel Textiles",      "pays_after_call"),
    ("Reddy Electronics",   "pays_after_10th"),
    ("Mehta Hardware",      "reliable"),
    ("Iyer Exports",        "goes_silent"),
    ("Khan Fabrics",        "always_slips"),
    ("Singh Agro",          "pays_after_call"),
    ("Nair Chemicals",      "reliable"),
    ("Desai Plastics",      "pays_after_10th"),
    ("Verma Motors",        "goes_silent"),
    ("Joshi Foods",         "always_slips"),
    ("Chopra Garments",     "pays_after_call"),
    ("Malhotra Pharma",     "reliable"),
    ("Bose Furniture",      "pays_after_10th"),
    ("Rao Electricals",     "always_slips"),
    ("Kulkarni Tools",      "goes_silent"),
    ("Banerjee Paper",      "pays_after_call"),
    ("Pillai Spices",       "reliable"),
    ("Sethi Metals",        "goes_silent"),
]

# ── Message Templates ──────────────────────────────────────────────────────

REMINDER_CHANNELS = ["WhatsApp", "call", "email"]
REMINDER_TONES = ["polite", "firm", "friendly"]

POLITE_REMINDERS = [
    "Gentle reminder: Invoice {inv} of Rs {amt} is due. Kindly process at the earliest.",
    "Sir, invoice {inv} ka payment pending hai — Rs {amt}. Request you to kindly clear it.",
    "Hi, this is a friendly reminder for invoice {inv} (Rs {amt}). Please let us know the expected date.",
    "Namaskar, invoice {inv} ka Rs {amt} abhi tak receive nahi hua. Kindly update.",
]

FIRM_REMINDERS = [
    "Invoice {inv} (Rs {amt}) is overdue. Please clear immediately to avoid escalation.",
    "Sir, aapka payment Rs {amt} (Inv {inv}) overdue ho chuka hai. Urgent action required.",
    "This is a final reminder for invoice {inv}. Amount Rs {amt} is significantly overdue.",
    "We have not received Rs {amt} against invoice {inv}. Please treat this as urgent.",
]

FRIENDLY_REMINDERS = [
    "Bhai, invoice {inv} ka Rs {amt} pending hai. Jab convenient ho kar dena.",
    "Hi! Just checking — invoice {inv} (Rs {amt}) ka kya status hai?",
    "Sir, ek chhota sa reminder — Rs {amt} invoice {inv} ke liye. No rush, but please update.",
    "Hello! Invoice {inv} ke Rs {amt} ke baare mein poochhna tha. Kab tak ho jayega?",
]

RELIABLE_REPLIES = [
    "Haan bhai, kal kar dunga payment.",
    "Sure, processing today itself.",
    "Payment initiate kar diya hai, 1-2 din mein aa jayega.",
    "Done, NEFT kar diya abhi.",
    "Yes, will clear by tomorrow EOD.",
]

SLIPS_REPLIES = [
    "Sir, payment kal tak kar dunga.",
    "Haan bhai, is week pakka.",
    "Thoda delay ho gaya, 2-3 din mein kar deta hoon.",
    "Sorry yaar, Friday tak pakka.",
    "Account mein thoda issue tha, next week fix ho jayega.",
    "Bhai, thoda time chahiye. 4-5 din mein kar dunga.",
]

AFTER_CALL_REPLIES = [
    "Acha acha, call aaya toh yaad aaya. Kal kar deta hoon.",
    "Haan sir, call ke baad hi process karta hoon. Parson tak.",
    "Oh haan, bhool gaya tha. Abhi karta hoon.",
    "Thanks for calling, warna bhool hi jaata. Tomorrow pakka.",
]

AFTER_10TH_REPLIES = [
    "Sir, 10 ke baad hi funds aate hain hamare. Tab kar dunga.",
    "Bhai hamare payment cycle 10th ke baad hai. Thoda wait karo.",
    "Month end tak tight hai, 11-12 ko kar dunga.",
    "Collection humara bhi 10th ke baad aata hai. Tab process karunga.",
]

SILENT_REPLIES = [
    "Haan bhai dekhta hoon...",
    "Ok.",
    "Will check.",
]

PROMISE_TEMPLATES = [
    "I'll pay by {date}.",
    "{date} tak kar dunga payment.",
    "Next week pakka, by {date}.",
    "Promise — {date} se pehle ho jayega.",
    "{date} tak NEFT kar dunga.",
    "Pakka {date} tak. Trust me.",
]

AGENT_ACTIONS_FOLLOW_UP = [
    "Logged follow-up. Will check again on {date}.",
    "Marked for follow-up call on {date}.",
    "Set reminder to call buyer on {date}.",
    "Noted promise. Tracking payment by {date}.",
]

AGENT_ACTIONS_ESCALATE = [
    "Buyer unresponsive. Escalating to senior collector.",
    "No response after 3 attempts. Flagged for escalation.",
    "Buyer has gone silent. Marking account as at-risk.",
    "Escalation note added. Will attempt visit if no response by {date}.",
]

AGENT_ACTIONS_PAYMENT = [
    "Payment of Rs {amt} received against invoice {inv}. Account updated.",
    "Rs {amt} credited for {inv}. Closing follow-up.",
    "Confirmed receipt of Rs {amt} ({inv}). Sending thank-you note.",
]


# ── Helper Functions ───────────────────────────────────────────────────────

def rand_date_in_month(year: int, month: int, day_min: int = 1, day_max: int = 28) -> datetime.date:
    """Return a random date within the given month, clamped to valid range."""
    day_max = min(day_max, 28)  # keep it safe for February
    day_min = max(day_min, 1)
    if day_min > day_max:
        day_min = day_max
    return datetime.date(year, month, random.randint(day_min, day_max))


def add_days(d: datetime.date, lo: int, hi: int) -> datetime.date:
    """Add a random number of days in [lo, hi] to d."""
    return d + datetime.timedelta(days=random.randint(lo, hi))


def fmt(d: datetime.date) -> str:
    return d.isoformat()


def pick(lst):
    return random.choice(lst)


def make_event(buyer, date, etype, text, amount=None, invoice_id=None):
    ev = {
        "buyer": buyer,
        "date": fmt(date),
        "type": etype,
        "text": text,
    }
    if amount is not None:
        ev["amount"] = amount
    if invoice_id is not None:
        ev["invoice_id"] = invoice_id
    return ev


# ── Core Event Generation ─────────────────────────────────────────────────

def generate_invoice_events(buyer_name: str, behavior: str, invoice_id: str,
                            amount: int, invoice_date: datetime.date) -> list:
    """
    Generate the full event sequence for a single invoice based on
    the buyer's hidden behavior type.
    """
    events = []

    # 1. Invoice sent
    events.append(make_event(
        buyer_name, invoice_date, "invoice_sent",
        f"Invoice {invoice_id} for Rs {amount:,} sent to {buyer_name}.",
        amount=amount, invoice_id=invoice_id
    ))

    due_date = add_days(invoice_date, 14, 21)  # net-14 to net-21 terms

    # 2. First reminder (a few days before or on due date)
    reminder_date = add_days(due_date, -3, 2)
    if reminder_date <= invoice_date:
        reminder_date = add_days(invoice_date, 3, 5)
    channel = pick(REMINDER_CHANNELS)
    tone = pick(REMINDER_TONES)
    if tone == "polite":
        msg = pick(POLITE_REMINDERS)
    elif tone == "firm":
        msg = pick(FIRM_REMINDERS)
    else:
        msg = pick(FRIENDLY_REMINDERS)
    msg = msg.format(inv=invoice_id, amt=f"{amount:,}")
    events.append(make_event(
        buyer_name, reminder_date, "reminder_sent",
        f"[{channel}/{tone}] {msg}",
        invoice_id=invoice_id
    ))

    # ── Behavior-driven sequences ──────────────────────────────────────

    if behavior == "reliable":
        # Reply quickly, pay on or before due date
        reply_date = add_days(reminder_date, 0, 1)
        events.append(make_event(
            buyer_name, reply_date, "buyer_reply",
            pick(RELIABLE_REPLIES),
            invoice_id=invoice_id
        ))
        promise_pay_date = add_days(reply_date, 0, 2)
        events.append(make_event(
            buyer_name, reply_date, "promise",
            pick(PROMISE_TEMPLATES).format(date=fmt(promise_pay_date)),
            invoice_id=invoice_id
        ))
        pay_date = add_days(promise_pay_date, 0, 1)  # pays on time or 1 day early
        events.append(make_event(
            buyer_name, pay_date, "payment_received",
            f"Rs {amount:,} received from {buyer_name} for invoice {invoice_id}.",
            amount=amount, invoice_id=invoice_id
        ))
        events.append(make_event(
            buyer_name, pay_date, "agent_action",
            pick(AGENT_ACTIONS_PAYMENT).format(amt=f"{amount:,}", inv=invoice_id),
            invoice_id=invoice_id
        ))

    elif behavior == "always_slips":
        # Promises but pays 8-12 days late
        reply_date = add_days(reminder_date, 1, 3)
        events.append(make_event(
            buyer_name, reply_date, "buyer_reply",
            pick(SLIPS_REPLIES),
            invoice_id=invoice_id
        ))
        promised_date = add_days(reply_date, 2, 4)
        events.append(make_event(
            buyer_name, reply_date, "promise",
            pick(PROMISE_TEMPLATES).format(date=fmt(promised_date)),
            invoice_id=invoice_id
        ))
        # Agent logs follow-up
        fu_date = add_days(promised_date, 1, 2)
        events.append(make_event(
            buyer_name, fu_date, "agent_action",
            pick(AGENT_ACTIONS_FOLLOW_UP).format(date=fmt(fu_date)),
            invoice_id=invoice_id
        ))
        # Second reminder after missed promise
        second_rem_date = add_days(promised_date, 2, 4)
        events.append(make_event(
            buyer_name, second_rem_date, "reminder_sent",
            f"[call/firm] {buyer_name}, aapne {fmt(promised_date)} tak payment ka promise kiya tha. "
            f"Invoice {invoice_id} Rs {amount:,} abhi bhi pending hai.",
            invoice_id=invoice_id
        ))
        slip_reply_date = add_days(second_rem_date, 0, 1)
        events.append(make_event(
            buyer_name, slip_reply_date, "buyer_reply",
            pick(["Sorry bhai, thoda aur delay ho gaya.", "Haan yaar, kal pakka this time.",
                   "Account issue tha, 2 din mein fix hoga.", "Aaj NEFT karta hoon pakka."]),
            invoice_id=invoice_id
        ))
        # Actually pays 8-12 days after original promise
        actual_pay_date = add_days(promised_date, 8, 12)
        events.append(make_event(
            buyer_name, actual_pay_date, "payment_received",
            f"Rs {amount:,} received from {buyer_name} for invoice {invoice_id} (late by "
            f"{(actual_pay_date - promised_date).days} days).",
            amount=amount, invoice_id=invoice_id
        ))
        events.append(make_event(
            buyer_name, actual_pay_date, "agent_action",
            pick(AGENT_ACTIONS_PAYMENT).format(amt=f"{amount:,}", inv=invoice_id),
            invoice_id=invoice_id
        ))

    elif behavior == "pays_after_call":
        # Ignores written reminders, pays only after phone call
        # No reply to first reminder
        second_rem_date = add_days(due_date, 3, 6)
        events.append(make_event(
            buyer_name, second_rem_date, "reminder_sent",
            f"[WhatsApp/polite] Hi {buyer_name}, invoice {invoice_id} (Rs {amount:,}) overdue hai. "
            f"Please update payment status.",
            invoice_id=invoice_id
        ))
        # Still no reply — agent calls
        call_date = add_days(second_rem_date, 2, 4)
        events.append(make_event(
            buyer_name, call_date, "agent_action",
            f"Called {buyer_name} directly regarding invoice {invoice_id}.",
            invoice_id=invoice_id
        ))
        events.append(make_event(
            buyer_name, call_date, "buyer_reply",
            pick(AFTER_CALL_REPLIES),
            invoice_id=invoice_id
        ))
        promise_date = add_days(call_date, 1, 3)
        events.append(make_event(
            buyer_name, call_date, "promise",
            pick(PROMISE_TEMPLATES).format(date=fmt(promise_date)),
            invoice_id=invoice_id
        ))
        pay_date = add_days(promise_date, 0, 2)
        events.append(make_event(
            buyer_name, pay_date, "payment_received",
            f"Rs {amount:,} received from {buyer_name} for invoice {invoice_id} after phone follow-up.",
            amount=amount, invoice_id=invoice_id
        ))
        events.append(make_event(
            buyer_name, pay_date, "agent_action",
            pick(AGENT_ACTIONS_PAYMENT).format(amt=f"{amount:,}", inv=invoice_id),
            invoice_id=invoice_id
        ))

    elif behavior == "pays_after_10th":
        # Always pays, but only after the 10th of the month
        reply_date = add_days(reminder_date, 1, 3)
        events.append(make_event(
            buyer_name, reply_date, "buyer_reply",
            pick(AFTER_10TH_REPLIES),
            invoice_id=invoice_id
        ))
        # Promise date is always after the 10th
        pay_month = due_date.month if due_date.day < 10 else (due_date.month % 12) + 1
        pay_year = due_date.year if pay_month > due_date.month else due_date.year + 1
        promise_target = datetime.date(pay_year, pay_month, random.randint(11, 15))
        events.append(make_event(
            buyer_name, reply_date, "promise",
            pick(PROMISE_TEMPLATES).format(date=fmt(promise_target)),
            invoice_id=invoice_id
        ))
        fu_date = add_days(due_date, 1, 3)
        events.append(make_event(
            buyer_name, fu_date, "agent_action",
            pick(AGENT_ACTIONS_FOLLOW_UP).format(date=fmt(promise_target)),
            invoice_id=invoice_id
        ))
        # Pays between 11th and 16th
        pay_date = datetime.date(pay_year, pay_month, random.randint(11, 16))
        events.append(make_event(
            buyer_name, pay_date, "payment_received",
            f"Rs {amount:,} received from {buyer_name} for invoice {invoice_id} (post-10th cycle).",
            amount=amount, invoice_id=invoice_id
        ))
        events.append(make_event(
            buyer_name, pay_date, "agent_action",
            pick(AGENT_ACTIONS_PAYMENT).format(amt=f"{amount:,}", inv=invoice_id),
            invoice_id=invoice_id
        ))

    elif behavior == "goes_silent":
        # Responds once or twice, then vanishes
        if random.random() < 0.6:
            reply_date = add_days(reminder_date, 1, 4)
            events.append(make_event(
                buyer_name, reply_date, "buyer_reply",
                pick(SILENT_REPLIES),
                invoice_id=invoice_id
            ))

        # Second reminder
        second_rem_date = add_days(due_date, 5, 8)
        events.append(make_event(
            buyer_name, second_rem_date, "reminder_sent",
            f"[call/firm] {buyer_name}, invoice {invoice_id} (Rs {amount:,}) is significantly overdue. "
            f"Please respond urgently.",
            invoice_id=invoice_id
        ))

        # Third reminder
        third_rem_date = add_days(second_rem_date, 4, 7)
        events.append(make_event(
            buyer_name, third_rem_date, "reminder_sent",
            f"[WhatsApp/firm] Final attempt: {buyer_name}, Rs {amount:,} for {invoice_id} pending. "
            f"No response received. Escalation imminent.",
            invoice_id=invoice_id
        ))

        # Agent escalates
        esc_date = add_days(third_rem_date, 2, 4)
        events.append(make_event(
            buyer_name, esc_date, "agent_action",
            pick(AGENT_ACTIONS_ESCALATE).format(date=fmt(add_days(esc_date, 5, 7))),
            invoice_id=invoice_id
        ))

        # ~40% chance they eventually pay after escalation, ~60% stays unpaid
        if random.random() < 0.4:
            late_pay = add_days(esc_date, 10, 20)
            events.append(make_event(
                buyer_name, late_pay, "buyer_reply",
                pick(["Sir, sorry for delay. Payment kar raha hoon aaj.",
                      "Bahut problem thi. Aaj NEFT kar diya.",
                      "Sorry bhai, sab kuch ek saath aa gaya tha. Payment done."]),
                invoice_id=invoice_id
            ))
            events.append(make_event(
                buyer_name, late_pay, "payment_received",
                f"Rs {amount:,} received from {buyer_name} for invoice {invoice_id} (severely late).",
                amount=amount, invoice_id=invoice_id
            ))
            events.append(make_event(
                buyer_name, late_pay, "agent_action",
                pick(AGENT_ACTIONS_PAYMENT).format(amt=f"{amount:,}", inv=invoice_id),
                invoice_id=invoice_id
            ))

    return events


# ── Main Generator ─────────────────────────────────────────────────────────

def generate_dataset():
    all_events = []
    invoice_counter = 1001

    # 6-month window: October 2024 → March 2025
    months = [
        (2024, 10), (2024, 11), (2024, 12),
        (2025, 1), (2025, 2), (2025, 3),
    ]

    for buyer_name, behavior in BUYERS:
        num_invoices = random.randint(3, 6)

        # Spread invoices across the 6-month window
        chosen_months = random.sample(months, min(num_invoices, len(months)))
        if num_invoices > len(months):
            chosen_months += random.choices(months, k=num_invoices - len(months))
        chosen_months.sort()

        for year, month in chosen_months:
            inv_id = f"INV-{invoice_counter}"
            invoice_counter += 1
            amount = random.randrange(20000, 200001, 1000)  # Rs 20,000 to Rs 2,00,000 in 1k steps
            inv_date = rand_date_in_month(year, month, 1, 15)

            inv_events = generate_invoice_events(buyer_name, behavior, inv_id, amount, inv_date)
            all_events.extend(inv_events)

    # Cap to the 6-month window (Oct 2024 – Mar 2025)
    CUTOFF = "2025-03-31"
    all_events = [e for e in all_events if e["date"] <= CUTOFF]

    # Sort everything by date, then by buyer for stability
    all_events.sort(key=lambda e: (e["date"], e["buyer"]))

    output_path = os.path.join(DATA_DIR, "events.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(all_events)} events for {len(BUYERS)} buyers")
    print(f"Saved to {output_path}")
    return all_events


if __name__ == "__main__":
    generate_dataset()
