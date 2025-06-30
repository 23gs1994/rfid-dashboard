import random
from datetime import datetime, timedelta

# Helper to generate random timestamps
def random_timestamp(start, end):
    delta = end - start
    random_sec = random.randint(0, int(delta.total_seconds()))
    return (start + timedelta(seconds=random_sec)).strftime("%Y-%m-%dT%H:%M:%SZ")

# Base session ID
base_session_id = 1234600

# Generate 50 records with more 'failed' statuses
generated_data = []
start_time = datetime(2025, 2, 10, 0, 0, 0)
end_time = datetime(2025, 2, 15, 23, 59, 59)

for i in range(50):
    status = "failed" if random.random() < 0.6 else "success"
    tags = [f"1234ABC{chr(65 + random.randint(0, 25))}" for _ in range(random.randint(1, 3))] if status == "success" else []
    count = str(random.randint(1, 20)) if status == "success" else "0"
    timestamp = random_timestamp(start_time, end_time)

    entry = {
        "session_id": base_session_id + i,
        "status": status,
        "tag_data": {
            "tags": tags,
            "count": count,
            "timestamp": timestamp
        }
    }
    generated_data.append(entry)
print(generated_data)