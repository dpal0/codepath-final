import streamlit as st
import os
from datetime import datetime
from food_logger.gemini_client import analyze_food
from food_logger.storage import save_entry, load_all
from food_logger.dashboard import build_heatmap, build_meal_time_chart, build_calorie_trend, build_week_grid

st.markdown("""
<style>
@import url('https://api.fontshare.com/v2/css?f[]=sentient@400,500,700&display=swap');

* {
    font-family: 'Sentient', Georgia, serif !important;
}

/* Main background */
.stApp {
    background-color: #fdf8ec;
    background-image:
        linear-gradient(rgba(180, 160, 100, 0.15) 1px, transparent 1px),
        linear-gradient(90deg, rgba(180, 160, 100, 0.15) 1px, transparent 1px);
    background-size: 32px 32px;
}

/* Sidebar and containers */
section[data-testid="stSidebar"] {
    background-color: #f5efd8;
}

/* Cards / metric blocks */
div[data-testid="metric-container"] {
    background-color: #fffbf0;
    border: 1px solid #d4bc80;
    border-radius: 4px;
    padding: 12px;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    font-family: 'Sentient', Georgia, serif !important;
    font-size: 1rem;
    letter-spacing: 0.04em;
}

/* Buttons */
.stButton > button {
    font-family: 'Sentient', Georgia, serif !important;
    background-color: #c8a84b;
    color: #2a1f0a;
    border: none;
    border-radius: 3px;
    font-weight: 500;
    letter-spacing: 0.05em;
}

.stButton > button:hover {
    background-color: #b8962f;
    color: #fff;
}

/* Title */
h1, h2, h3 {
    letter-spacing: 0.02em;
    color: #2a1f0a;
}

/* Input fields */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background-color: #fffbf0;
    border: 1px solid #d4bc80;
    font-family: 'Sentient', Georgia, serif !important;
}

/* Divider */
hr {
    border-color: #d4bc80;
}
</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="FoodLog AI",
    page_icon="🍽️",
    layout="wide"
)

st.title("🍽️ FoodLog AI")
st.caption("Upload a photo of what you ate. The rest is handled.")

tab1, tab2 = st.tabs(["Log Food", "Dashboard"])

# ── Tab 1: Log Food ──────────────────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Upload a food photo",
            type=["jpg", "jpeg", "png", "webp"],
            help="Photo timestamp will be used as meal time"
        )
        note = st.text_area(
            "Notes (optional)",
            placeholder="e.g. 'chicken bowl, ~600 cal' or 'medium portion' or just leave blank",
            height=100
        )
        daily_goal = st.number_input(
            "Your daily calorie goal",
            min_value=1000,
            max_value=5000,
            value=2000,
            step=50
        )
        retro = st.toggle("Log for a different date/time")
        if retro:
            retro_date = st.date_input("Date", value=datetime.now().date())
            retro_time_str = st.text_input("Time (HH:MM)", value=datetime.now().strftime("%H:%M"))
            try:
                retro_time = datetime.strptime(retro_time_str, "%H:%M").time()
            except ValueError:
                st.error("Please enter time as HH:MM (e.g. 13:30)")
                retro_time = datetime.now().time()
            selected_timestamp = datetime.combine(retro_date, retro_time)
        else:
            selected_timestamp = datetime.now()
            
        if uploaded_file and st.button("Analyze & Log", type="primary"):
            with st.spinner("Analyzing your meal with Gemini..."):
                image_bytes = uploaded_file.read()

                # Save image to uploads/
                os.makedirs("uploads", exist_ok=True)
                timestamp = selected_timestamp
                image_filename = f"uploads/{timestamp.strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
                with open(image_filename, "wb") as f:
                    f.write(image_bytes)

                # Analyze with Gemini
                result = analyze_food(image_bytes, note, timestamp)

                if "error" in result:
                    st.error(f"Analysis failed: {result['error']}")
                else:
                    # Save entry
                    entry = {
                        "timestamp": timestamp.isoformat(),
                        "image_path": image_filename,
                        "note": note,
                        "daily_goal": daily_goal,
                        **result
                    }
                    save_entry(entry)
                    st.success("Logged!")

    with col2:
        if uploaded_file:
            st.image(uploaded_file, caption="Your meal", use_container_width=True)

# ── Tab 2: Dashboard ─────────────────────────────────────────────────────────
with tab2:
    entries = load_all()

    if not entries:
        st.info("No entries yet. Log your first meal to see your dashboard.")
    else:
        total = len(entries)
        avg_cal = sum(e.get("estimated_calories", 0) for e in entries) / total

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Meals Logged", total)
        m2.metric("Avg Calories / Meal", f"{avg_cal:.0f} kcal")

        # Most common meal time
        times = [e.get("meal_time_guess", "unknown") for e in entries]
        most_common_time = max(set(times), key=times.count) if times else "N/A"
        m3.metric("Most Common Meal Time", most_common_time.title())

        st.divider()

        col_left, col_right = st.columns([1.2, 1])

        with col_left:
            st.subheader("📅 Calorie Deficit Calendar")
            fig_heatmap = build_heatmap(entries)
            if fig_heatmap:
                st.plotly_chart(fig_heatmap, use_container_width=True)

        with col_right:
            st.subheader("🕐 When Do You Usually Eat?")
            fig_time = build_meal_time_chart(entries)
            if fig_time:
                st.plotly_chart(fig_time, use_container_width=True)

        st.subheader("📈 Calorie Trend")
        fig_trend = build_calorie_trend(entries)
        if fig_trend:
            st.plotly_chart(fig_trend, use_container_width=True)
        
        st.subheader("🗓️ Week View")
        week_html = build_week_grid(entries)
        if week_html:
            st.html(week_html)

        st.subheader("📋 Recent Entries")
        display_entries = []
        for e in reversed(entries[-10:]):
            display_entries.append({
                "Time": e.get("timestamp", "")[:16].replace("T", " "),
                "Dish": e.get("dish", "Unknown"),
                "Calories": e.get("estimated_calories", "?"),
                "Portion": e.get("portion", "?"),
                "Meal Time": e.get("meal_time_guess", "?").title(),
                "Note": e.get("note", "")[:40]
            })
        st.dataframe(display_entries, use_container_width=True)