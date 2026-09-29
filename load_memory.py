"""
VASOOL Memory Loader
Reads data/events.json and retains every event into a Hindsight memory bank.
"""

import os
import json
import time
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
EVENTS_PATH = os.path.join(DATA_DIR, "events.json")

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY", "").strip()
HINDSIGHT_BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "vasool-demo").strip()


def load_memory():
    # Read events
    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        events = json.load(f)

    print(f"Found {len(events)} events in {EVENTS_PATH}")
    print(f"Target bank: {HINDSIGHT_BANK_ID}")
    print()

    # Initialize Hindsight client using the exact pattern from docs
    client = Hindsight(
        base_url="https://api.hindsight.vectorize.io",
        api_key=HINDSIGHT_API_KEY
    )

    loaded = 0
    skipped = 0

    for i, event in enumerate(events):
        buyer = event.get("buyer", "Unknown")
        text = event.get("text", "")
        event_type = event.get("type", "")
        date = event.get("date", "")

        # Always prepend buyer name so it appears in memory text
        content = f"{buyer}: {text}"

        # Try up to 2 times (initial + 1 retry)
        success = False
        for attempt in range(2):
            try:
                client.retain(
                    bank_id=HINDSIGHT_BANK_ID,
                    content=content,
                    context=event_type,
                )
                success = True
                break
            except Exception as e:
                if attempt == 0:
                    print(f"  Retry event {i+1} after error: {e}")
                    time.sleep(1)
                else:
                    print(f"  Skipping event {i+1} after 2 failures: {e}")

        if success:
            loaded += 1
        else:
            skipped += 1

        # Print progress every 20 events
        if (i + 1) % 20 == 0:
            print(f"  Progress: {i+1}/{len(events)} events processed ({loaded} loaded, {skipped} skipped)")

    print()
    print(f"Loaded {loaded} events into Hindsight")
    if skipped:
        print(f"Skipped {skipped} events due to errors")


if __name__ == "__main__":
    load_memory()
