import streamlit as st
import openai
# from supabase import create_client, Client
from st_supabase_connection import SupabaseConnection

# Set your OpenAI API key and Supabase credentials in Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Supachat", page_icon="⚡")

avatar = {'user': '⚡', 'assistant': '🤖'}

# Initialize Supabase connection
supabase = st.connection("supabase", type=SupabaseConnection)

# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant."}]

def store_message(role, content):
    data = {"role": role, "content": content}
    supabase.table("chat_messages").insert(data).execute()

def generate_response(messages):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    return response.choices[0].message.content

# Chat input
user_input = st.chat_input("Supachat:", key="user_input")

if user_input:
    # Append user's message to session state messages
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Store the user's message in the database
    store_message("user", user_input)
    
    # Generate AI response
    ai_response = generate_response(st.session_state.messages)
    
    # Append AI's response to session state messages
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    
    # Store the assistant's message in the database
    store_message("assistant", ai_response)

# Display the conversation
for msg in st.session_state.messages[1:]:  # Skip the system message
    with st.chat_message(msg["role"], avatar=avatar[msg["role"]]):
        st.write(msg["content"])
