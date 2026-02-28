# 📖 Project Description

FlowGlow AI is more than just a calendar; it is an intelligent health companion that understands the nuances of the menstrual cycle. Using the Step 3.5 Flash model, the application analyzes user logs to provide phase-specific nutrition advice, activity plans, and mood tracking. It is specifically localized for the Indian context, offering suggestions for Kerala-based foods and local wellness practices.

# 💻 Tech Stack


Frontend: Streamlit (Python)

AI Engine: Step-3.5-Flash (via OpenRouter API)

Database: SQLite3 (Local storage for secure, private diaries)

Data Visualization: Plotly Graph Objects (Interactive health metrics)

Language: Python 3.14 

# ✨ Features List

🎀 Bespoke Glow Up Plan: Generates phase-specific (Menstrual, Follicular, Ovulatory, Luteal) daily schedules including Indian meal plans and tailored activity goals.

🥩 AI Nutrition Parser: Automatically calculates protein and calories from natural language food descriptions (e.g., "I had 2 idlis and sambar") using AI analysis.

📈 Magical Health Reports: Visualizes mood trends ("Vibe Check") and nutritional intake over time with interactive charts to identify hormonal patterns.

🌸 Tessa Chechi (Floating Chatbot): A supportive, empathetic AI coach available 24/7 to provide sisterly advice, "spill the tea," or answer health questions in the user's preferred language.

🛡️ Girl Code: Safe Space: One-tap emergency access to women's helplines and police services.

# 🛠️ Installation Commands

To set up FlowGlow on your local machine, follow these steps:

1. Clone the repository
git clone https://github.com/your-username/flowglow.git
cd flowglow

2. Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies
pip install streamlit pandas plotly openai python-dotenv

# 🚀 Run Commands

Create a .env file in the root directory and add your API key:
OPENROUTER_API_KEY=your_key_here

Launch the application:

streamlit run newer.py

# Screenshots

<img width="1917" height="637" alt="1" src="https://github.com/user-attachments/assets/c404a3db-2da0-47ce-8a19-893f94e38f63" />

<img width="1915" height="795" alt="2" src="https://github.com/user-attachments/assets/f19e837e-2f0b-48f4-8d1d-514f0c957d4a" />

<img width="1725" height="735" alt="Screenshot 2026-02-28 220942" src="https://github.com/user-attachments/assets/98313fe9-eade-4de7-9706-c7d5ceac15a4" />

<img width="1596" height="778" alt="Screenshot 2026-02-28 215656" src="https://github.com/user-attachments/assets/70f60c65-d401-455b-8b38-862c834e5ab6" />

<img width="1095" height="444" alt="Screenshot 2026-02-28 222727" src="https://github.com/user-attachments/assets/624c5f1e-3b19-4184-9bc0-2d8ccee882cc" />

# Demo Video Link

https://drive.google.com/file/d/113y7ZeKrXDdGjc1GumifpeieM_4yj-gp/view?usp=sharing


# 🏗️ Architecture Diagram  


<img width="404" height="397" alt="Screenshot 2026-02-28 184931" src="https://github.com/user-attachments/assets/51fac0a4-8622-4f23-a539-2c444e2b158a" />


# 📜 API Documentation

The application integrates with the OpenRouter API to access LLM capabilities.

Base URL: https://openrouter.ai/api/v1

Model: stepfun/step-3.5-flash

Key Functions:

ai_analyze_food: Parses text to JSON containing protein and calorie counts.

ai_day_plan: Returns a structured daily schedule based on the user's current phase.

ai_chat: Provides conversational support using an empathetic system prompt.

# 👥 Team Members
Maneesha Manohar

Parvathy G
