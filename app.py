import streamlit as st
import json
import os
from pypdf import PdfReader
from pydantic import BaseModel, Field

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from g4f.client import Client

# Initialize G4F Client
client = Client()

# ==========================================
# STREAMLIT CONFIG & HIDE SIDEBAR & FIX CHAT INPUT
# ==========================================
st.set_page_config(
    page_title="AI Athletic Copilot", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to force hidden sidebar and position chat input at bottom
st.markdown("""
    <style>
        [data-testid="collapsedControl"] {display: none;}
        section[data-testid="stSidebar"] {display: none;}
        
        .stChatInput {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            width: 70% !important;
            z-index: 1000;
            background-color: white;
        }
        
        .main .block-container {
            padding-bottom: 120px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Advanced AI Athletic Copilot (LLMOps Architecture)")

# ==========================================
# 1. DYNAMIC PDF + FILE RAG KNOWLEDGE BASE
# ==========================================
KB_FILE_PATH = "athletic_knowledge_base.txt"

if not os.path.exists(KB_FILE_PATH):
    default_knowledge = """ISSN Nutrition Guidelines:
- Hypertrophy Protein Requirements: 1.6 to 2.2 grams per kg of body weight daily.
- Pre-workout Nutrition: Consume 1-2g/kg of carbs 1-2 hours prior to high-intensity training.
- Hydration Baseline: Daily Water = Body Weight (kg) * 0.035 Liters. Add 0.5L-1.0L per 60 min sweat session.
- Athlete Recovery: 8-9 hours sleep requirement. Cold water immersion (10-15°C for 10-15 mins) mitigates DOMS.
- Bedtime Protein: Casein protein (30-40g) prevents nocturnal muscle protein breakdown.
- Mental Prep: Tactical 4-7-8 breathing reduces acute pre-competition sympathetic autonomic stress.
"""
    with open(KB_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(default_knowledge)

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text content from uploaded PDF file."""
    reader = PdfReader(pdf_file)
    extracted_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            extracted_text += text + "\n"
    return extracted_text

def load_and_retrieve_rag(query: str, extra_pdf_text: str = "") -> str:
    """Retrieve relevant context from persistent KB file and optional uploaded PDF text."""
    combined_knowledge = ""
    if os.path.exists(KB_FILE_PATH):
        with open(KB_FILE_PATH, "r", encoding="utf-8") as f:
            combined_knowledge += f.read() + "\n"
    
    if extra_pdf_text:
        combined_knowledge += "\n--- Custom Uploaded Document Context ---\n" + extra_pdf_text

    lines = combined_knowledge.splitlines()
    keywords = query.lower().split()
    matched = [line.strip() for line in lines if any(kw in line.lower() for kw in keywords if len(kw) > 2)]
    
    if matched:
        return "\n".join(matched[:10])
    return "\n".join([line.strip() for line in lines[:8] if line.strip()])

# ==========================================
# 2. GUARDRAILS / INPUT VALIDATION
# ==========================================
ALLOWED_ATHLETIC_KEYWORDS = [
    "run", "running", "track", "field", "800m", "400m", "1500m", "sprint", "marathon",
    "workout", "training", "gym", "exercise", "pace", "warmup", "cooldown", "drills",
    "nutrition", "protein", "carbs", "calories", "diet", "meal", "hydration", "water",
    "recovery", "sleep", "stretching", "athlete", "fitness", "hiit", "fatigue", "coach",
    "hello", "hi", "hey", "plan", "schedule", "rest"
]

def validate_input_guardrail(user_prompt: str) -> bool:
    """Check if the user input falls within the athletic and sports domain."""
    text_lower = user_prompt.lower()
    return any(keyword in text_lower for keyword in ALLOWED_ATHLETIC_KEYWORDS)

# ==========================================
# 3. PYDANTIC SCHEMAS (Output Parsing)
# ==========================================
class MealItem(BaseModel):
    time: str = Field(description="Timing of the meal, e.g., 08:00 AM")
    meal_name: str = Field(description="Name of the meal")
    description: str = Field(description="Food items included")
    macros: str = Field(description="Estimated calories and macros")

class NutritionScheduleSchema(BaseModel):
    daily_calories: int = Field(description="Total daily calorie target")
    protein: str = Field(description="Total protein target in grams")
    carbs: str = Field(description="Total carbs target in grams")
    fats: str = Field(description="Total fats target in grams")
    meals: list[MealItem] = Field(description="List of structured meals")
    supplements: list[str] = Field(description="Recommended supplements")

class ExerciseItem(BaseModel):
    exercise: str = Field(description="Exercise name")
    sets: int = Field(description="Number of sets")
    reps: str = Field(description="Reps or duration")
    notes: str = Field(description="Form or tempo guidance")

class WorkoutSchema(BaseModel):
    workout_title: str = Field(description="Name of workout routine")
    warmup: str = Field(description="Warm-up routine")
    exercises: list[ExerciseItem] = Field(description="List of exercises")

nutrition_parser = JsonOutputParser(pydantic_object=NutritionScheduleSchema)
workout_parser = JsonOutputParser(pydantic_object=WorkoutSchema)

# ==========================================
# 4. TABS UI
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🥗 RAG Nutrition Planner", 
    "🏋️ Custom Gym Program", 
    "💧 Hydration & Recovery", 
    "💬 AI Coach Chat (Memory Enabled)"
])

# ------------------------------------------
# TAB 1: RAG NUTRITION PLANNER (WITH DYNAMIC PDF)
# ------------------------------------------
with tab1:
    st.subheader("🥗 RAG-Enhanced Sports Nutrition Schedule")
    
    uploaded_pdf = st.file_uploader("📄 (Optional) Upload custom PDF (Training plan, Medical test, or Guide):", type=["pdf"], key="pdf_rag")
    pdf_text_content = ""
    if uploaded_pdf is not None:
        try:
            pdf_text_content = extract_text_from_pdf(uploaded_pdf)
            st.success(f"PDF Successfully Loaded: '{uploaded_pdf.name}' ({len(pdf_text_content)} characters extracted)")
        except Exception as pdf_err:
            st.error(f"Failed to process PDF: {pdf_err}")

    col1, col2 = st.columns(2)
    with col1:
        sport = st.text_input("Sport / Discipline:", value="Football", key="rag_sport")
        weight = st.number_input("Weight (kg):", value=75.0, key="rag_w")
    with col2:
        schedule = st.text_area("Training Schedule:", value="Morning strength training + Evening practice", key="rag_sched")
        restrictions = st.text_input("Dietary Restrictions:", value="None", key="rag_rest")

    if st.button("Generate RAG Nutrition Schedule 🚀", key="btn_rag_nut"):
        with st.spinner("Retrieving scientific knowledge & generating plan..."):
            try:
                context = load_and_retrieve_rag(f"{sport} protein hydration recovery", extra_pdf_text=pdf_text_content)

                prompt = f"""You are an expert Sports Nutritionist.
Retrieved Knowledge Context:
{context}

Athlete Profile:
- Sport: {sport}
- Weight: {weight} kg
- Schedule: {schedule}
- Restrictions: {restrictions}

Format Instructions:
Return ONLY a JSON matching this schema:
{nutrition_parser.get_format_instructions()}
"""
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                raw_text = response.choices[0].message.content

                start_idx = raw_text.find('{')
                end_idx = raw_text.rfind('}') + 1
                parsed_data = json.loads(raw_text[start_idx:end_idx])

                st.session_state['rag_nut_data'] = parsed_data
                st.session_state['rag_context'] = context
                st.success("Plan Generated Successfully!")

            except Exception as e:
                st.error(f"Error: {e}")

    if 'rag_nut_data' in st.session_state:
        data = st.session_state['rag_nut_data']
        
        st.metric("Target Daily Calories", f"{data.get('daily_calories', 2500)} kcal")
        c1, c2, c3 = st.columns(3)
        c1.metric("Protein", data.get('protein', '150g'))
        c2.metric("Carbohydrates", data.get('carbs', '300g'))
        c3.metric("Fats", data.get('fats', '70g'))

        st.markdown("### 📅 Meal Schedule")
        st.table(data.get('meals', []))

        st.markdown("### 💊 Recommended Supplements")
        for supp in data.get('supplements', []):
            st.write(f"- {supp}")

        with st.expander("🔍 View Retrieved Document Context"):
            st.info(st.session_state.get('rag_context', ''))

# ------------------------------------------
# TAB 2: WORKOUT PROGRAM
# ------------------------------------------
with tab2:
    st.subheader("🏋️ Personalized Workout Split")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        goal = st.selectbox("Goal:", ["Hypertrophy", "Max Strength", "Explosive Power", "Endurance"])
        experience = st.selectbox("Experience Level:", ["Beginner", "Intermediate", "Advanced"])
    with col_g2:
        days = st.slider("Training Days / Week:", 2, 6, 4)
        equipment = st.text_input("Available Equipment:", value="Full Gym")

    if st.button("Generate Workout Routine 🏋️‍♂️", key="btn_gym"):
        with st.spinner("Generating workout structure..."):
            try:
                prompt = f"""You are an Elite Strength Coach.
Athlete Parameters:
- Goal: {goal}
- Level: {experience}
- Frequency: {days} days/week
- Equipment: {equipment}

Format Instruction:
Return ONLY a JSON matching this schema:
{workout_parser.get_format_instructions()}
"""
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                raw_text = response.choices[0].message.content
                start_idx = raw_text.find('{')
                end_idx = raw_text.rfind('}') + 1
                parsed_workout = json.loads(raw_text[start_idx:end_idx])

                st.session_state['workout_data'] = parsed_workout
                st.success("Workout Program Ready!")

            except Exception as e:
                st.error(f"Error: {e}")

    if 'workout_data' in st.session_state:
        w_data = st.session_state['workout_data']
        st.markdown(f"### 📋 {w_data.get('workout_title', 'Routine')}")
        st.info(f"**Warm-up:** {w_data.get('warmup', '')}")
        st.table(w_data.get('exercises', []))

# ------------------------------------------
# TAB 3: HYDRATION & RECOVERY
# ------------------------------------------
with tab3:
    st.subheader("💧 Hydration & Recovery Protocol")
    
    rec_weight = st.number_input("Enter Weight (kg):", value=75.0)
    workout_mins = st.number_input("Workout Duration (Minutes):", value=60)
    
    total_water = round((rec_weight * 0.035) + ((workout_mins / 60) * 0.75), 2)
    st.metric("Target Daily Fluid Intake", f"{total_water} Liters")
    
    st.markdown("""
    **💡 Science-Based Recovery Checklist:**
    - **Sleep:** Aim for 8-9 hours per night.
    - **Cold Water Therapy:** 10-15 minutes at 10-15°C to speed up HRV recovery.
    - **Night Protein:** 30g slow-digesting Casein protein before bed.
    """)

# ------------------------------------------
# TAB 4: CHAT WITH GUARDRAILS & STRUCTURED OUTPUT
# ------------------------------------------
with tab4:
    st.subheader("💬 AI Athletic Coach (with Conversation Memory)")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "system", 
                "content": (
                    "You are an Elite Sports Performance Coach. "
                    "Whenever the athlete asks for training plans, workout schedules, or track routines, "
                    "ALWAYS respond in a clean, structured Markdown format featuring:\n"
                    "1. Clear Headers (e.g., Warm-up, Main Session, Progression, Cool-down).\n"
                    "2. Bulleted lists for drills and preparation.\n"
                    "3. A clean Markdown Table when presenting multi-day or weekly schedules with columns: "
                    "[Day/Track, Warm up (KM), Session, Rest / Recovery, Cool down (KM)]."
                )
            },
            {"role": "assistant", "content": "Hello Athlete! Tell me your discipline, schedule, or performance targets, and I will structure a complete training program for you."}
        ]

    if st.button("🗑️ Clear Chat History", key="clear_chat"):
        st.session_state.chat_history = [st.session_state.chat_history[0]]
        st.rerun()

    chat_container = st.container()

    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] != "system":
                st.chat_message(msg["role"]).write(msg["content"])

    if user_input := st.chat_input("Ask about training, track schedules, or recovery..."):
        if not validate_input_guardrail(user_input):
            st.warning("🛡️ **Guardrail Triggered:** I am an AI Athletic Coach specialized exclusively in sports, workouts, nutrition, and recovery. Please keep questions relevant to your athletic goals.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            with chat_container:
                st.chat_message("user").write(user_input)

                with st.spinner("Analyzing parameters & generating structured routine..."):
                    try:
                        res = client.chat.completions.create(
                            model="gpt-4o",
                            messages=st.session_state.chat_history
                        )
                        bot_reply = res.choices[0].message.content
                        st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
                        st.chat_message("assistant").markdown(bot_reply)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Chat error: {e}")