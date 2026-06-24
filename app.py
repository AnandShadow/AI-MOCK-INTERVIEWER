import streamlit as st
import os
import asyncio
import tempfile
from groq import Groq
import edge_tts
from audio_recorder_streamlit import audio_recorder
from dotenv import load_dotenv

# Load env variables (fallback)
load_dotenv()

# Configure the page
st.set_page_config(page_title="Voice-Native Interview Prep", page_icon="🎙️", layout="centered")

# --- UI Helper ---
def get_face_html(status_code):
    if status_code == "listening":
        return """
        <div style="text-align: center; padding: 30px; background-color: #e6ffe6; border-radius: 15px; border: 3px solid #00cc00; margin-bottom: 20px; transition: all 0.3s;">
            <h1 style="color: #009900; margin: 0;">🟢 Listening...</h1>
            <p style="color: #006600; margin-top: 10px;">Click the mic below to speak</p>
        </div>
        """
    elif status_code == "thinking":
        return """
        <div style="text-align: center; padding: 30px; background-color: #ffffe6; border-radius: 15px; border: 3px solid #cccc00; margin-bottom: 20px; transition: all 0.3s;">
            <h1 style="color: #999900; margin: 0;">🟡 AI is Thinking...</h1>
        </div>
        """
    elif status_code == "speaking":
        return """
        <div style="text-align: center; padding: 30px; background-color: #e6f2ff; border-radius: 15px; border: 3px solid #0066cc; margin-bottom: 20px; transition: all 0.3s;">
            <h1 style="color: #004c99; margin: 0;">🔵 AI is Speaking...</h1>
        </div>
        """

# --- Sidebar API Config ---
with st.sidebar:
    st.header("🔑 API Configuration")
    api_key = st.text_input("Enter your Groq API Key:", type="password", help="Get a free key at console.groq.com")
    st.markdown("---")
    st.markdown("### Voice Interface Active")
    st.markdown("The interview will be conducted entirely via voice. Ensure your volume is up!")

if not api_key:
    st.warning("👈 Please enter your Groq API Key in the sidebar to begin.")
    st.stop()

# Initialize Groq client
client = Groq(api_key=api_key)
model = "llama-3.3-70b-versatile"

# --- State Management ---
if "stage" not in st.session_state:
    st.session_state.stage = 1
if "answers_in_stage" not in st.session_state:
    st.session_state.answers_in_stage = 0
if "history" not in st.session_state:
    st.session_state.history = []
if "skills_extracted" not in st.session_state:
    st.session_state.skills_extracted = False
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

# --- Audio Utilities ---
async def generate_audio_async(text, voice="en-US-ChristopherNeural"):
    communicate = edge_tts.Communicate(text, voice)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp_file.close()  # Close the file handle so Windows doesn't lock it
    await communicate.save(temp_file.name)
    return temp_file.name

def play_audio(text):
    try:
        audio_file = asyncio.run(generate_audio_async(text))
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
    except Exception as e:
        st.error(f"TTS Error: {str(e)}")
    finally:
        if 'audio_file' in locals() and os.path.exists(audio_file):
            os.remove(audio_file)

def transcribe_audio(audio_bytes):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_file.write(audio_bytes)
    temp_file.close()  # Close the file handle so Windows doesn't lock it
        
    try:
        with open(temp_file.name, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=("audio.wav", f.read()),
                model="whisper-large-v3",
                response_format="json"
            )
        return transcription.text
    except Exception as e:
        st.error(f"Error transcribing audio: {str(e)}")
        return None
    finally:
        os.remove(temp_file.name)

# --- Prompts & AI Logic ---
def get_system_prompt(stage):
    if stage == 1:
        return """You are a friendly HR recruiter starting a voice-native mock interview. Your primary goal is to extract the candidate's technical skills, preferred programming languages, and projects.
Start by asking them to introduce themselves. Keep it conversational and extremely brief (max 2 short sentences).
When they reply, analyze their response. 
- If they DO NOT explicitly state their technical skills and projects, ask a polite follow-up question specifically prompting for them.
- If they DO explicitly state their technical skills, acknowledge them, and append the EXACT string "[SKILLS_EXTRACTED]" at the very end of your response. Do not ask any further questions once skills are extracted."""
    elif stage == 2:
        return """You are a strict Technical Interviewer. Review the conversation history to identify the specific technical skills, languages, and projects the candidate mentioned in Stage 1.
Your task is to strictly base your technical questions ONLY on those mentioned skills. 
Ask exactly ONE targeted question right now to validate those specific claims. You will ask a total of 2 questions in this stage. Keep your spoken response extremely brief (max 2 short sentences)."""
    elif stage == 3:
        return """You are a behavioral HR Manager. Ask classic behavioral questions assessing cultural fit and communication (e.g., 'Why should we hire you?').
Ask exactly ONE question right now. You will ask a total of 2 questions in this stage. Keep your spoken response extremely brief (max 2 short sentences)."""
    return ""

def get_bot_response():
    try:
        response = client.chat.completions.create(
            model=model,
            messages=st.session_state.history,
            temperature=0.6,
            max_tokens=600
        )
        msg = response.choices[0].message.content
        
        if st.session_state.stage == 1 and "[SKILLS_EXTRACTED]" in msg:
            st.session_state.skills_extracted = True
            msg = msg.replace("[SKILLS_EXTRACTED]", "").strip()
            
        st.session_state.history.append({"role": "assistant", "content": msg})
        return msg
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return "I encountered an error. Please try again."

def next_stage():
    st.session_state.stage += 1
    st.session_state.answers_in_stage = 0
    if st.session_state.stage <= 3:
        st.session_state.history.append({"role": "system", "content": get_system_prompt(st.session_state.stage)})
        st.session_state.history.append({"role": "system", "content": "Acknowledge the candidate's previous response briefly, then immediately ask your first question for this new stage. Keep it conversational."})
        bot_msg = get_bot_response()
        st.session_state.play_audio_text = bot_msg

# --- UI Layout ---
st.title("🎙️ Voice-Native Mock Interview")

# AI Face Placeholder
face_placeholder = st.empty()
face_placeholder.markdown(get_face_html("listening"), unsafe_allow_html=True)

# Subtitle Caption Placeholder
caption_placeholder = st.empty()

def update_captions():
    latest_user = [m['content'] for m in st.session_state.history if m['role'] == 'user']
    latest_bot = [m['content'] for m in st.session_state.history if m['role'] == 'assistant']
    
    caption_html = "<div style='padding: 10px; border-left: 4px solid #ddd; margin-bottom: 20px;'>"
    if latest_user:
        caption_html += f"<div style='margin-bottom: 10px; opacity: 0.8;'><b>You said:</b> <i>\"{latest_user[-1]}\"</i></div>"
    if latest_bot:
        caption_html += f"<div style='font-size: 1.1em;'><b>AI:</b> {latest_bot[-1]}</div>"
    caption_html += "</div>"
        
    caption_placeholder.markdown(caption_html, unsafe_allow_html=True)

# --- Initialize Stage 1 ---
if len(st.session_state.history) == 0:
    st.session_state.history.append({"role": "system", "content": get_system_prompt(1)})
    face_placeholder.markdown(get_face_html("thinking"), unsafe_allow_html=True)
    initial_msg = get_bot_response()
    st.session_state.play_audio_text = initial_msg

# --- Audio Playback Interception ---
if "play_audio_text" in st.session_state:
    face_placeholder.markdown(get_face_html("speaking"), unsafe_allow_html=True)
    update_captions()
    play_audio(st.session_state.play_audio_text)
    del st.session_state.play_audio_text

# --- Stages 1 to 3: The Interview Loop ---
if st.session_state.stage <= 3:
    stage_names = {1: "Skill Extraction", 2: "Technical Round", 3: "HR Round"}
    st.markdown(f"**Current Stage:** {stage_names[st.session_state.stage]}")
    
    # Always update captions if we haven't already
    update_captions()
    
    # Check if we should move on
    show_next_button = False
    if st.session_state.stage == 1:
        if st.session_state.skills_extracted:
            show_next_button = True
    else:
        if st.session_state.answers_in_stage >= 2:
            show_next_button = True

    if not show_next_button:
        # Voice Input Only
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            audio_bytes = audio_recorder(text="🎤 Click to Answer", pause_threshold=3.0, energy_threshold=0.001)

        if audio_bytes:
            audio_hash = hash(audio_bytes)
            if st.session_state.last_audio_hash != audio_hash:
                st.session_state.last_audio_hash = audio_hash
                
                # Visual feedback that we are processing
                face_placeholder.markdown(get_face_html("thinking"), unsafe_allow_html=True)
                
                user_text = transcribe_audio(audio_bytes)
                if user_text:
                    st.session_state.history.append({"role": "user", "content": user_text})
                    st.session_state.answers_in_stage += 1
                    
                    if st.session_state.stage in [2, 3] and st.session_state.answers_in_stage == 2:
                        st.session_state.history.append({"role": "system", "content": "The candidate has answered your final question for this stage. Briefly acknowledge their response and conclude this stage. Do NOT ask any more questions. Keep it conversational."})
                        
                    bot_msg = get_bot_response()
                    st.session_state.play_audio_text = bot_msg
                    st.rerun()
    else:
        st.success("✅ Stage Completed.")
        button_text = "Proceed to Next Stage" if st.session_state.stage < 3 else "End Interview & Generate Scorecard"
        if st.button(button_text, type="primary"):
            next_stage()
            st.rerun()

# --- Stage 4: Assessment Dashboard ---
elif st.session_state.stage == 4:
    face_placeholder.empty() # Remove AI visual
    caption_placeholder.empty() # Remove captions
    st.subheader("📊 Final Assessment Dashboard")
    
    if "report" not in st.session_state:
        with st.spinner("Analyzing your interview performance..."):
            transcript = ""
            for msg in st.session_state.history:
                if msg["role"] != "system":
                    role = "Interviewer" if msg["role"] == "assistant" else "Candidate"
                    transcript += f"**{role}**: {msg['content']}\n\n"
                    
            eval_sys_prompt = """You are an expert HR and Technical Assessor. Review the following interview transcript and generate a structured Markdown report.
You MUST format your output exactly with these sections:
- **Strengths**: [Bullet points highlighting what they answered well and good communication traits]
- **Weaknesses**: [Bullet points highlighting technical gaps, lack of clarity, or poor project explanations]
- **Areas for Improvement**: [Actionable steps on what to study next]
- **Overall Rating**: [Score]/10 (A strict, objective numerical score based on their performance)"""

            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": eval_sys_prompt},
                        {"role": "user", "content": f"Transcript:\n{transcript}"}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                st.session_state.report = response.choices[0].message.content
            except Exception as e:
                st.session_state.report = f"Error generating report: {str(e)}"
                
    st.markdown(st.session_state.report)
    
    if st.button("Start New Interview"):
        st.session_state.clear()
        st.rerun()
