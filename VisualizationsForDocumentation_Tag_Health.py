import pandas as pd
import ast, os
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from datetime import datetime


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
csv_path_tag = os.path.join(os.path.dirname(__file__), "data", "tag_data_from_customerdevicedata_table.csv")
csv_path_health = os.path.join(os.path.dirname(__file__), "data", "device_management_healthdata.csv")
df = pd.read_csv(csv_path_tag, parse_dates=["created_at", "updated_at"])
df_health = pd.read_csv(csv_path_health, parse_dates=["created_at", "updated_at"])

# Parse JSON
def parse_json(val):
    try:
        return ast.literal_eval(val) if isinstance(val, str) else val
    except Exception:
        return {}

#for df
df["json_1"] = df["json_1"].apply(parse_json)
df["json_timestamp"] = df["json_1"].apply(lambda x: pd.to_datetime(x.get("timestamp"), utc=True) if isinstance(x, dict) and x.get("timestamp") else pd.NaT)
df["year"] = df["json_timestamp"].dt.year.astype("Int64").astype(str)
df["month"] = df["json_timestamp"].dt.strftime('%b')  # Jan, Feb, etc.
df["weekday"] = df["json_timestamp"].dt.day_name()    # Monday, Tuesday, etc.
df["hour"] = df["json_timestamp"].dt.hour.astype("Int64").astype(str).str.zfill(2)
df["date"] = df["json_timestamp"].dt.date




#for df_health
df_health["timestamp"] = pd.to_datetime(
    df_health["timestamp"], errors="coerce", utc=True
)
df_health["year"] = df_health["timestamp"].dt.year.astype("Int64").astype(str)
df_health["month"] = df_health["timestamp"].dt.strftime('%b')  # Jan, Feb, etc.
df_health["weekday"] = df_health["timestamp"].dt.day_name()    # Monday, Tuesday, etc.
df_health["hour"] = df_health["timestamp"].dt.hour.astype("Int64").astype(str).str.zfill(2)


# App
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "RFID Dashboard"

# application layout
app.layout = html.Div([
    html.H2("RFID Device Dashboard", style={"textAlign": "center", "marginTop": "20px"}),
    dcc.Tabs(id="tabs", value="Tag", children=[
        dcc.Tab(label="Tag", value="Tag"),
        dcc.Tab(label="Health", value="Health")
    ], style={"marginBottom": "20px"}),
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
        "minHeight": "1920px"
    }),
    dbc.Col([
                html.Div(id="tab-content")  # this will be dynamically updated
            ], width=9),

                        # RIGHT COLUMN: ALL CHARTS STACKED VERTICALLY
                        # RIGHT COLUMN: CHARTS STACKED VERTICALLY
            dbc.Col([
                
            ], width=9)

        ])
    ], fluid=True, style={"overflowX": "hidden"})  # <-- Prevents horizontal scroll
])

@app.callback(
    Output("kpi-blocks", "children"),
    Output("tab-content", "children"),
    Input("tabs", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date")
)
def render_tab_content(tab, start_date, end_date):
    if tab == "Tag":
        # Existing logic for tag KPIs and charts
        return update_visuals_for_Tag(start_date, end_date)
    elif tab == "Health":
        return update_visuals_for_Health(start_date, end_date)
def update_visuals_for_Tag(start_date, end_date):
    filtered = df.copy()
    filtered_health = df_health.copy()

    # if device_id:
    #     filtered = filtered[filtered["device_id_id"] == device_id]

    filtered = filtered[filtered["device_id_id"] == 1]
    filtered_health = filtered_health[filtered_health["device_id_id"] == 1]
    

    start_dt = pd.to_datetime(start_date, utc=True)
    end_dt = pd.to_datetime(end_date, utc=True)

    filtered = filtered[(filtered["json_timestamp"] >= start_dt) & (filtered["json_timestamp"] <= end_dt)]
    filtered_health = filtered_health[(filtered_health["timestamp"] >= start_dt) & (filtered_health["timestamp"] <= end_dt)]
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

    hours = filtered.groupby("hour").apply(lambda f: sum(
        int(js.get("count", len(js.get("tags", [])))) if isinstance(js := j, dict) and js.get("count") not in [None, '', 'null']
        else len(js.get("tags", []))
        for j in f["json_1"]
    )).reset_index(name="hourly_total_tag_reads")
    peak_hour = hours.loc[hours["hourly_total_tag_reads"].idxmax(), "hour"]
    peak_hour_ampm = datetime.strptime(str(peak_hour), "%H").strftime("%I %p")
    start_hour = f"{int(peak_hour_ampm.split(' ')[0]) - 1}{peak_hour_ampm.split(' ')[1]}"# Extract hour part
    end_hour =  f"{int(peak_hour_ampm.split(' ')[0]) + 1}{peak_hour_ampm.split(' ')[1]}"# Extract hour part
    # print("peak_weekdate:", peak_weekdate)
    print("peak dates:", df[df['date'] == peak_weekdate]['weekday'])
    # print("df_weekdates:", df[df['date'] == peak_weekdate])



    kpi_blocks = [
        html.Div([html.H6("Total Tag Reads"), html.H4(f"{total_tag_reads}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),
        html.Div([html.H6("Total Sessions"), html.H4(f"{total_sessions}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),
        html.Div([html.H6("Successes"), html.H4(f"{successes}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),
        html.Div([html.H6("Failures"), html.H4(f"{failures}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),
        html.Div([html.H6("Peak Day"), html.H4(f"{peak_weekdate}, {df[df['date'] == peak_weekdate]['weekday'].iloc[0]}, {start_hour}-{end_hour}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),
        # html.Div([html.H6("Peak Hour(in 24hr format)"), html.H4(f"{start_hour}-{end_hour}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),

        # Add dynamic color style for success ratepeak_temperature_value_end_hour
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
    
    # Chart creation
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

    charts = [
            dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            id="line-timestamps",
                            figure=line_fig,
                            config={"responsive": True},
                            style={"height": "400px", "width": "100%"}
                        )
                    ], width=12)
                ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="yearly-tag-reads",
                        figure=year_fig,
                        config={"responsive": True, "scrollZoom": True},
                        style={"height": "350px", "width": "100%"}  # Fixed height
                    )
                ], width=6),
                dbc.Col([
                    dcc.Graph(
                        id="monthly-tag-reads",
                        figure=month_fig,
                        config={"responsive": True, "scrollZoom": True},
                        style={"height": "350px", "width": "100%"}  # Same height
                    )
                ], width=6),
            ]),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="weekday-tag-reads",
                        figure=weekday_fig,
                        config={"responsive": True},
                        style={"height": "400px", "width": "100%"}
                    )
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="hourly-tag-reads",  # LINE chart
                        figure=hour_fig,
                        config={"responsive": True},
                        style={"height": "400px", "width": "100%"}
                    )
                ], width=12)
            ])]

    return kpi_blocks, charts

# , year_fig, month_fig, weekday_fig, hour_fig, line_fig


def update_visuals_for_Health(start_date, end_date):
    filtered_health = df_health.copy()

    # if device_id:
    #     filtered = filtered[filtered["device_id_id"] == device_id]

    filtered_health = filtered_health[filtered_health["device_id_id"] == 1]
    

    start_dt = pd.to_datetime(start_date, utc=True)
    end_dt = pd.to_datetime(end_date, utc=True)

    filtered_health = filtered_health[(filtered_health["timestamp"] >= start_dt) & (filtered_health["timestamp"] <= end_dt)]
    print("filtered_health:", filtered_health)

    max_cpu = filtered_health["cpu_usage"].max()
    max_memory_usage = filtered_health["memory_usage"].max()
    max_disk_usage = filtered_health["disk_usage"].max()
    max_temperature = filtered_health["temperature"].max()

    # peak_cpu_value = filtered_health[filtered_health["cpu_usage"] == max_cpu]["cpu_usage"].iloc[0].astype(str)  # first row only
    peak_cpu_value_date = filtered_health[filtered_health["cpu_usage"] == max_cpu]["timestamp"].iloc[0].strftime("%Y-%m-%d")  # first row only
    peak_cpu_value_weekday = filtered_health[filtered_health["cpu_usage"] == max_cpu]["weekday"].iloc[0]  # first row only
    peak_cpu_value_hour = filtered_health[filtered_health["cpu_usage"] == max_cpu]["hour"].iloc[0]  # first row only
    peak_cpu_value_hour_ampm = datetime.strptime(peak_cpu_value_hour, "%H").strftime("%I %p")
    peak_cpu_value_start_hour = f"{int(peak_cpu_value_hour_ampm.split(' ')[0]) - 1}{peak_cpu_value_hour_ampm.split(' ')[1]}"# Extract hour part
    peak_cpu_value_end_hour =  f"{int(peak_cpu_value_hour_ampm.split(' ')[0]) + 1}{peak_cpu_value_hour_ampm.split(' ')[1]}"# Extract hour part
    
    # peak_memory_value = filtered_health[filtered_health["memory_usage"] == max_memory_usage]["memory_usage"].iloc[0].astype(str)  # first row only
    peak_memory_value_date = filtered_health[filtered_health["memory_usage"] == max_memory_usage]["timestamp"].iloc[0].strftime("%Y-%m-%d")  # first row only
    peak_memory_value_weekday = filtered_health[filtered_health["memory_usage"] == max_memory_usage]["weekday"].iloc[0]  # first row only
    peak_memory_value_hour = filtered_health[filtered_health["memory_usage"] == max_memory_usage]["hour"].iloc[0]  # first row only
    peak_memory_value_hour_ampm = datetime.strptime(peak_memory_value_hour, "%H").strftime("%I %p")
    peak_memory_value_start_hour = f"{int(peak_memory_value_hour_ampm.split(' ')[0]) - 1}{peak_memory_value_hour_ampm.split(' ')[1]}"# Extract hour part
    peak_memory_value_end_hour =  f"{int(peak_memory_value_hour_ampm.split(' ')[0]) + 1}{peak_memory_value_hour_ampm.split(' ')[1]}"# Extract hour part

    # peak_disk_value = filtered_health[filtered_health["disk_usage"] == max_disk_usage]["disk_usage"].iloc[0].astype(str)  # first row only
    peak_disk_value_date = filtered_health[filtered_health["disk_usage"] == max_disk_usage]["timestamp"].iloc[0].strftime("%Y-%m-%d")  # first row only
    peak_disk_value_weekday = filtered_health[filtered_health["disk_usage"] == max_disk_usage]["weekday"].iloc[0]  # first row only
    peak_disk_value_hour = filtered_health[filtered_health["disk_usage"] == max_disk_usage]["hour"].iloc[0]  # first row only
    peak_disk_value_hour_ampm = datetime.strptime(peak_disk_value_hour, "%H").strftime("%I %p")
    peak_disk_value_start_hour = f"{int(peak_disk_value_hour_ampm.split(' ')[0]) - 1}{peak_disk_value_hour_ampm.split(' ')[1]}"# Extract hour part
    peak_disk_value_end_hour =  f"{int(peak_disk_value_hour_ampm.split(' ')[0]) + 1}{peak_disk_value_hour_ampm.split(' ')[1]}"# Extract hour part

    # peak_temperature_value = filtered_health[filtered_health["temperature"] == max_temperature]["temperature"].iloc[0].astype(str)  # first row only
    # print("peak_temperature_value_df:", filtered_health[filtered_health["temperature"] == max_temperature]["temperature"])
    peak_temperature_value_date = filtered_health[filtered_health["temperature"] == max_temperature]["timestamp"].iloc[0].strftime("%Y-%m-%d")  # first row only
    peak_temperature_value_weekday = filtered_health[filtered_health["temperature"] == max_temperature]["weekday"].iloc[0]  # first row only
    peak_temperature_value_hour = filtered_health[filtered_health["temperature"] == max_temperature]["hour"].iloc[0]  # first row only
    peak_temperature_value_hour_ampm = datetime.strptime(peak_temperature_value_hour, "%H").strftime("%I %p")
    peak_temperature_value_start_hour = f"{int(peak_temperature_value_hour_ampm.split(' ')[0]) - 1}{peak_temperature_value_hour_ampm.split(' ')[1]}"# Extract hour part
    peak_temperature_value_end_hour =  f"{int(peak_temperature_value_hour_ampm.split(' ')[0]) + 1}{peak_temperature_value_hour_ampm.split(' ')[1]}"# Extract hour part


    kpi_blocks = [
        # Add dynamic color style for success ratepeak_temperature_value_end_hour
        html.Div([html.H6("Peak cpu_usage"), html.H4(f"{max_cpu}%, {peak_cpu_value_date}, {peak_cpu_value_weekday}, {peak_cpu_value_start_hour}-{peak_cpu_value_end_hour}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),
        html.Div([html.H6("Peak memory_usage"), html.H4(f"{max_memory_usage}MB, {peak_memory_value_date}, {peak_memory_value_weekday}, {peak_memory_value_start_hour}-{peak_memory_value_end_hour}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),
        html.Div([html.H6("Peak disk_usage"), html.H4(f"{max_disk_usage}%, {peak_disk_value_date}, {peak_disk_value_weekday}, {peak_disk_value_start_hour}-{peak_disk_value_end_hour}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),
        html.Div([html.H6("Peak temperature"), html.H4(f"{max_temperature} C, {peak_temperature_value_date}, {peak_temperature_value_weekday}, {peak_temperature_value_start_hour}-{peak_temperature_value_end_hour}")], style={**kpi_card_style, "backgroundColor": "#f8f9fa"}),
    ]

    yearly_health = filtered_health.groupby("year", as_index=False).agg({
    "cpu_usage": "mean",
    "memory_usage": "mean",
    "disk_usage": "mean",
    "temperature": "mean"
}).round(2)
    # Monthly averages
    monthly_health = filtered_health.groupby("month", as_index=False).agg({
    "cpu_usage": "mean",
    "memory_usage": "mean",
    "disk_usage": "mean",
    "temperature": "mean"
}).round(2)
    weekday_health = filtered_health.groupby("weekday", as_index=False).agg({
    "cpu_usage": "mean",
    "memory_usage": "mean",
    "disk_usage": "mean",
    "temperature": "mean"
}).round(2)
    hour_health = filtered_health.groupby("hour", as_index=False).agg({
    "cpu_usage": "mean",
    "memory_usage": "mean",
    "disk_usage": "mean",
    "temperature": "mean"
}).round(2)
    
    
    # # Chart creation
    monthly_health_fig = go.Figure([
    go.Bar(
        x=monthly_health["month"],
        y=monthly_health["cpu_usage"],
        name="CPU Usage",
        marker_color="#1f77b4",
        width=0.1,
        text=monthly_health["cpu_usage"],       
        textposition="outside",
    ),
    go.Bar(
        x=monthly_health["month"],
        y=monthly_health["memory_usage"],
        name="Memory Usage",
        marker_color="#ff7f0e",
        width=0.1,
        text=monthly_health["memory_usage"],        #
        textposition="outside",
    ),
    go.Bar(
        x=monthly_health["month"],
        y=monthly_health["disk_usage"],
        name="Disk Usage",
        marker_color="#2ca02c",
        width=0.1,
        text=monthly_health["disk_usage"], 
        textposition="outside",
    ),
    go.Bar(
        x=monthly_health["month"],
        y=monthly_health["temperature"],
        name="Temperature",
        marker_color="#d62728",
        width=0.1,
        text=monthly_health["temperature"],
        textposition="outside",
    )
])

    # Layout for grouped bars
    monthly_health_fig.update_layout(
        title="Average Heakth data per Month (Across Years)",
        barmode="group",  # Ensures bars are side-by-side within each year group
        bargap=0.4,       # Controls gap between year groups (increase to separate years more)
        bargroupgap=0,  # <-- GROUPED, not stacked
        dragmode="pan",
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            title="Month",
            gridcolor="#e6e6e6",
            zerolinecolor="#cccccc"
        ),
        yaxis=dict(
            title="Average Value",
            gridcolor="#e6e6e6",
            zerolinecolor="#cccccc"
        ),
        legend=dict(title="Metric", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )                   
    # 2.Bar charts for year, weekday, and hour
    year_health_fig = go.Figure([
    go.Bar(
        x=yearly_health["year"],
        y=yearly_health["cpu_usage"],
        name="CPU Usage",
        marker_color="#1f77b4",
        width=0.1,
        text=yearly_health["temperature"], 
        textposition="outside",
    ),
    go.Bar(
        x=yearly_health["year"],
        y=yearly_health["memory_usage"],
        name="Memory Usage",
        marker_color="#ff7f0e",
        width=0.1,
        text=yearly_health["memory_usage"],        #
        textposition="outside",
    ),
    go.Bar(
        x=yearly_health["year"],
        y=yearly_health["disk_usage"],
        name="Disk Usage",
        marker_color="#2ca02c",
        width=0.1,
        text=yearly_health["disk_usage"],       
        textposition="outside",
    ),
    go.Bar(
        x=yearly_health["year"],
        y=yearly_health["temperature"],
        name="Temperature",
        marker_color="#d62728",
        width=0.1,
        text=yearly_health["temperature"],
        textposition="outside",
    )
])

    # Layout for grouped bars
    year_health_fig.update_layout(
        title="Average Health Data per Year",
        barmode="group",  # Ensures bars are side-by-side within each year group
        bargap=0.4,       # Controls gap between year groups (increase to separate years more)
        bargroupgap=0,  # <-- GROUPED, not stacked
        dragmode="pan",
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            title="Year",
            gridcolor="#e6e6e6",
            zerolinecolor="#cccccc"
        ),
        yaxis=dict(
            title="Average Value",
            gridcolor="#e6e6e6",
            zerolinecolor="#cccccc"
        ),
        legend=dict(title="Metric", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    weekday_health_fig = go.Figure([
    go.Bar(
        x=weekday_health["weekday"],
        y=weekday_health["cpu_usage"],
        name="CPU Usage",
        marker_color="#1f77b4",
        width=0.1,
        text=weekday_health["cpu_usage"],       
        textposition="outside",
    ),
    go.Bar(
        x=weekday_health["weekday"],
        y=weekday_health["memory_usage"],
        name="Memory Usage",
        marker_color="#ff7f0e",
        width=0.1,
        text=weekday_health["memory_usage"],        #
        textposition="outside",
    ),
    go.Bar(
        x=weekday_health["weekday"],
        y=weekday_health["disk_usage"],
        name="Disk Usage",
        marker_color="#2ca02c",
        width=0.1,
        text=weekday_health["disk_usage"],        #
        textposition="outside",
    ),
    go.Bar(
        x=weekday_health["weekday"],
        y=weekday_health["temperature"],
        name="Temperature",
        marker_color="#d62728",
        width=0.1,
        text=weekday_health["temperature"], 
        textposition="outside",
    )
])

    # Layout for grouped bars
    weekday_health_fig.update_layout(
        title="Average Health per weekday (Across Years)",
        barmode="group",  # Ensures bars are side-by-side within each year group
        bargap=0.4,       # Controls gap between year groups (increase to separate years more)
        bargroupgap=0,  # <-- GROUPED, not stacked
        dragmode="pan",
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            title="Year",
            gridcolor="#e6e6e6",
            zerolinecolor="#cccccc"
        ),
        yaxis=dict(
            title="Average Value",
            gridcolor="#e6e6e6",
            zerolinecolor="#cccccc"
        ),
        legend=dict(title="Metric", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )



    hour_health_fig = go.Figure([
        go.Scatter(
            x=hour_health["hour"],
            y=hour_health["cpu_usage"],
            mode="lines+markers+text",
            name="CPU Usage",
            text=hour_health["cpu_usage"],       
            textposition="top center",
            line=dict(color="#1f77b4")
        ),
        go.Scatter(
            x=hour_health["hour"],
            y=hour_health["memory_usage"],
            mode="lines+markers+text",
            name="Memory Usage",
            text=hour_health["memory_usage"],        #
            textposition="top center",
            line=dict(color="#ff7f0e")
        ),
        go.Scatter(
            x=hour_health["hour"],
            y=hour_health["disk_usage"],
            mode="lines+markers+text",
            name="Disk Usage",
            text=hour_health["disk_usage"], 
            textposition="top center",
            line=dict(color="#2ca02c")
        ),
        go.Scatter(
            x=hour_health["hour"],
            y=hour_health["temperature"],
            mode="lines+markers+text",
            name="Temperature",
            text=hour_health["temperature"], 
            textposition="top center",
            line=dict(color="#d62728")
        )
    ])

    hour_health_fig.update_layout(
        title="Average Health per Hour (Across Years)",
        dragmode="pan",
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            title="Hour (24-hour format)",
            gridcolor="#e6e6e6",
            zerolinecolor="#cccccc"
        ),
        yaxis=dict(
            title="Average Value",
            gridcolor="#e6e6e6",
            zerolinecolor="#cccccc"
        ),
        legend=dict(
            title="Metric", 
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1
        )
    )

    # # 3.Line Chart
    # line_data = []
    # for _, row in filtered.iterrows():
    #     js = row["json_1"]
    #     ts = js.get("timestamp")
    #     if ts:
    #         try:
    #             ts = pd.to_datetime(ts)
    #             count_val = js.get("count", None)
    #             count = int(count_val) if count_val not in [None, '', 'null'] else len(js.get("tags", []))
    #             line_data.append({"timestamp": ts, "tag_reads": count})
    #         except:
    #             continue

    # line_df = pd.DataFrame(line_data)
    # if not line_df.empty:
    #     line_df["time_bin"] = line_df["timestamp"].dt.floor("1h")
    #     grouped = line_df.groupby("time_bin")["tag_reads"].sum().reset_index()

    #     # Only show labels for top 10% tag_reads values
    #     threshold = grouped["tag_reads"].quantile(0.90)
    #     grouped["label_text"] = grouped["tag_reads"].apply(lambda x: str(x) if x >= threshold else "")

    #     line_fig = go.Figure([
    #         go.Scatter(
    #             x=grouped["time_bin"],
    #             y=grouped["tag_reads"],
    #             mode="lines+markers+text",
    #             text=grouped["label_text"],  # show only big values
    #             textposition="top center",
    #             marker=dict(color="blue"),
    #             line=dict(color="blue")
    #         )
    #     ])
    #     line_fig.update_layout(
    #         title="Tag Reads Over Time",
    #         xaxis_title="Time",
    #         yaxis_title="Tag Reads",
    #         margin=dict(t=30, b=30),
    #         hovermode="x unified",
    #         dragmode="pan",#212
    #         plot_bgcolor="white",        # chart area
    #         paper_bgcolor="white",       # outer frame
    #         xaxis=dict(
    #             gridcolor="#e6e6e6",     # light gray grid lines
    #             zerolinecolor="#cccccc"
    #         ),
    #         yaxis=dict(
    #             gridcolor="#e6e6e6",
    #             zerolinecolor="#cccccc"
    #         ),
    #             )
    # else:
    #     line_fig = go.Figure()
    charts = [
            # dbc.Row([
            #         dbc.Col([
            #             dcc.Graph(
            #                 id="line-timestamps",
            #                 figure=line_fig,
            #                 config={"responsive": True},
            #                 style={"height": "400px", "width": "100%"}
            #             )
            #         ], width=12)
            #     ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="yearly-health",
                        figure=year_health_fig,
                        config={"responsive": True, "scrollZoom": True},
                        style={"height": "350px", "width": "100%"}  # Fixed height
                    )
                ], width=6),
                dbc.Col([
                    dcc.Graph(
                        id="monthly-health",
                        figure=monthly_health_fig,
                        config={"responsive": True, "scrollZoom": True},
                        style={"height": "350px", "width": "100%"}  # Same height
                    )
                ], width=6),
            ]),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="weekday-tag-reads",
                        figure=weekday_health_fig,
                        config={"responsive": True},
                        style={"height": "400px", "width": "100%"}
                    )
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="hourly-tag-reads",  # LINE chart
                        figure=hour_health_fig,
                        config={"responsive": True},
                        style={"height": "400px", "width": "100%"}
                    )
                ], width=12)
            ])
            ]




    return kpi_blocks, charts
    
# , year_fig, month_fig, weekday_fig, hour_fig, line_fig


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))  # Use PORT from Render if available
    app.run(host="0.0.0.0", port=port, debug=True)
    # app.run(debug=True)  # For local testing
