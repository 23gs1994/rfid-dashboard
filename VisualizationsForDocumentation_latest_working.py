# Full Python script to analyze RFID device data from a CSV file
# Generates KPIs and visualizations as per the user's request

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import ast

# Load CSV (update the path to your actual file)
csv_path = r"C:\actionfi\projects\aakash\testing\csv_data_downloaded_from_db\tag_data_ from_customerdevicedata_table-1750942566819.csv"
df = pd.read_csv(csv_path, parse_dates=["created_at", "updated_at"])

def parse_char1_dict(value):
    try:
        return ast.literal_eval(value) if isinstance(value, str) else {}
    except Exception:
        return {}

df["json_1"] = df["json_1"].apply(parse_char1_dict)

def extract_timestamp(js):
    ts = js.get("timestamp") if isinstance(js, dict) else None
    try:
        return pd.to_datetime(ts.replace("Z", "+00:00")) if ts else None
    except:
        return None

df["json_timestamp"] = df["json_1"].apply(extract_timestamp)


# ---------- Helpers ----------

def kpis(frame):
    total_tag_reads = 0
    total_devices = frame["device_id_id"].nunique()
    total_sessions = frame["int_1"].nunique()
    print("Total Sessionssss:", total_sessions)
    successes = (frame["char_1"] == "success").sum()
    failures = (frame["char_1"] == "failed").sum()
    success_rate = successes / (successes + failures) if (successes + failures) else 0
    for i in frame["json_1"]:
        if isinstance(i, dict):
            if "count" in i.keys():
                total_tag_reads += int(i.get("count", 0))
            elif "tags" in i.keys():
                total_tag_reads += len(i.get("tags", []))
            else:
                total_tag_reads += 0
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


# ---------- Visual Insight A: device_id_id vs total tag read counts ----------

def compute_tag_reads_per_device(frame):
    tag_read_counts = {}
    for _, row in frame.iterrows():
        device_id = row["device_id_id"]
        json_data = row["json_1"]
        count_val = json_data.get("count", None)

# Check if count is valid and non-empty
        if count_val not in [None, '', 'null']:
            try:
                count = int(count_val)
            except ValueError:
                count = len(json_data.get("tags", []))
        else:
            count = len(json_data.get("tags", []))
        tag_read_counts[device_id] = tag_read_counts.get(device_id, 0) + count
    return pd.DataFrame(list(tag_read_counts.items()), columns=["device_id_id", "total_tag_reads"])

tag_reads_df = compute_tag_reads_per_device(df)

plt.figure(figsize=(10, 4))
ax1 = sns.barplot(data=tag_reads_df, x="device_id_id", y="total_tag_reads", palette="Blues_d")
plt.title("Total Tag Reads per Device")
plt.ylabel("Tag Reads")
plt.xlabel("Device ID")
plt.xticks(rotation=45)
for p in ax1.patches:
    height = p.get_height()
    ax1.annotate(f'{int(height)}', (p.get_x() + p.get_width() / 2, height),
                 ha='center', va='bottom', fontsize=9, fontweight='bold')
plt.tight_layout()
plt.savefig("C:/actionfi/projects/aakash/testing/csv_data_downloaded_from_db/total_tag_reads_per_device.png")
plt.close()


# ---------- Visual Insight B: device_id_id vs total session counts ----------

# Count unique session IDs (int_1) per device
session_counts = df.groupby("device_id_id")["int_1"].nunique().reset_index()
session_counts.rename(columns={"int_1": "session_count"}, inplace=True)

plt.figure(figsize=(10, 4))
ax2 = sns.barplot(data=session_counts, x="device_id_id", y="session_count", palette="Greens_d")
plt.title("Total Sessions per Device")
plt.ylabel("Sessions")
plt.xlabel("Device ID")
plt.xticks(rotation=45)
for p in ax2.patches:
    height = p.get_height()
    ax2.annotate(f'{int(height)}', (p.get_x() + p.get_width() / 2, height),
                 ha='center', va='bottom', fontsize=9, fontweight='bold')
plt.tight_layout()
plt.savefig("C:/actionfi/projects/aakash/testing/csv_data_downloaded_from_db/total_sessions_per_device.png")
plt.close()

# ---------- Line Chart: Timestamp Ranges vs Tag Read Count (device_id_id = 1) ----------

df_device1 = df[df["device_id_id"] == 1]

# ---------- Extract timestamp and tag read count ----------
line_data = []

for _, row in df_device1.iterrows():
    json_data = row["json_1"]
    if isinstance(json_data, dict):
        ts = json_data.get("timestamp")
        if ts:
            try:
                ts_parsed = pd.to_datetime(ts)
                count_val = json_data.get("count", None)
                if count_val not in [None, '', 'null']:
                    try:
                        count = int(count_val)
                    except ValueError:
                        count = len(json_data.get("tags", []))
                else:
                    count = len(json_data.get("tags", []))
                line_data.append({"timestamp": ts_parsed, "tag_reads": count})
            except Exception:
                continue

line_df = pd.DataFrame(line_data)
line_df["timestamp"] = pd.to_datetime(line_df["timestamp"])

# === Filter: Only first 2 months of earliest year ===
first_year = line_df["timestamp"].min().year
line_df = line_df[
    (line_df["timestamp"].dt.year == first_year) &
    (line_df["timestamp"].dt.month.isin([3]))
]

# === Create time bins and plot ===
bin_size = "1H"
min_time = line_df["timestamp"].min().floor(bin_size)
max_time = line_df["timestamp"].max().ceil(bin_size)
time_bins = pd.date_range(start=min_time, end=max_time, freq=bin_size)

line_df["time_bin"] = line_df["timestamp"].dt.floor(bin_size)
grouped = line_df.groupby("time_bin")["tag_reads"].sum().reindex(time_bins, fill_value=0)

plt.figure(figsize=(12, 5))
plt.plot(grouped.index, grouped.values, linestyle='-', color='blue')
plt.axhline(0, color='gray', linestyle='--', linewidth=1)
plt.title(f"Device 1: Tag Reads (Mar 2025)")
plt.xlabel("Time")
plt.ylabel("Tag Reads")
plt.xticks(rotation=45)
plt.grid(True)

# Annotate peaks
for i in range(1, len(grouped) - 1):
    prev_val = grouped.values[i - 1]
    curr_val = grouped.values[i]
    next_val = grouped.values[i + 1]
    
    if curr_val > prev_val and curr_val > next_val:
        plt.annotate(
            f"{curr_val}",
            (grouped.index[i], curr_val),
            textcoords="offset points",
            xytext=(0, 5),
            ha='center',
            fontsize=9,
            fontweight='bold',
            color='black'
        )

plt.tight_layout()
plt.savefig("C:/actionfi/projects/aakash/testing/csv_data_downloaded_from_db/device_1_tag_reads_line_chart.png")
plt.close()



