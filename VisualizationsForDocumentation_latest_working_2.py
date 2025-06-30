import pandas as pd
import ast
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output

# Load CSV
csv_path = r"C:\actionfi\projects\aakash\testing\csv_data_downloaded_from_db\tag_data_ from_customerdevicedata_table-1750942566819.csv"
df = pd.read_csv(csv_path, parse_dates=["created_at", "updated_at"])

def parse_json(val):
    try:
        return ast.literal_eval(val) if isinstance(val, str) else {}
    except Exception:
        return {}

df["json_1"] = df["json_1"].apply(parse_json)
df["json_timestamp"] = df["json_1"].apply(lambda x: pd.to_datetime(x.get("timestamp"), utc=True) if isinstance(x, dict) and x.get("timestamp") else pd.NaT)

# Dash App
app = Dash(__name__)
app.title = "RFID Dashboard"

min_date = df["json_timestamp"].min()
max_date = df["json_timestamp"].max()

device_options = sorted(df["device_id_id"].dropna().unique())

app.layout = html.Div([
    html.H2("RFID Device Dashboard", style={"textAlign": "center"}),

    html.Div([
        html.Label("Select Device ID:"),
        dcc.Dropdown(
            id="device-dropdown",
            options=[{"label": str(i), "value": i} for i in device_options],
            placeholder="All Devices",
            style={"width": "300px"}
        ),
        html.Label("Select Date Range:"),
        dcc.DatePickerRange(
            id="date-picker",
            min_date_allowed=min_date,
            max_date_allowed=max_date,
            start_date=min_date,
            end_date=max_date
        )
    ], style={
        "margin": "20px",
        "display": "flex",
        "alignItems": "center",
        "gap": "20px"
    }),

    html.Div(id="kpi-output", style={
        "display": "flex",
        "gap": "20px",
        "flexWrap": "wrap",
        "justifyContent": "center",
        "marginBottom": "30px"
    }),

    html.Div([
        html.Div(dcc.Graph(id="bar-tag-reads", config={"displayModeBar": False}),
                 style={"flex": "1", "minWidth": "400px", "padding": "10px"}),
        html.Div(dcc.Graph(id="bar-sessions", config={"displayModeBar": False}),
                 style={"flex": "1", "minWidth": "400px", "padding": "10px"})
    ], style={
        "display": "flex",
        "flexWrap": "wrap",
        "justifyContent": "center"
    }),

    html.Div(dcc.Graph(id="line-timestamps", config={"displayModeBar": False}),
             style={"padding": "10px", "marginTop": "30px"})
])

@app.callback(
    Output("kpi-output", "children"),
    Output("bar-tag-reads", "figure"),
    Output("bar-sessions", "figure"),
    Output("line-timestamps", "figure"),
    Input("device-dropdown", "value"),
    Input("date-picker", "start_date"),
    Input("date-picker", "end_date")
)
def update_visuals(device_id, start_date, end_date):
    # Handle time zone consistency
    def to_utc(dt):
        ts = pd.to_datetime(dt)
        return ts if ts.tzinfo else ts.tz_localize("UTC")

    start = to_utc(start_date)
    end = to_utc(end_date)

    filtered = df.copy()
    if device_id:
        filtered = filtered[filtered["device_id_id"] == device_id]
        print("filteredddd",filtered)
    filtered = filtered[(filtered["json_timestamp"] >= start) & (filtered["json_timestamp"] <= end)]

    total_tag_reads = 0
    for js in filtered["json_1"]:
        if isinstance(js, dict):
            count = js.get("count")
            if count not in [None, '', 'null']:
                try:
                    total_tag_reads += int(count)
                except:
                    total_tag_reads += len(js.get("tags", []))
            else:
                total_tag_reads += len(js.get("tags", []))

    total_sessions = filtered["int_1"].nunique()
    successes = (filtered["char_1"] == "success").sum()
    failures = (filtered["char_1"] == "failed").sum()
    success_rate = round((successes / (successes + failures)) * 100, 2) if (successes + failures) else 0

    kpi_blocks = [
        html.Div([html.H5("Total Tag Reads"), html.H3(f"{total_tag_reads}")], style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "8px", "textAlign": "center", "width": "160px"}),
        html.Div([html.H5("Total Sessions"), html.H3(f"{total_sessions}")], style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "8px", "textAlign": "center", "width": "160px"}),
        html.Div([html.H5("Successes"), html.H3(f"{successes}")], style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "8px", "textAlign": "center", "width": "160px"}),
        html.Div([html.H5("Failures"), html.H3(f"{failures}")], style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "8px", "textAlign": "center", "width": "160px"}),
        html.Div([html.H5("Success Rate (%)"), html.H3(f"{success_rate}")], style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "8px", "textAlign": "center", "width": "180px"})
    ]

    # Tag Read Bar Chart
    tag_df = filtered.groupby("device_id_id").apply(lambda f: sum(
        int(js.get("count", len(js.get("tags", [])))) if isinstance(js := j, dict) and js.get("count") not in [None, '', 'null']
        else len(js.get("tags", []))
        for j in f["json_1"]
    )).reset_index(name="total_tag_reads")

    tag_fig = go.Figure([
        go.Bar(x=tag_df["device_id_id"], y=tag_df["total_tag_reads"], marker_color="red", width=0.4)
    ])
    tag_fig.update_layout(title="Total Tag Reads per Device", xaxis_title="Device ID", yaxis_title="Tag Reads", height=300, bargap=0.3)

    # Session Count Bar Chart
    session_df = filtered.groupby("device_id_id")["int_1"].nunique().reset_index(name="session_count")
    session_fig = go.Figure([
        go.Bar(x=session_df["device_id_id"], y=session_df["session_count"], marker_color="green", width=0.4)
    ])
    session_fig.update_layout(title="Total Sessions per Device", xaxis_title="Device ID", yaxis_title="Sessions", height=300, bargap=0.3)

    # Line Chart
    line_data = []
    for _, row in filtered.iterrows():
        js = row["json_1"]
        ts = js.get("timestamp")
        if ts:
            try:
                ts = pd.to_datetime(ts, utc=True)
                count_val = js.get("count", None)
                count = int(count_val) if count_val not in [None, '', 'null'] else len(js.get("tags", []))
                line_data.append({"timestamp": ts, "tag_reads": count})
            except:
                continue

    line_df = pd.DataFrame(line_data)
    if not line_df.empty:
        line_df["time_bin"] = line_df["timestamp"].dt.floor("1h")
        grouped = line_df.groupby("time_bin")["tag_reads"].sum().reset_index()
        line_fig = go.Figure([go.Scatter(x=grouped["time_bin"], y=grouped["tag_reads"], mode="lines+markers")])
        line_fig.update_layout(title="Tag Reads Over Time", xaxis_title="Time", yaxis_title="Tag Reads")
    else:
        line_fig = go.Figure()

    return kpi_blocks, tag_fig, session_fig, line_fig

if __name__ == "__main__":
    app.run(debug=True)
