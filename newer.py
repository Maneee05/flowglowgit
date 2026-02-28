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
import google.generativeai as genai
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 🔑 Gemini API Setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3-flash-preview')

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
        response = model.generate_content(prompt)
        text = response.text.strip()
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
    Indian foods, Kerala location. Include 3 meals, 2 snacks, activity, hydration, mood boosters.
    IMPORTANT: Provide EXACTLY this JSON structure and nothing else:
    {{
        "meals": ["description of breakfast", "description of snack 1", "description of lunch", "description of snack 2", "description of dinner"],
        "activity": "simple string describing 30min activity",
        "hydration": "simple string describing hydration goal"
    }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
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
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

@st.cache_data(ttl=300)
def ai_chat(query: str, user_id: int, phase: str) -> str:
    prompt = f"""
    You are empathetic women's health AI coach (Kerala, India).
    User is in {phase} phase. Answer: "{query}"
    Be supportive, use local foods, practical advice.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "I'm here for you! Ask about nutrition, cycles, or mood. 🌸"

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
st.set_page_config(page_title="🤖 AI Period Coach", layout="wide")
init_db()

# Sidebar
with st.sidebar:
    st.title("🔐 AI Coach Login")
    code_name = st.text_input("Secret code name", type="password")
    if st.button("🚀 Connect AI", type="primary"):
        if code_name:
            st.session_state.user_id = get_or_create_user(code_name)
            st.session_state.code_name = code_name
            st.rerun()

    if 'user_id' in st.session_state:
        st.success(f"🤖 Hi {st.session_state.code_name}!")
        
        # Period Tracking UI
        st.markdown("---")
        st.subheader("🩸 Cycle Tracking")
        
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
        st.subheader("💬 AI Wellness Chat")
        chat_input = st.text_input("Ask AI anything...", key="chat")
        if chat_input:
            with st.spinner("🤖 AI thinking..."):
                phase = get_current_phase(st.session_state.user_id)
                response = ai_chat(chat_input, st.session_state.user_id, phase)
                st.markdown(response)

if 'user_id' not in st.session_state:
    st.title("🤖 AI Period Coach")
    st.info("🔑 Login via sidebar to unlock AI features!")
    st.stop()

# ✅ FIX: Define user_id after login check
user_id = st.session_state.user_id

# MAIN TABS
tab1, tab2, tab3, tab4 = st.tabs(["🤖 AI Day Plan", "📝 AI Food Log", "📊 AI Insights", "🚨 AI SOS"])

with tab1:
    st.header("🤖 Personalized AI Day Plan")
    phase = get_current_phase(user_id)

    if st.button("✨ Generate AI Plan", type="primary"):
        with st.spinner("AI creating your perfect day..."):
            plan = ai_day_plan(user_id, phase)
            st.subheader(f"{phase.upper()} PHASE PLAN")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🍎 AI Meals")
                for i, meal in enumerate(plan.get("meals", []), 1):
                    st.markdown(f"**Meal {i}:** {meal}")

            with col2:
                st.markdown(f"🏃 **Activity:** {plan.get('activity', 'Yoga')}")
                st.markdown(f"💧 **Hydration:** {plan.get('hydration', '3L')}")

with tab2:
    st.header("🤖 AI Food Analyzer")

    col1, col2, col3 = st.columns(3)
    with col1:
        log_date = st.date_input("📅 Date", value=date.today())
        mood = st.selectbox("😊 Mood", ["Very Low", "Low", "Neutral", "High", "Very High"])

    with col2:
        symptoms = st.multiselect("🤕 Symptoms", ["Cramps", "Bloating", "Headache", "Fatigue", "None"])
        activities = st.multiselect("⚡ Today", ["Yoga", "Walk", "Work", "Gym", "Rest"])

    with col3:
        st.subheader("🍲 What did you eat?")
        food_text = st.text_area("Type freely", height=100)

        phase = get_current_phase(user_id)
        if food_text:
            with st.spinner("🤖 AI analyzing your meal..."):
                nutrition = ai_analyze_food(food_text, phase)
                st.metric("🥩 AI Protein", f"{nutrition['total_protein_g']}g")
                st.metric("🔥 Calories", f"{nutrition['calories']}")

    if st.button("💾 Save AI Log", type="primary"):
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
        st.success("✅ AI Log Saved!")

with tab3:
    st.header("📊 AI Health Insights")
    if st.button("🔍 Generate AI Report", type="primary"):
        with st.spinner("🤖 AI analyzing your patterns..."):
            insights = ai_insights(user_id)
            st.markdown(insights)

with tab4:
    st.header("🚨 AI Emergency Support")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📞 Women Helpline 1091"):
            webbrowser.open("tel:1091")
    with col2:
        if st.button("🚨 Police 100"):
            webbrowser.open("tel:100")

st.markdown("---")
st.markdown("*🤖 Powered by Google Gemini AI*")