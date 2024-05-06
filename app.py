from tempfile import NamedTemporaryFile
import os

import streamlit as st
from llama_index.core import VectorStoreIndex
from llama_index.llms.openai import OpenAI
from llama_index.readers.file import PDFReader
from dotenv import load_dotenv

load_dotenv()


st.set_page_config(
    page_title="OPENAI Resume Reviewer",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None,
)

if "messages" not in st.session_state.keys():  
    st.session_state.messages = [
        {"role": "assistant", "content": "Upload your resumé to get feedback!"}
    ]

uploaded_file = st.file_uploader("Upload resumé")
if uploaded_file:
    bytes_data = uploaded_file.read()
    with NamedTemporaryFile(delete=False) as tmp:  
        tmp.write(bytes_data)  
        with st.spinner(
            text="Loading and indexing the Streamlit docs – hang tight! This should take 1-2 minutes."
        ):
            reader = PDFReader()
            docs = reader.load_data(tmp.name)
            llm = OpenAI(
                model="gpt-3.5-turbo",
                temperature=0.0,
                system_prompt="You are an expert on the content of Product design resumé, provide detailed answers to the questions. Use the document to support your answers. Here is an good example: Here's a detailed review of the resume: Contact Information and Introduction. Clarity and Accessibility: The contact information is clear and easily accessible, which is great. However, the introduction could be enhanced by adding a brief professional summary or objective statement. This would provide immediate context about your career goals and key strengths. Skills. Relevance and Specificity: The skills listed are relevant to a UX design role, covering both technical and soft skills. To further improve, consider prioritizing these skills based on the job you're applying for, highlighting those most relevant at the top. Additionally, specifying your proficiency level in tools like Figma could be helpful.Professional Experience: Detail and Quantification: Your experience section is well-detailed, showcasing your roles and responsibilities. To strengthen this section, quantify your achievements (e.g., improved user engagement by X%, reduced bounce rate by Y%) and include more specific outcomes of your projects.Project Descriptions: You've mentioned significant projects, which is excellent. Including a brief context about the project scope and your contribution can provide more depth. For instance, describing the challenge, your approach, and the impact of your solution for the Mini Program project could make it more compelling. Education: Alignment and Clarity: Your educational background is clearly listed, showing a strong foundation in design. Clarifying how your degrees specifically contribute to your UX design expertise can make your education section more impactful. For example, mentioning particular courses or projects related to UX design could demonstrate your preparedness for the role. General Suggestions: Portfolio Link: While you've included your website, ensuring it's hyperlinked in a digital version of your resume can make it easier for employers to view your work. Consistency and Formatting: Ensure consistent formatting throughout the resume for a professional look. This includes alignment, bullet point style, and font usage.Cover Letter: If not already included, consider pairing your resume with a tailored cover letter. This can provide an opportunity to express your passion for UX design and how you align with the company's values and goals.",
            )
            index = VectorStoreIndex.from_documents(docs)
            
    os.remove(tmp.name) 

    if "chat_engine" not in st.session_state.keys():  # Initialize the chat engine
        st.session_state.chat_engine = index.as_chat_engine(
            chat_mode="condense_question", verbose=False, llm=llm
        )

if prompt := st.chat_input(
    "How can I help you?"
): 
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:  # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])


if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat_engine.stream_chat(prompt)
            st.write_stream(response.response_gen)
            message = {"role": "assistant", "content": response.response}
            st.session_state.messages.append(message) 

