from typing import List, Optional
from collections import defaultdict
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
import plotly.express as px
import os


def _parse_ts(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def build_heatmap(entries: List[dict]):
    """
    Calendar heatmap: green = deficit day, gray = surplus/unknown.
    Each cell is a day; color intensity = how far under/over goal.
    """
    # Aggregate calories per day
    daily_calories = defaultdict(int)
    daily_goal = {}

    for e in entries:
        dt = _parse_ts(e.get("timestamp", ""))
        if not dt:
            continue
        day = dt.date().isoformat()
        cal = e.get("estimated_calories", 0) or 0
        daily_calories[day] += cal
        # Use last-seen goal for the day
        daily_goal[day] = e.get("daily_goal", 2000)

    if not daily_calories:
        return None

    # Build date range from first entry to today
    all_days = sorted(daily_calories.keys())
    start = date.fromisoformat(all_days[0])
    end = date.today()

    dates, values, hover, colors = [], [], [], []

    current = start
    while current <= end:
        day_str = current.isoformat()
        cal = daily_calories.get(day_str, None)
        goal = daily_goal.get(day_str, 2000)

        dates.append(current)
        if cal is None:
            values.append(0)
            hover.append(f"{day_str}<br>No data")
            colors.append("lightgray")
        else:
            diff = goal - cal  # positive = deficit (good)
            values.append(diff)
            status = "✅ Deficit" if diff >= 0 else "⚠️ Surplus"
            hover.append(f"{day_str}<br>{cal} kcal eaten<br>Goal: {goal}<br>{status} ({abs(diff)} kcal)")
            colors.append("mediumseagreen" if diff >= 0 else "#d3d3d3")

        current += timedelta(days=1)

    # Layout as a weekly grid
    weeks = []
    week = []
    for i, d in enumerate(dates):
        week.append(d)
        if d.weekday() == 6 or i == len(dates) - 1:
            weeks.append(week)
            week = []

    # Build scatter-based calendar
    x_vals, y_vals, texts, marker_colors = [], [], [], []
    for week_idx, week in enumerate(weeks):
        for day in week:
            day_str = day.isoformat()
            idx = dates.index(day)
            x_vals.append(week_idx)
            y_vals.append(day.weekday())  # 0=Mon, 6=Sun
            texts.append(hover[idx])
            marker_colors.append(colors[idx])

    fig = go.Figure(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="markers",
        marker=dict(
            size=18,
            color=marker_colors,
            symbol="square",
            line=dict(width=1, color="white")
        ),
        hovertext=texts,
        hoverinfo="text"
    ))

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    fig.update_layout(
        height=220,
        margin=dict(l=40, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(
            tickvals=list(range(7)),
            ticktext=day_names,
            showgrid=False,
            zeroline=False,
            autorange="reversed"
        ),
        showlegend=False
    )
    return fig


def build_meal_time_chart(entries: List[dict]):
    """Bar chart of how many meals were logged at each hour of the day."""
    hour_counts = defaultdict(int)

    for e in entries:
        dt = _parse_ts(e.get("timestamp", ""))
        if dt:
            hour_counts[dt.hour] += 1

    if not hour_counts:
        return None

    hours = list(range(24))
    counts = [hour_counts.get(h, 0) for h in hours]
    labels = [f"{h:02d}:00" for h in hours]

    fig = px.bar(
        x=labels,
        y=counts,
        labels={"x": "Hour of Day", "y": "Meals Logged"},
        color=counts,
        color_continuous_scale="Teal"
    )
    fig.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=10, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
        xaxis=dict(tickangle=45)
    )
    return fig


def build_calorie_trend(entries: List[dict]):
    """Line chart of daily total calories over time vs goal."""
    daily_calories = defaultdict(int)
    daily_goal = {}

    for e in entries:
        dt = _parse_ts(e.get("timestamp", ""))
        if not dt:
            continue
        day = dt.date().isoformat()
        daily_calories[day] += e.get("estimated_calories", 0) or 0
        daily_goal[day] = e.get("daily_goal", 2000)

    if not daily_calories:
        return None

    days = sorted(daily_calories.keys())
    cals = [daily_calories[d] for d in days]
    goals = [daily_goal.get(d, 2000) for d in days]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=days, y=cals,
        mode="lines+markers",
        name="Calories Eaten",
        line=dict(color="steelblue", width=2),
        marker=dict(size=7)
    ))
    mode = "lines+markers" if len(days) > 1 else "markers"

    fig.add_trace(go.Scatter(
        x=days, y=cals,
        mode=mode,
        name="Calories Eaten",
        line=dict(color="steelblue", width=2),
        marker=dict(size=12)
    ))
    fig.add_trace(go.Scatter(
        x=days, y=goals,
        mode=mode,
        name="Daily Goal",
        line=dict(color="salmon", width=2, dash="dash"),
        marker=dict(size=12)
    ))
    
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(showgrid=False, type="category"),
        yaxis=dict(title="kcal", showgrid=True, gridcolor="rgba(200,200,200,0.2)")
    )
    return fig

def build_week_grid(entries: List[dict]):
    """
    Week grid view: days top to bottom, meals left to right within each day
    ordered by time. Returns HTML string.
    """
    from collections import defaultdict

    day_meals = defaultdict(list)

    for e in entries:
        dt = _parse_ts(e.get("timestamp", ""))
        if not dt:
            continue
        day_label = dt.strftime("%A, %b %d")   # e.g. "Tuesday, Apr 29"
        day_key = dt.date().isoformat()
        day_meals[day_key].append({
            "label": day_label,
            "day_key": day_key,
            "time": dt.strftime("%I:%M %p"),
            "dish": e.get("dish", "Unknown"),
            "calories": e.get("estimated_calories", "?"),
            "portion": e.get("portion", "?"),
            "image_path": e.get("image_path", None),
            "sort_dt": dt
        })

    if not day_meals:
        return None

    # Sort days, sort meals within each day by time
    sorted_days = sorted(day_meals.keys())
    for k in sorted_days:
        day_meals[k].sort(key=lambda x: x["sort_dt"])

    # Build HTML
    rows_html = ""
    for day_key in sorted_days:
        meals = day_meals[day_key]
        day_label = meals[0]["label"]

        cards_html = ""
        for m in meals:
            img_html = ""
            if m["image_path"] and os.path.exists(m["image_path"]):
                import base64
                with open(m["image_path"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                ext = m["image_path"].split(".")[-1].lower()
                mime = "image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}"
                img_html = f'<img src="data:{mime};base64,{b64}" style="width:100%;height:90px;object-fit:cover;border-radius:3px;margin-bottom:6px;">'

            cards_html += f"""
            <div style="
                min-width:140px; max-width:160px;
                background:#fffbf0;
                border:1px solid #d4bc80;
                border-radius:4px;
                padding:8px;
                flex-shrink:0;
                font-family:'Sentient',Georgia,serif;
            ">
                {img_html}
                <div style="font-size:0.7rem;color:#a08040;margin-bottom:2px;">{m['time']}</div>
                <div style="font-size:0.85rem;font-weight:600;color:#2a1f0a;line-height:1.2;margin-bottom:4px;">{m['dish']}</div>
                <div style="font-size:0.75rem;color:#6b5a2e;">{m['calories']} kcal · {m['portion']}</div>
            </div>"""

        rows_html += f"""
        <div style="margin-bottom:16px;">
            <div style="
                font-family:'Sentient',Georgia,serif;
                font-size:0.8rem;
                font-weight:600;
                color:#a08040;
                letter-spacing:0.08em;
                text-transform:uppercase;
                margin-bottom:6px;
            ">{day_label}</div>
            <div style="display:flex;gap:10px;overflow-x:auto;padding-bottom:4px;">
                {cards_html}
            </div>
        </div>"""

    return f"""
    <div style="
        background:rgba(253,248,236,0.6);
        border:1px solid #d4bc80;
        border-radius:6px;
        padding:16px;
    ">
        {rows_html}
    </div>"""