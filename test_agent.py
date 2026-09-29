from agent import recall_buyer, buyer_profile, predict_payment_date, draft_message

print("--- RECALL ---")
print(recall_buyer("Sharma Traders"))

print("\n--- PROFILE ---")
print(buyer_profile("Sharma Traders"))

print("\n--- PREDICT ---")
print(predict_payment_date("Sharma Traders", "INV-104"))

print("\n--- DRAFT ---")
print(draft_message("Sharma Traders"))
