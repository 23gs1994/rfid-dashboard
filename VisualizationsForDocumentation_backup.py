# Full Python script to analyze RFID device data from a CSV file
# Generates KPIs and visualizations as per the user's request

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load CSV (update the path to your actual file)
csv_path = r"C:\actionfi\projects\aakash\testing\csv_data_downloaded_from_db\tag_data_ from_customerdevicedata_table-1750942566819.csv"
df = pd.read_csv(csv_path, parse_dates=["created_at", "updated_at"])

# ---------- Helpers ----------

# def filter_by_date(df, date_col, start=None, end=None, freq=None):
#     if start or end:
#         mask = True
#         if start:
#             mask &= df[date_col] >= pd.to_datetime(start)
#         if end:
#             mask &= df[date_col] <= pd.to_datetime(end)
#         return df.loc[mask]
#     if freq:
#         return df.set_index(date_col).groupby(pd.Grouper(freq=freq))
#     return df

# def apply_filters(df, device_id=None, start=None, end=None):
#     out = df.copy()
#     if device_id:
#         out = out[out["device_id_id"] == device_id]
#     if start or end:
#         out = filter_by_date(out, "created_at", start, end)
#     return out

def kpis(frame):
    total_devices = frame["device_id_id"].nunique()
    total_tag_reads = frame["int_1"].sum()
    total_sessions = frame["char_1"].nunique()
    successes = (frame["char_1"] == "success").sum()
    failures = (frame["char_1"] == "failed").sum()
    success_rate = successes / (successes + failures) if (successes + failures) else 0
    return {
        "total_devices": total_devices,
        "total_tag_reads": total_tag_reads,
        "total_sessions": total_sessions,
        "successes": successes,
        "failures": failures,
        "success_rate (%)": round(success_rate * 100, 2)
    }

# ---------- Print KPIs ----------
overall_kpis = kpis(df)

fig, axs = plt.subplots(2, 3, figsize=(15, 6))
fig.suptitle("RFID Device KPIs", fontsize=16, weight='bold')

kpi_titles = [
    "Total Devices",
    "Total Tag Reads",
    "Total Sessions",
    "Successes",
    "Failures",
    "Success Rate (%)"
]

for ax, (title, key) in zip(axs.flat, zip(kpi_titles, overall_kpis.keys())):
    ax.axis("off")
    ax.set_title(title, fontsize=12)
    ax.text(0.5, 0.5, f"{overall_kpis[key]}", fontsize=22, weight='bold', ha='center', va='center')

plt.tight_layout(rect=[0, 0, 1, 0.93])  # Make space for title
kpi_output_path = "C:/actionfi/projects/aakash/testing/csv_data_downloaded_from_db/kpi_dashboard.png"
plt.savefig(kpi_output_path)
plt.close()

print("=== Overall KPIs ===")
for k, v in overall_kpis.items():
    print(f"{k}: {v}")

# ---------- Visualizations ----------

# # A. Device vs Total Tag Reads
# tag_reads = df.groupby("device_id_id")["int_1"].sum().reset_index()
# plt.figure(figsize=(10, 4))
# sns.barplot(data=tag_reads, x="device_id_id", y="int_1")
# plt.title("Total tag reads per device")
# plt.ylabel("Reads")
# plt.xlabel("Device ID")
# plt.xticks(rotation=45)
# plt.tight_layout()
# plt.savefig("C:/actionfi/projects/aakash/testing/csv_data_downloaded_from_db/total_tag_reads_per_device.png")
# plt.close()

# # B. Device vs Session Counts
# session_counts = df.groupby("device_id_id")["char_1"].nunique().reset_index()
# plt.figure(figsize=(10, 4))
# sns.barplot(data=session_counts, x="device_id_id", y="char_1")
# plt.title("Total sessions per device")
# plt.ylabel("Sessions")
# plt.xlabel("Device ID")
# plt.xticks(rotation=45)
# plt.tight_layout()
# plt.savefig("C:/actionfi/projects/aakash/testing/csv_data_downloaded_from_db/total_sessions_per_device.png")
# plt.close()

# # C. Line Chart: Date vs Unique Devices
# daily = df.set_index("created_at").groupby(pd.Grouper(freq="D"))["device_id_id"].nunique()
# plt.figure(figsize=(12, 4))
# daily.plot()
# plt.title("Unique active devices per day")
# plt.ylabel("Device count")
# plt.xlabel("Date")
# plt.tight_layout()
# plt.savefig("C:/actionfi/projects/aakash/testing/csv_data_downloaded_from_db/daily_device_activity.png")
# plt.close()

# # Output file paths for download
# [
#     "C:/actionfi/projects/aakash/testing/csv_data_downloaded_from_db/total_tag_reads_per_device.png",
#     "C:/actionfi/projects/aakash/testing/csv_data_downloaded_from_db/total_sessions_per_device.png",
#     "C:/actionfi/projects/aakash/testing/csv_data_downloaded_from_db/daily_device_activity.png"
# ]

