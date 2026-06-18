import streamlit as st
import requests

API_BASE = "https://medium-article-rag-assistant-five.vercel.app"


st.title("📚 Medium RAG Assistant")

question = st.text_input("Ask a question")

col1, col2 = st.columns(2)

# -----------------------
# BUTTON 1: QUERY RAG
# -----------------------
with col1:
    if st.button("Ask RAG"):
        if not question:
            st.warning("Please enter a question")
        else:
            with st.spinner("Thinking..."):
                res = requests.post(
                    f"{API_BASE}/api/prompt",
                    json={"question": question}
                )

                data = res.json()

            st.subheader("Answer")
            st.write(data["response"])

            st.subheader("Context")

            for c in data["context"]:
                st.markdown(
                    f"""
                    **{c['title']}**  
                    score: `{c['score']:.3f}`  
                    article_id: `{c['article_id']}`  
                    ---
                    """
                )

            st.subheader("Prompt (debug)")
            st.json(data["Augmented_prompt"])


# -----------------------
# BUTTON 2: STATS
# -----------------------
with col2:
    if st.button("Get Stats"):
        with st.spinner("Loading stats..."):
            res = requests.get(f"{API_BASE}/api/stats")
            stats = res.json()

        st.subheader("System Stats")
        st.json(stats)