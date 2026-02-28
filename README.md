## 📖 Project Description
FlowGlow AI is more than just a calendar; it is an intelligent health companion that understands the nuances of the menstrual cycle. Using the Step 3.5 Flash model, the application analyzes user logs to provide phase-specific nutrition advice, activity plans, and mood tracking. It is specifically localized for the Indian context, offering suggestions for Kerala-based foods and local wellness practices.

## 💻 Tech Stack
Frontend: Streamlit (Python)
AI Engine: Step-3.5-Flash (via OpenRouter API)
Database: SQLite3 (Local storage for secure, private diaries)
Data Visualization: Plotly Graph Objects (Interactive health metrics)
Language: Python 3.14 

✨ Features List
🎀 Bespoke Glow Up Plan: Generates phase-specific (Menstrual, Follicular, Ovulatory, Luteal) daily schedules including Indian meal plans and tailored activity goals.

🥩 AI Nutrition Parser: Automatically calculates protein and calories from natural language food descriptions (e.g., "I had 2 idlis and sambar") using AI analysis.

📈 Magical Health Reports: Visualizes mood trends ("Vibe Check") and nutritional intake over time with interactive charts to identify hormonal patterns.

🌸 Tessa Chechi (Floating Chatbot): A supportive, empathetic AI coach available 24/7 to provide sisterly advice, "spill the tea," or answer health questions in the user's preferred language.

🛡️ Girl Code: Safe Space: One-tap emergency access to women's helplines and police services.

🛠️ Installation Commands
To set up FlowGlow on your local machine, follow these steps:

Bash
# 1. Clone the repository
git clone https://github.com/your-username/flowglow.git
cd flowglow

# 2. Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install streamlit pandas plotly openai python-dotenv
🚀 Run Commands
Create a .env file in the root directory and add your API key:
OPENROUTER_API_KEY=your_key_here

Launch the application:

Bash
streamlit run newer.py
🏗️ Architecture Diagram
The application follows a modular structure:

UI Layer: Handles the "Girly" CSS styling and Streamlit tab navigation.

Logic Layer: Manages cycle calculations based on a 28-day model.

Data Layer: SQLite handles five relational tables (users, period_logs, daily_logs, emergency_contacts, and preferences).

AI Layer: Integrates the Step 3.5 Flash model for natural language processing and health coaching.

📜 API Documentation
The application integrates with the OpenRouter API to access LLM capabilities.

Base URL: https://openrouter.ai/api/v1

Model: stepfun/step-3.5-flash

Key Functions:

ai_analyze_food: Parses text to JSON containing protein and calorie counts.

ai_day_plan: Returns a structured daily schedule based on the user's current phase.

ai_chat: Provides conversational support using an empathetic system prompt.

## 👥 Team Members
Maneesha Manohar
Parvathy G

Supportive AI Coach: Tessa Chechi 🌸

✨ Powered by Google Gemini AI & Girl Math 💖
