import pandas as pd
import ast, os
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

# Load CSV
# csv_path = r"C:\actionfi\projects\learn_test\learning_agentic_ai\data\tag_data_from_customerdevicedata_table.csv"
csv_path = os.path.join(os.path.dirname(__file__), "data", "tag_data_from_customerdevicedata_table.csv")
# csv_path = r"C:\\actionfi\\projects\\aakash\\testing\\csv_data_downloaded_from_db\\tag_data_ from_customerdevicedata_table-1750942566819.csv"  # IGNORE
df = pd.read_csv(csv_path, parse_dates=["created_at", "updated_at"])

# Parse JSON
def parse_json(val):
    try:
        return ast.literal_eval(val) if isinstance(val, str) else {} #string to dict conversion
    except Exception:
        return {}

df["json_1"] = df["json_1"].apply(parse_json)
df["json_timestamp"] = df["json_1"].apply(
    lambda x: pd.to_datetime(x.get("timestamp"), utc=True) if isinstance(x, dict) and x.get("timestamp") else pd.NaT
)

# App
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "RFID Dashboard"

device_options = sorted(df["device_id_id"].dropna().unique())

app.layout = html.Div([
    html.H2("RFID Device Dashboard", style={"textAlign": "center", "marginTop": "20px"}),

    dbc.Container([
        dbc.Row([
            # Left Column: Filters + KPIs
            dbc.Col([
                html.Div([
                    html.Label("Select Device ID:"),
                    dcc.Dropdown(
                        id="device-dropdown",
                        options=[{"label": str(i), "value": i} for i in device_options],
                        placeholder="All Devices",
                        style={"width": "100%", "marginBottom": "10px"}
                    ),
                    html.Label("Select Date Range:"),
                    dcc.DatePickerRange(
                        id="date-range",
                        display_format="YYYY-MM-DD",
                        start_date=df["json_timestamp"].min().date(),
                        end_date=df["json_timestamp"].max().date(),
                        style={"marginBottom": "20px"}
                    )
                ]),
                html.Div(id="kpi-output", style={
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "15px",
                    "padding": "10px"
                })
            ], width=3, style={"display": "flex", "flexDirection": "column", "justifyContent": "flex-start"}),

            # Right Column: Charts
            dbc.Col([
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id="bar-tag-reads", config={"displayModeBar": False}, style={"height": "300px", "width": "100%"})
                    ], width=6),
                    dbc.Col([
                        dcc.Graph(id="bar-sessions", config={"displayModeBar": False}, style={"height": "300px", "width": "100%"})
                    ], width=6)
                ]),
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id="line-timestamps", config={"responsive": True}, style={"height": "400px", "width": "100%"})
                    ])
                ])
            ], width=9)
        ])
    ], fluid=True)
])


@app.callback(
    Output("kpi-output", "children"),
    Output("bar-tag-reads", "figure"),
    Output("bar-sessions", "figure"),
    Output("line-timestamps", "figure"),
    Input("device-dropdown", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date")
)
def update_visuals(device_id, start_date, end_date):
    filtered = df.copy()

    if device_id:
        filtered = filtered[filtered["device_id_id"] == device_id]

    start_dt = pd.to_datetime(start_date, utc=True)
    end_dt = pd.to_datetime(end_date, utc=True)

    filtered = filtered[(filtered["json_timestamp"] >= start_dt) & (filtered["json_timestamp"] <= end_dt)]

    # KPIs
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

    total_devices = filtered["device_id_id"].nunique()
    total_sessions = filtered["int_1"].nunique()
    successes = (filtered["char_1"] == "success").sum()
    failures = (filtered["char_1"] == "failed").sum()
    success_rate = round((successes / (successes + failures)) * 100, 2) if (successes + failures) else 0

    kpi_style = {"padding": "10px", "border": "1px solid #ccc", "borderRadius": "8px", "textAlign": "center", "background": "#f8f9fa"}
    if success_rate >= 90:
        rate_color = "#4CAF50"  # green
    elif success_rate >= 50:
        rate_color = "#FFC107"  # yellow
    else:
        rate_color = "#CB5F30"  # light red

    kpi_blocks = [
        html.Div([html.H6("Total Devices"), html.H4(f"{total_devices}")], style=kpi_style),
        html.Div([html.H6("Total Tag Reads"), html.H4(f"{total_tag_reads}")], style=kpi_style),
        html.Div([html.H6("Total Sessions"), html.H4(f"{total_sessions}")], style=kpi_style),
        html.Div([html.H6("Successes"), html.H4(f"{successes}")], style=kpi_style),
        html.Div([html.H6("Failures"), html.H4(f"{failures}")], style=kpi_style),
        
        # Add dynamic color style for success rate
        html.Div(
            [html.H6("Success Rate (%)"), html.H4(f"{success_rate}")],
            style={**kpi_style, "backgroundColor": rate_color}
        )
    ]

    # Bar Charts
    tag_df = filtered.groupby("device_id_id").apply(lambda f: sum(
        int(js.get("count", len(js.get("tags", [])))) if isinstance(js := j, dict) and js.get("count") not in [None, '', 'null']
        else len(js.get("tags", []))
        for j in f["json_1"]
    )).reset_index(name="total_tag_reads")

    tag_fig = go.Figure([
        go.Bar(
    x=tag_df["device_id_id"].astype(str),
    y=tag_df["total_tag_reads"],
    text=tag_df["total_tag_reads"],
    textposition="outside",
    marker_color="red",
    width=[0.6] * len(tag_df)
)

    ])
    tag_fig.update_layout(
    title="Total Tag Reads per Device",
    xaxis_title="Device ID",
    yaxis_title="Tag Reads",
    margin=dict(t=30, b=30),
    yaxis=dict(range=[0, tag_df["total_tag_reads"].max() * 1.2]),
    uniformtext_minsize=10,
    uniformtext_mode='show'
)

    session_df = filtered.groupby("device_id_id")["int_1"].nunique().reset_index(name="session_count")
    session_fig = go.Figure([
        go.Bar(
    x=session_df["device_id_id"].astype(str),
    y=session_df["session_count"],
    text=session_df["session_count"],
    textposition="outside",
    marker_color="green",
    width=[0.6] * len(session_df)
)

    ])
    session_fig.update_layout(title="Total Sessions per Device", xaxis_title="Device ID", yaxis_title="Sessions", margin=dict(t=30, b=30), yaxis=dict(range=[0, session_df["session_count"].max() * 1.2]), uniformtext_minsize=10, uniformtext_mode='show')

    # Line Chart
    line_data = []
    for _, row in filtered.iterrows():
        js = row["json_1"]
        ts = js.get("timestamp")
        if ts:
            try:
                ts = pd.to_datetime(ts)
                count_val = js.get("count", None)
                count = int(count_val) if count_val not in [None, '', 'null'] else len(js.get("tags", []))
                line_data.append({"timestamp": ts, "tag_reads": count})
            except:
                continue

    line_df = pd.DataFrame(line_data)
    if not line_df.empty:
        line_df["time_bin"] = line_df["timestamp"].dt.floor("1h")
        grouped = line_df.groupby("time_bin")["tag_reads"].sum().reset_index()

        # Only show labels for top 10% tag_reads values
        threshold = grouped["tag_reads"].quantile(0.90)
        grouped["label_text"] = grouped["tag_reads"].apply(lambda x: str(x) if x >= threshold else "")

        line_fig = go.Figure([
            go.Scatter(
                x=grouped["time_bin"],
                y=grouped["tag_reads"],
                mode="lines+markers+text",
                text=grouped["label_text"],  # show only big values
                textposition="top center",
                marker=dict(color="blue"),
                line=dict(color="blue")
            )
        ])
        line_fig.update_layout(
            title="Tag Reads Over Time",
            xaxis_title="Time",
            yaxis_title="Tag Reads",
            margin=dict(t=30, b=30),
            hovermode="x unified"
        )
    else:
        line_fig = go.Figure()

    return kpi_blocks, tag_fig, session_fig, line_fig

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))  # Use PORT from Render if available
    app.run(host="0.0.0.0", port=port, debug=True)
    # app.run(debug=True)  # For local testing, remove in production