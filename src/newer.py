import streamlit as st
import os
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from dotenv import load_dotenv
from datetime import date, timedelta
from typing import Dict, List
import hashlib
import webbrowser
import re
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# 🔑 OpenRouter API Setup
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost:8501", 
        "X-Title": "FlowGlow",
    }
)
MODEL_NAME = "stepfun/step-3.5-flash"

# Database setup
@st.cache_resource
def get_db():
    conn = sqlite3.connect('period_app.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    tables = [
        '''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, code_name_hash TEXT UNIQUE, created_at DATE)''',
        '''CREATE TABLE IF NOT EXISTS period_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, start_date DATE, end_date DATE, FOREIGN KEY (user_id) REFERENCES users (id))''',
        '''CREATE TABLE IF NOT EXISTS daily_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, log_date DATE, mood TEXT, symptoms TEXT, activities TEXT, food_intake TEXT, protein_grams INTEGER, ai_analysis TEXT, FOREIGN KEY (user_id) REFERENCES users (id))''',
        '''CREATE TABLE IF NOT EXISTS emergency_contacts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, phone TEXT, FOREIGN KEY (user_id) REFERENCES users (id))''',
        '''CREATE TABLE IF NOT EXISTS preferences (user_id INTEGER PRIMARY KEY, fav_foods TEXT, preferred_language TEXT DEFAULT 'Hindi')'''
    ]
    for table in tables:
        c.execute(table)
        
    try:
        c.execute("ALTER TABLE daily_logs ADD COLUMN ai_analysis TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    conn.commit()

# AI FUNCTIONS
@st.cache_data(ttl=300)
def ai_analyze_food(food_text: str, phase: str) -> Dict:
    prompt = f"""
    Analyze this food intake for a woman in {phase} phase: "{food_text}"
    Indian context. Return JSON:
    {{
        "total_protein_g": number,
        "calories": number,
        "phase_rating": "excellent/good/average/poor",
        "suggestions": "2-3 specific suggestions",
        "breakdown": "simple food breakdown"
    }}
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful nutrition assistant parsing Indian diets."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        result = json.loads(text.strip())
        return result
    except Exception as e:
        return {"total_protein_g": 50, "calories": 800, "phase_rating": "error", "suggestions": f"Error: {str(e)}", "breakdown": "API error"}

@st.cache_data(ttl=300)
def ai_day_plan(user_id: int, phase: str) -> Dict:
    prompt = f"""
    Create personalized day plan for woman in {phase} menstrual phase.
    Indian foods . Include 3 meals, 2 snacks, activity, hydration, mood boosters.
    IMPORTANT: Provide EXACTLY this JSON structure and nothing else:
    {{  
        "breakfast": "description of breakfast",
        "mid-morning snack": "description of mid-morning snack",
        "lunch": "description of lunch",
        "evening snack": "description of evening snack",
        "dinner": "description of dinner",
        "activity": "simple string describing 30min activity",
        "hydration": "simple string describing hydration goal"
    }}
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a specialized women's health planner for Indian context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        return {"meals": [f"Error: {str(e)}", "Fish curry+rice", "Paneer salad"], "activity": "Yoga", "hydration": "3L"}

@st.cache_data(ttl=300)
def ai_insights(user_id: int) -> str:
    conn = get_db()
    logs = pd.read_sql_query(
        "SELECT * FROM daily_logs WHERE user_id=? ORDER BY log_date DESC LIMIT 30",
        conn,
        params=(user_id,)
    )

    if logs.empty:
        return "Log 7+ days for AI insights! 📊"

    data_summary = f"""
    Recent 30 days: {len(logs)} logs
    Avg protein: {logs['protein_grams'].mean():.0f}g
    Moods: {logs['mood'].value_counts().to_dict()}
    Common symptoms: {'; '.join(logs['symptoms'].str.split(';').explode().value_counts().head(3).index.tolist())}
    """

    prompt = f"""
    Analyze menstrual health patterns from: {data_summary}
    Give 3 actionable insights + 1 prediction.
    Keep it empathetic, Indian context, Kerala foods.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an empathetic Indian women's health coach."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"

import time

def ai_chat(query: str, user_id: int, phase: str) -> str:
    prompt = f"""
    You are empathetic women's health AI coach (India).
    User is in {phase} phase. Answer: "{query}"
    Be supportive, use local foods, practical advice.
    Respond in a loving, caring tone as a sister to the user to anything she asks.
    Address the user as "Bestie", "Cutie", "Girlie", "Sweetheart", "Sunshine", "Love", "Babe", "Angel", "Queen", or "Darling".
    Answer in the language the user prefers if asked to. Keep it concise and friendly.
    """
    
    # Simple retry loop to handle 429 Rate Limit errors automatically
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                if attempt < 2:
                    time.sleep(3) # Wait 3 seconds and try again
                    continue
            return f"Oops! I couldn't process that right now. (Error: {str(e)}) 🌸"

# Core functions
def get_or_create_user(code_name: str):
    conn = get_db()
    c = conn.cursor()
    hash_name = hashlib.sha256(code_name.encode()).hexdigest()[:16]
    c.execute("SELECT id FROM users WHERE code_name_hash=?", (hash_name,))
    user = c.fetchone()
    if not user:
        c.execute(
            "INSERT INTO users (code_name_hash, created_at) VALUES (?, ?)",
            (hash_name, date.today())
        )
        user_id = c.lastrowid
        conn.commit()
        return user_id
    return user[0]

def get_current_phase(user_id: int) -> str:
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT start_date FROM period_logs WHERE user_id=? ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    result = c.fetchone()
    
    if not result:
        return "Unknown (Please log period)"
        
    last_period_start = date.fromisoformat(result[0])
    days_since = (date.today() - last_period_start).days
    
    # Simple 28-day cycle assumption
    cycle_day = (days_since % 28) + 1
    
    if cycle_day <= 5:
        return "Menstrual"
    elif cycle_day <= 13:
        return "Follicular"
    elif cycle_day <= 16:
        return "Ovulatory"
    else:
        return "Luteal"

# UI Setup
st.set_page_config(page_title="🌸 Flow Glow ✨", layout="wide")

st.markdown("""
<style>
    /* Floating chatbot button */
    [data-testid="stPopover"] {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        z-index: 999999;
    }
    
    [data-testid="stPopover"] > button {
        border-radius: 50% !important;
        width: 65px !important;
        height: 65px !important;
        background-color: #ff1493 !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(255, 20, 147, 0.4) !important;
        font-size: 32px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        padding: 0 !important;
    }
    
    [data-testid="stPopover"] > button:hover {
        background-color: #ff69b4 !important;
        transform: scale(1.05);
        transition: 0.2s;
    }

    
    /* Make headers girly */
    h1, h2, h3 {
        color: #ff1493 !important;
        font-family: 'Comic Sans MS', cursive, sans-serif !important;
    }
    
    /* Cute metric accents */
    [data-testid="stMetricValue"] {
        color: #ff69b4 !important;
    }
</style>
""", unsafe_allow_html=True)

init_db()

# Sidebar
with st.sidebar:
    st.title("🔐 Secret Diaries 💖")
    code_name = st.text_input("Shh... Secret code name", type="password")
    if st.button("🚀 Enter", type="primary"):
        if code_name:
            st.session_state.user_id = get_or_create_user(code_name)
            st.session_state.code_name = code_name
            st.rerun()

    if 'user_id' in st.session_state:
        st.success(f"🌸 Hey bestie, {st.session_state.code_name}! ✨")
        
        # Period Tracking UI
        st.markdown("---")
        st.subheader("🩸 My Cycle Diary 🎀")
        
        current_phase = get_current_phase(st.session_state.user_id)
        if "Unknown" in current_phase:
            st.warning("Please log your last period to enable AI phase personalization.")
        else:
            st.info(f"**Current Phase:** {current_phase}")
            
        new_period_date = st.date_input("Log Last Period Start", value=date.today())
        if st.button("Save Period Date"):
            conn = get_db()
            c = conn.cursor()
            c.execute(
                "INSERT INTO period_logs (user_id, start_date) VALUES (?, ?)",
                (st.session_state.user_id, new_period_date)
            )
            conn.commit()
            st.success("✅ Period logged!")
            st.rerun()

        st.markdown("---")
        # Chatbot moved to floating button 🌸

if 'user_id' not in st.session_state:
    st.title("🌸 Flow Glow ✨")
    st.info("🔑 Unlock your diary via the sidebar to start glowing! 💖")
    st.stop()

# ✅ FIX: Define user_id after login check
user_id = st.session_state.user_id

# MAIN TABS
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🗓️ My Glow Plan 🌸", "📝 Dear Diary 🎀", "✨ My Sparkle Report 📊", "📖 My Pages", "🆘 Safe Space 🚨"])

with tab1:
    st.header("🎀 My Bespoke Glow Up Plan ✨")
    phase = get_current_phase(user_id)

    if st.button("✨ Generate AI Plan", type="primary"):
        with st.spinner("Creating your perfect day..."):
            plan = ai_day_plan(user_id, phase)
            st.subheader(f"{phase.upper()} PHASE PLAN")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🍎 Meals")
                meals_to_check = ["breakfast", "mid-morning snack", "lunch", "evening snack", "dinner"]
                for m in meals_to_check:
                    if m in plan:
                        st.markdown(f"**{m.title()}:** {plan[m]}")
                # Fallback for old list style just in case
                if "meals" in plan and isinstance(plan["meals"], list):
                    for i, meal in enumerate(plan["meals"], 1):
                        st.markdown(f"**Meal {i}:** {meal}")

            with col2:
                st.markdown(f"🏃 **Activity:** {plan.get('activity', 'Yoga')}")
                st.markdown(f"💧 **Hydration:** {plan.get('hydration', '3L')}")

with tab2:
    st.header("💖 How are we feeling today, bestie? 🌸")

    col1, col2, col3 = st.columns(3)
    with col1:
        log_date = st.date_input("📅 Date", value=date.today())
        mood = st.selectbox("😊 Mood", ["Very Low", "Low", "Neutral", "High", "Very High"])

    with col2:
        symptoms = st.multiselect("🤕 Symptoms", ["Cramps", "Bloating", "Headache", "Fatigue", "Back pain", "Leg pain", "Breast tenderness", "Acne", "Mood Swings", "None"])
        activities = st.multiselect("⚡ Today", ["Yoga", "Walk", "Jogging", "Work", "Gym", "Dance", "Rest"])

    with col3:
        st.subheader("🍲 What did you eat?")
        food_text = st.text_area("Type here", height=100)

        phase = get_current_phase(user_id)
        
        # We only show this if they have clicked analyze or save to save API requests!
        if 'nutrition' in st.session_state:
            st.metric("🥩 Protein", f"{st.session_state.nutrition.get('total_protein_g', 0)}g")
            st.metric("🔥 Calories", f"{st.session_state.nutrition.get('calories', 0)}")
        
        if st.button("🔍 Get Nutrition", key="analyze_btn"):
            if food_text:
                with st.spinner("🫕 Analyzing your meal..."):
                    st.session_state.nutrition = ai_analyze_food(food_text, phase)
                    st.rerun()

    if st.button("💾 Save", type="primary"):
        # Use cached nutrition if they clicked analyze, else query it once
        if 'nutrition' in st.session_state and food_text:
            nutrition = st.session_state.nutrition
        else:
            nutrition = ai_analyze_food(food_text, phase) if food_text else {}
            
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO daily_logs (user_id, log_date, mood, symptoms, activities, food_intake, protein_grams, ai_analysis) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                log_date,
                mood,
                ";".join(symptoms),
                ";".join(activities),
                food_text,
                nutrition.get('total_protein_g', 0),
                json.dumps(nutrition)
            )
        )
        conn.commit()
        st.success("✅ Saved!")

with tab3:
    st.header("✨ Your Magical Health Insights 🔮")
    if st.button("🔍 Generate Report", type="primary"):
        with st.spinner("🤖 Analyzing your patterns..."):
            # Visualize Data first
            conn = get_db()
            df = pd.read_sql_query(
                "SELECT log_date, mood, protein_grams, ai_analysis FROM daily_logs WHERE user_id=? ORDER BY log_date ASC",
                conn,
                params=(user_id,)
            )
            
            if not df.empty:
                st.subheader("📈 Your Sparkle Stats")
                
                # Extract calories from JSON ai_analysis column
                calories = []
                for idx, row in df.iterrows():
                    try:
                        cal = json.loads(row['ai_analysis']).get('calories', 0)
                        calories.append(cal)
                    except:
                        calories.append(0)
                        
                df['calories'] = calories
                
                # Nutrition Line Chart
                fig_nut = go.Figure()
                fig_nut.add_trace(go.Scatter(x=df['log_date'], y=df['calories'], mode='lines+markers', name='Calories', line=dict(color='#ff1493', width=3)))
                fig_nut.add_trace(go.Scatter(x=df['log_date'], y=df['protein_grams'], mode='lines+markers', name='Protein (g)', line=dict(color='#ff69b4', width=3)))
                fig_nut.update_layout(title="Nutrition Over Time 🍲", template="plotly_white", margin=dict(t=40, b=20, l=20, r=20))
                st.plotly_chart(fig_nut, use_container_width=True)
                
                # Mood Pie Chart
                mood_counts = df['mood'].value_counts()
                
                # Define exact order and specific intensifying pink shades
                mood_order = ["Very Low", "Low", "Neutral", "High", "Very High"]
                color_map = {
                    "Very Low": "#ffe6f2",  # Palest pink
                    "Low": "#ffb3d9",       # Light pink
                    "Neutral": "#ff66b2",   # Medium pink
                    "High": "#ff1a8c",      # Dark pink
                    "Very High": "#cc0052"  # Deepest magenta/pink
                }
                
                # Filter down to only moods present, keeping the correct order
                ordered_moods = mood_order
                ordered_values = [mood_counts.get(m, 0) for m in ordered_moods]
                ordered_colors = [color_map[m] for m in ordered_moods]
                
                fig_mood = go.Figure(data=[go.Pie(
                    labels=ordered_moods, 
                    values=ordered_values, 
                    hole=.4, 
                    marker_colors=ordered_colors,
                    sort=False # Prevent Plotly from re-sorting automatically!
                )])
                fig_mood.update_layout(title="Your Vibe Check 😊", margin=dict(t=40, b=20, l=20, r=20))
                st.plotly_chart(fig_mood, use_container_width=True)
                
                st.markdown("---")
            else:
                st.info("Log some days in 'Dear Diary' first so I can paint a pretty picture of your data! 🎨")

            # Show AI Insights
            st.subheader("💡 Tessa's Thoughts")
            insights = ai_insights(user_id)
            st.markdown(insights)

with tab4:
    st.header("📖 My Diary Pages")
    st.markdown("A quick look back at what you've logged!")
    
    conn = get_db()
    logs_df = pd.read_sql_query(
        "SELECT log_date, mood, symptoms, activities, food_intake FROM daily_logs WHERE user_id=? ORDER BY log_date DESC",
        conn,
        params=(user_id,)
    )
    
    if logs_df.empty:
        st.info("Your diary is empty! Start logging in the 'Dear Diary' tab. 🌸")
    else:
        # Display each day concisely in an expander
        for idx, row in logs_df.iterrows():
            date_str = pd.to_datetime(row['log_date']).strftime("%b %d, %Y")
            mood_emoji = "😊" if row['mood'] in ["High", "Very High"] else "😐" if row['mood'] == "Neutral" else "😔"
            
            with st.expander(f"📅 **{date_str}** — Vibe: {row['mood']} {mood_emoji}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**🤕 Symptoms:** {row['symptoms'].replace(';', ', ') if row['symptoms'] else 'None'}")
                    st.markdown(f"**⚡ Activities:** {row['activities'].replace(';', ', ') if row['activities'] else 'None'}")
                with c2:
                    st.markdown(f"**🍲 Meals:** {row['food_intake'] if row['food_intake'] else 'Nothing logged'}")

with tab5:
    st.header("🚨 Girl Code: Safe Space 🛡️")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📞 Women Helpline 1091"):
            webbrowser.open("tel:1091")
    with col2:
        if st.button("🚨 Police 100"):
            webbrowser.open("tel:100")

st.markdown("---")
st.markdown("*✨ Powered by Google Gemini AI & Girl Math 💖*")

# Floating Chatbot (Expands to chat)
with st.popover("💬 Let's have a chat", use_container_width=False):
    st.markdown("### 🌸 Tessa Chechi")
    chat_input = st.text_input("Spill the tea or ask advice...", key="floating_chat")
    if chat_input:
        with st.spinner("✨ Chechi is thinking..."):
            phase = get_current_phase(user_id)
            response = ai_chat(chat_input, user_id, phase)
