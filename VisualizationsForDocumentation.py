import pandas as pd
import ast, os
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc


kpi_card_style = {
    "backgroundColor": "white",
    "borderRadius": "10px",
    "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
    "padding": "20px",
    "textAlign": "center",
    "width": "100%",
    "height": "100px",     # Increase height
    "display": "flex",
    "flexDirection": "column",
    "justifyContent": "center",
    "alignItems": "center"
}


# Load CSV
# csv_path = r"C:\actionfi\projects\learn_test\learning_agentic_ai\data\tag_data_from_customerdevicedata_table.csv"
csv_path = os.path.join(os.path.dirname(__file__), "data", "tag_data_from_customerdevicedata_table.csv")
# csv_path = r"C:\\actionfi\\projects\\aakash\\testing\\csv_data_downloaded_from_db\\tag_data_ from_customerdevicedata_table-1750942566819.csv"  # IGNORE
df = pd.read_csv(csv_path, parse_dates=["created_at", "updated_at"])

# Parse JSON
def parse_json(val):
    try:
        return ast.literal_eval(val) if isinstance(val, str) else val
    except Exception:
        return {}

df["json_1"] = df["json_1"].apply(parse_json)
print(df["json_1"].head(3).to_list())
df["json_timestamp"] = df["json_1"].apply(
    lambda x: pd.to_datetime(x.get("timestamp"), utc=True) if isinstance(x, dict) and x.get("timestamp") else pd.NaT
)
# print(df["json_1"].apply(lambda x: x.get("timestamp") if isinstance(x, dict) else None).head(5))
print(df["json_timestamp"].head(5))
df["year"] = df["json_timestamp"].dt.year.astype("Int64").astype(str)
df["month"] = df["json_timestamp"].dt.strftime('%b')  # Jan, Feb, etc.
df["weekday"] = df["json_timestamp"].dt.day_name()    # Monday, Tuesday, etc.
df["hour"] = df["json_timestamp"].dt.hour.astype("Int64").astype(str).str.zfill(2)
df["date"] = df["json_timestamp"].dt.date

# App
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "RFID Dashboard"

device_options = sorted(df["device_id_id"].dropna().unique())

# application layout
app.layout = html.Div([
    html.H2("RFID Device Dashboard", style={"textAlign": "center", "marginTop": "20px"}),

    dbc.Container([
        dbc.Row([
            # LEFT COLUMN: Date Picker + Uniform KPIs
            dbc.Col([
    html.Div([
        html.Label("Select Date Range:"),
        dcc.DatePickerRange(
            id="date-range",
            display_format="YYYY-MM-DD",
            start_date=df["json_timestamp"].min().date(),
            end_date=df["json_timestamp"].max().date(),
            style={"marginBottom": "20px"}
        ),

        # Unified KPI block container
        html.Div(id="kpi-blocks", style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "10px",
            "flexGrow": "1",
            "height": "100%",                   # Fill column height
            "justifyContent": "space-between",  # Even spacing
        })
        ])
    ], width=3, style={
        "backgroundColor": "#b9b49d",  # light yellow
        "display": "flex",
        "flexDirection": "column",
        "padding": "20px",
        "height": "100vh",              # Full viewport height
        "minHeight": "700px"
    }),

                        # RIGHT COLUMN: ALL CHARTS STACKED VERTICALLY
                        # RIGHT COLUMN: CHARTS STACKED VERTICALLY
            dbc.Col([
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            id="line-timestamps",
                            config={"responsive": True},
                            style={"height": "400px", "width": "100%"}
                        )
                    ], width=12)
                ]),
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            id="yearly-tag-reads",
                            config={"responsive": True, "scrollZoom": True},
                            style={"height": "350px", "width": "100%"}  # Fixed height
                        )
                    ], width=6),
                    dbc.Col([
                        dcc.Graph(
                            id="monthly-tag-reads",
                            config={"responsive": True, "scrollZoom": True},
                            style={"height": "350px", "width": "100%"}  # Same height
                        )
                    ], width=6),
                ]),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            id="weekday-tag-reads",
                            config={"responsive": True},
                            style={"height": "400px", "width": "100%"}
                        )
                    ], width=12)
                ]),
                
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            id="hourly-tag-reads",  # LINE chart
                            config={"responsive": True},
                            style={"height": "400px", "width": "100%"}
                        )
                    ], width=12)
                ])
            ], width=9)

        ])
    ], fluid=True, style={"overflowX": "hidden"})  # <-- Prevents horizontal scroll
])

@app.callback(
    Output("kpi-blocks", "children"),   # Updated to single KPI container
    Output("yearly-tag-reads", "figure"),
    Output("monthly-tag-reads", "figure"),
    Output("weekday-tag-reads", "figure"),
    Output("hourly-tag-reads", "figure"),
    Output("line-timestamps", "figure"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date")
)
def update_visuals(start_date, end_date):
    filtered = df.copy()

    # if device_id:
    #     filtered = filtered[filtered["device_id_id"] == device_id]

    filtered = filtered[filtered["device_id_id"] == 1]
    

    start_dt = pd.to_datetime(start_date, utc=True)
    end_dt = pd.to_datetime(end_date, utc=True)

    filtered = filtered[(filtered["json_timestamp"] >= start_dt) & (filtered["json_timestamp"] <= end_dt)]
    print("columns:",filtered.columns)
    # KPIs
    total_tag_reads = 0
    for js in filtered["json_1"]:
        if isinstance(js, dict):
            # print("true")
            count = js.get("count")
            if count not in [None, '', 'null']:
                try:
                    total_tag_reads += int(count)
                except:
                    total_tag_reads += len(js.get("tags", []))
            else:
                total_tag_reads += len(js.get("tags", []))

    # total_devices = filtered["device_id_id"].nunique()
    total_sessions = filtered["int_1"].nunique()
    successes = (filtered["char_1"] == "success").sum()
    failures = (filtered["char_1"] == "failed").sum()
    success_rate = round((successes / (successes + failures)) * 100, 2) if (successes + failures) else 0

    # kpi_style = {"padding": "10px", "border": "1px solid #ccc", "borderRadius": "8px", "textAlign": "center", "background": "#f8f9fa"}
    if success_rate >= 90:
        rate_color = "#4CAF50"  # green
    elif success_rate >= 50:
        rate_color = "#FFC107"  # yellow
    else:
        rate_color = "#CB5F30"  # light red

    weekdates = filtered.groupby("date").apply(
    lambda f: sum(
        int(js.get("count", len(js.get("tags", []))))
        if isinstance(js := j, dict) and js.get("count") not in [None, '', 'null']
        else len(js.get("tags", []))
        for j in f["json_1"]
    )
).reset_index(name="weekly_total_tag_reads")  # Use this syntax when it's a Series


    

    # Get peak weekday (row with max tag reads)
    peak_weekdate = weekdates.loc[weekdates["weekly_total_tag_reads"].idxmax(), "date"]

    print("peak_weekdate:", peak_weekdate)
    print(f"peak_weekday:{df[df['date'] == peak_weekdate]['weekday'].iloc[0]}")

    hours = filtered.groupby("hour").apply(lambda f: sum(
        int(js.get("count", len(js.get("tags", [])))) if isinstance(js := j, dict) and js.get("count") not in [None, '', 'null']
        else len(js.get("tags", []))
        for j in f["json_1"]
    )).reset_index(name="hourly_total_tag_reads")
    peak_hour = hours.loc[hours["hourly_total_tag_reads"].idxmax(), "hour"]

    kpi_blocks = [
        html.Div([html.H6("Total Tag Reads"), html.H4(f"{total_tag_reads}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),
        html.Div([html.H6("Total Sessions"), html.H4(f"{total_sessions}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),
        html.Div([html.H6("Successes"), html.H4(f"{successes}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),
        html.Div([html.H6("Failures"), html.H4(f"{failures}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),
        html.Div([html.H6("Peak Day"), html.H4(f"{peak_weekdate}, {df[df['date'] == peak_weekdate]['weekday'].iloc[0]}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),
        html.Div([html.H6("Peak Hour(in 24hr format)"), html.H4(f"{str(int(peak_hour)-1)}-{str(int(peak_hour)+1)}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),
        
        # Add dynamic color style for success rate
        html.Div(
            [html.H6("Success Rate (%)"), html.H4(f"{success_rate}")],
            style={**kpi_card_style, "backgroundColor": rate_color}
        )
    ]

    # Yearly totals
    yearly = filtered.groupby("year").apply(lambda f: sum(
        int(js.get("count", len(js.get("tags", [])))) if isinstance(js := j, dict) and js.get("count") not in [None, '', 'null']
        else len(js.get("tags", []))
        for j in f["json_1"]
    )).reset_index(name="yearly_total_tag_reads")

    # Monthly averages
    monthly = filtered.groupby(["year", "month"]).apply(lambda f: sum(
    int(js.get("count", len(js.get("tags", [])))) if isinstance(js := j, dict) and js.get("count") not in [None, '', 'null']
    else len(js.get("tags", []))
    for j in f["json_1"]
    )).reset_index(name="monthly_total_tag_reads")
    monthly_avg = monthly.groupby("month")["monthly_total_tag_reads"].mean().reset_index()

    # Weekly averages
    weekday = filtered.groupby("weekday").apply(lambda f: sum(
        int(js.get("count", len(js.get("tags", [])))) if isinstance(js := j, dict) and js.get("count") not in [None, '', 'null']
        else len(js.get("tags", []))
        for j in f["json_1"]
    )).reset_index(name="weekly_total_tag_reads")
    weekly_avg = weekday.groupby("weekday")["weekly_total_tag_reads"].mean().reset_index()

    # Calculate hourly averages
    hourly = filtered.groupby("hour").apply(lambda f: sum(
        int(js.get("count", len(js.get("tags", [])))) if isinstance(js := j, dict) and js.get("count") not in [None, '', 'null']
        else len(js.get("tags", []))
        for j in f["json_1"]
    )).reset_index(name="hourly_total_tag_reads")
    hourly_avg = hourly.groupby("hour")["hourly_total_tag_reads"].mean().reset_index()
    
    ## Chart creation
    # 1.Stacked bar for month with years
    month_fig = go.Figure()
    month_fig.add_trace(go.Bar(
        x=monthly_avg["month"],
        y=monthly_avg["monthly_total_tag_reads"],
        marker_color="steelblue",
        text=monthly_avg["monthly_total_tag_reads"].round(2),
        textposition="outside",
        
    ))
    month_fig.update_layout(
        title="Average Tag Reads per Month (Across Years)",
        xaxis_title="Month",
        yaxis_title="Average Tag Reads",
        margin=dict(t=30, b=30),
        dragmode='pan',
        plot_bgcolor="white",        # chart area
        xaxis=dict(
            gridcolor="#e6e6e6",     # light gray grid lines
            zerolinecolor="#cccccc"
        ),
        yaxis=dict(
            gridcolor="#e6e6e6",
            zerolinecolor="#cccccc"
        ),
                          )
    # 2.Bar charts for year, weekday, and hour
    year_fig = go.Figure([go.Bar(x=yearly["year"], y=yearly["yearly_total_tag_reads"], marker_color='blue',textposition="outside")])
    year_fig.update_layout(title="Tag Reads per Year",
                            barmode='stack',
                            dragmode='pan', 
                            plot_bgcolor="white",        # chart area
                            paper_bgcolor="white",       # outer frame
                            xaxis=dict(
                                gridcolor="#e6e6e6",     # light gray grid lines
                                zerolinecolor="#cccccc"
                            ),
                            yaxis=dict(
                                gridcolor="#e6e6e6",
                                zerolinecolor="#cccccc"
                            ),)

    weekday_fig = go.Figure()
    weekday_fig.add_trace(go.Bar(
                            x=weekly_avg["weekday"],
                            y=weekly_avg["weekly_total_tag_reads"],
                            marker_color="steelblue",
                            text=weekly_avg["weekly_total_tag_reads"].round(2),
                            textposition="outside"
    ))
    weekday_fig.update_layout(
                            title="Average Tag Reads per weekday (Across Years)",
                            xaxis_title="Weekday",
                            yaxis_title="Average Tag Reads",
                            margin=dict(t=30, b=30),
                            dragmode='pan', plot_bgcolor="white",        # chart area
                            paper_bgcolor="white",       # outer frame
                            xaxis=dict(
                                gridcolor="#e6e6e6",     # light gray grid lines
                                zerolinecolor="#cccccc"
                            ),
                            yaxis=dict(
                                gridcolor="#e6e6e6",
                                zerolinecolor="#cccccc"
                            ),
                        )

    hour_fig = go.Figure()
    hour_fig.add_trace(go.Scatter(
                            x=hourly_avg["hour"],
                            y=hourly_avg["hourly_total_tag_reads"],
                            mode="lines+markers+text",  # Enable text annotations
                            line=dict(color="steelblue"),
                            name="Avg Tag Reads",
                            text=hourly_avg["hourly_total_tag_reads"],  # Show the value as label
                            textposition="top center"  # <-- valid for Scatter
    ))
    hour_fig.update_layout(
                            title="Average Tag Reads per Hour (Across Years)",
                            xaxis_title="Hour",
                            yaxis_title="Average Tag Reads",
                            margin=dict(t=30, b=30),
                            dragmode="pan",
                            plot_bgcolor="white",        # chart area
                            paper_bgcolor="white",       # outer frame
                            xaxis=dict(
                                gridcolor="#e6e6e6",     # light gray grid lines
                                zerolinecolor="#cccccc"
                            ),
                            yaxis=dict(
                                gridcolor="#e6e6e6",
                                zerolinecolor="#cccccc"
                            ),
                        )

    # 3.Line Chart
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
            hovermode="x unified",
            dragmode="pan",#212
            plot_bgcolor="white",        # chart area
            paper_bgcolor="white",       # outer frame
            xaxis=dict(
                gridcolor="#e6e6e6",     # light gray grid lines
                zerolinecolor="#cccccc"
            ),
            yaxis=dict(
                gridcolor="#e6e6e6",
                zerolinecolor="#cccccc"
            ),
                )
    else:
        line_fig = go.Figure()

    return kpi_blocks, year_fig, month_fig, weekday_fig, hour_fig, line_fig


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))  # Use PORT from Render if available
    app.run(host="0.0.0.0", port=port, debug=True)
    # app.run(debug=True)  # For local testing