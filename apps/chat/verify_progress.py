from src.services.progress_service import ProgressService
from src.config import CURRICULUM

ps = ProgressService()
progress = ps.get_current_state()

print("\n--- Current Progress State ---")
print(f"Level: {progress['current_level']}")
print(f"Topic: {progress['current_topic']}")

# Check if current topic matches first item
first_level = list(CURRICULUM.keys())[0]
first_item = CURRICULUM[first_level][0]
expected_topic = first_item["topic"] if isinstance(first_item, dict) else first_item

print(f"\nExpected Default Topic (if reset needed): {expected_topic}")

# We expect the current_topic to be a STRING
if isinstance(progress['current_topic'], str) and progress['current_topic'] == expected_topic:
    print("✅ Topic is a string and matches expected default (or was valid).")
else:
    print(f"ℹ️ Topic is: {progress['current_topic']}")
