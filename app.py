"""
app.py
------
Frontend entry point for the AI Study Assistant. Handles all Streamlit UI —
layout, session state, widgets — and delegates every AI / file-processing
task to backend.py.

Run with:
    streamlit run app.py
"""

import os

import streamlit as st

import backend


# --------------------------------------------------------------------------- #
# Page Config & Styling
# --------------------------------------------------------------------------- #

st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide",
)


def load_css(path: str) -> None:
    if os.path.exists(path):
        with open(path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css(os.path.join(os.path.dirname(__file__), "assets", "style.css"))


# --------------------------------------------------------------------------- #
# Client (cached across reruns)
# --------------------------------------------------------------------------- #

@st.cache_resource(show_spinner=False)
def get_cached_client():
    return backend.get_client()


try:
    client = get_cached_client()
except RuntimeError as e:
    st.error(str(e))
    st.stop()


# --------------------------------------------------------------------------- #
# Session State
# --------------------------------------------------------------------------- #

def init_state():
    defaults = {
        "material": None,            # backend.StudyMaterial instance
        "study_notes": None,
        "quiz": None,
        "quiz_submitted": False,
        "quiz_answers": {},
        "practice_questions": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_state()


def material_loaded() -> bool:
    return st.session_state.material is not None and st.session_state.material.is_loaded()


def reset_generated_content():
    st.session_state.study_notes = None
    st.session_state.quiz = None
    st.session_state.quiz_submitted = False
    st.session_state.quiz_answers = {}
    st.session_state.practice_questions = None


# --------------------------------------------------------------------------- #
# Sidebar — Upload & Process
# --------------------------------------------------------------------------- #

with st.sidebar:
    st.title("📚 Study Assistant")
    st.markdown("Upload your study material to get started.")

    uploaded_file = st.file_uploader(
        "Upload PDF or TXT file",
        type=["pdf", "txt"],
        help="Upload your lecture notes, textbook chapter, or article.",
    )

    if st.button("🚀 Process Material", use_container_width=True, type="primary"):
        if uploaded_file is None:
            st.warning("Please choose a file to upload first.")
        else:
            with st.spinner("Processing your material..."):
                try:
                    st.session_state.material = backend.load_file(
                        client, uploaded_file.name, uploaded_file.getvalue()
                    )
                    reset_generated_content()
                    st.success(f"Processed: {uploaded_file.name}")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Failed to process file: {e}")

    st.divider()

    if material_loaded():
        st.info(f"📎 Loaded: **{st.session_state.material.display_name}**")
        if st.button("🗑️ Clear Material", use_container_width=True):
            st.session_state.material = None
            reset_generated_content()
            st.rerun()
    else:
        st.caption("No material loaded yet.")


# --------------------------------------------------------------------------- #
# Main Area — Tabs
# --------------------------------------------------------------------------- #

st.title("AI Study Assistant")

tab_notes, tab_quiz, tab_practice = st.tabs(
    ["📄 Study Notes", "📝 Interactive Quiz", "🎯 Extra Practice Questions"]
)

# ----------------------------- Tab 1: Notes -------------------------------- #
with tab_notes:
    if not material_loaded():
        st.info("👋 Please upload and process a study material file in the sidebar to get started.")
    else:
        if st.button("✨ Generate Study Notes"):
            with st.spinner("Reading through your material and writing notes..."):
                try:
                    st.session_state.study_notes = backend.generate_study_notes(
                        client, st.session_state.material
                    )
                except Exception as e:
                    st.error(f"Something went wrong generating notes: {e}")

        if st.session_state.study_notes:
            st.markdown(st.session_state.study_notes)
            st.download_button(
                "⬇️ Download Notes (Markdown)",
                data=st.session_state.study_notes,
                file_name="study_notes.md",
                mime="text/markdown",
            )
        else:
            st.caption("Click 'Generate Study Notes' to synthesize your material into notes.")

# ----------------------------- Tab 2: Quiz --------------------------------- #
with tab_quiz:
    if not material_loaded():
        st.info("👋 Please upload and process a study material file in the sidebar to get started.")
    else:
        if st.button("🎲 Generate Quiz"):
            with st.spinner("Writing a 5-question quiz..."):
                try:
                    st.session_state.quiz = backend.generate_quiz(client, st.session_state.material)
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers = {}
                except Exception as e:
                    st.error(f"Something went wrong generating the quiz: {e}")

        quiz = st.session_state.quiz
        if quiz:
            with st.form("quiz_form"):
                for i, q in enumerate(quiz.questions):
                    st.markdown(f"**Q{i + 1}. {q.question}**")
                    selected = st.radio(
                        label=f"quiz_q_{i}",
                        options=q.options,
                        index=None,
                        key=f"quiz_radio_{i}",
                        label_visibility="collapsed",
                    )
                    st.session_state.quiz_answers[i] = selected
                    st.markdown("")

                submitted = st.form_submit_button("✅ Submit Quiz")
                if submitted:
                    st.session_state.quiz_submitted = True

            if st.session_state.quiz_submitted:
                score = 0
                st.divider()
                st.subheader("Results")
                for i, q in enumerate(quiz.questions):
                    user_answer = st.session_state.quiz_answers.get(i)
                    is_correct = user_answer == q.answer
                    if is_correct:
                        score += 1

                    if user_answer is None:
                        st.warning(f"Q{i + 1}: No answer selected.")
                    elif is_correct:
                        st.success(f"Q{i + 1}: ✅ Correct — {user_answer}")
                    else:
                        st.error(f"Q{i + 1}: ❌ You chose '{user_answer}'. Correct answer: '{q.answer}'")
                    st.caption(f"💡 {q.explanation}")

                st.divider()
                pct = int(100 * score / len(quiz.questions))
                st.metric("Your Score", f"{score} / {len(quiz.questions)}", f"{pct}%")
                if pct == 100:
                    st.balloons()
        else:
            st.caption("Click 'Generate Quiz' to create a 5-question multiple-choice quiz.")

# ------------------------- Tab 3: Extra Practice --------------------------- #
with tab_practice:
    if not material_loaded():
        st.info("👋 Please upload and process a study material file in the sidebar to get started.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            num_questions = st.slider("Number of questions", min_value=3, max_value=15, value=6)
        with col2:
            difficulty = st.selectbox(
                "Difficulty level",
                ["Foundational", "Intermediate", "Advanced / Exam-level"],
                index=1,
            )

        if st.button("🎯 Generate Practice Questions"):
            with st.spinner("Crafting high-yield practice questions..."):
                try:
                    st.session_state.practice_questions = backend.generate_practice_questions(
                        client, st.session_state.material, num_questions, difficulty
                    )
                except Exception as e:
                    st.error(f"Something went wrong generating practice questions: {e}")

        practice = st.session_state.practice_questions
        if practice:
            for i, pq in enumerate(practice.questions):
                with st.expander(f"Q{i + 1}. {pq.question}"):
                    st.markdown(f"**Focus area:** {pq.focus_area}")
                    st.markdown("**Model answer / key points:**")
                    st.markdown(pq.answer)
        else:
            st.caption("Set your preferences above and click 'Generate Practice Questions'.")
