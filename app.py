import streamlit as st
import openai, uuid
from st_supabase_connection import SupabaseConnection

st.set_page_config(page_title="Supachat", page_icon="⚡")
avatar = {'user': '⚡', 'assistant': '🤖'}
model = 'gpt-4o-mini'

# Initialize Supabase connection
supabase = st.connection("supabase", type=SupabaseConnection)
# Set your OpenAI API key and Supabase credentials in Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Initialize session state for chat history
if 'uuid' not in st.session_state or st.session_state.uuid is None:
    st.session_state.uuid = str(uuid.uuid4())

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'title' not in st.session_state:
    st.session_state.title = ""

if 'user_id' not in st.session_state:
    st.session_state.user_id = None

if 'user_email' not in st.session_state:
    st.session_state.user_email = None

# Functions
def new_chat():
   st.session_state.messages = []
   st.session_state.uuid = str(uuid.uuid4())

def list_chat():
    result = supabase.table("chat_messages").select("uuid", "title").eq("user_id", st.session_state.user_id).execute()
    # Use a dictionary to keep only the latest title for each uuid
    chat_dict = {}
    for item in result.data:
        if item['uuid'] is not None:  # Add this check
            chat_dict[item['uuid']] = item['title']
    # Convert the dictionary back to a list of dictionaries
    return [{'uuid': uuid, 'title': title} for uuid, title in chat_dict.items()]

def select_chat(uuid):
    if uuid is None:  # Add this check
        st.error("Invalid chat selected. Please try again.")
        return
    st.session_state.messages = []
    result = supabase.table("chat_messages").select("role", "content", "title").eq("uuid", uuid).order("created_at").execute()
    if result.data:
        st.session_state.messages = [{"role": item['role'], "content": item['content']} for item in result.data]
        st.session_state.uuid = uuid
        st.session_state.title = result.data[0]['title']
    else:
        st.warning(f"No messages found for chat with UUID: {uuid}")

def chat_stream(messages,model='gpt-4o-mini'):
  # Generate a response from the ChatGPT model
  completion = openai.chat.completions.create(
        model = model,
        messages= messages,
        stream = True
  )
  report = []
  res_box = st.empty()
  # Looping over the response
  for resp in completion:
      if resp.choices[0].finish_reason is None:
          # join method to concatenate the elements of the list 
          # into a single string, then strip out any empty strings
          report.append(resp.choices[0].delta.content)
          result = ''.join(report).strip()
          result = result.replace('\n', '')        
          res_box.write(result) 
  return result

def chat_completion(messages, model='gpt-4o-mini'):
  completion = openai.chat.completions.create(
        model=model,
        messages= messages,
  )
  return completion.choices[0].message.content

def chat_title(user_input):
  completion = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages= [{"role": "system", "content": "Create a short title for the conversation."},
                   {"role": "user", "content": user_input}],
  )
  return completion.choices[0].message.content

def store_message(role, content):
    data = {"role": role, "content": content, "uuid": st.session_state.uuid, "title": st.session_state.title}
    supabase.table("chat_messages").insert(data).execute()

st.logo('img/high-voltage.png')

# User Authentication Section
if st.session_state.user_id is None:
    st.subheader('Supachat')
    with st.form("Sign in"):
        st.write("**Log in**")
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input(label="Enter your email ID")
        with col2:
            password = st.text_input(
            label="Enter your password",
            placeholder="Min 6 characters",
            type="password",
            help="Password is encrypted",
        )
        if st.form_submit_button('Login⚡'):
            try:
                response = supabase.auth.sign_in_with_password({"email": email, "password": password}) 
                st.session_state.user_id = response.user.id
                st.session_state.user_email = response.user.email
                st.rerun()
            except Exception as e:
                st.error(str(e), icon="❌")
    st.write("To get early access to the Supachat, email slevin.an209@gadz.org")
   

else:
    with st.sidebar:
        st.title('Supachat')

        st.write(f"Howdy, {st.session_state.user_email}!")
        if st.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.user_id = None
            st.session_state.user_email = None
            st.session_state.messages = []
            st.session_state.uuid = None
            st.session_state.title = ""
            st.rerun()

        st.write("**Chats**")
        if st.button('New Chat 🐱'):
            new_chat()
            st.session_state.title = ""

        for chat in list_chat():
            if st.button(f'💬 {chat["title"]}'):
                if chat["uuid"] is not None:  # Add this check
                    select_chat(chat["uuid"])
                else:
                    st.error("Invalid chat selected. Please try again.")
        # st.sidebar.write(list_chat())

    # Display the conversation
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=avatar[msg["role"]]):
            st.write(msg["content"])

    # Chat input
    if user_input := st.chat_input("Supachat:"):
        # Append the text input to the conversation
        with st.chat_message('user',avatar=avatar['user']):
            st.write(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})
        # Generate a title for the conversation
        if st.session_state.title == "":
            st.session_state.title = chat_title(user_input)
        # Store the user's message in the database
        store_message("user", user_input)
        # Query the chatbot with the complete conversation
        with st.chat_message('assistant',avatar=avatar['assistant']):
            result = chat_stream(st.session_state.messages, model)
        st.session_state.messages.append({"role": "assistant", "content": result})
        # Store the assistant's message in the database
        store_message("assistant", result)
        st.rerun()

    #     # Debug
    # if st.sidebar.toggle('Debug'):
    #     st.sidebar.write('Session state:')
    #     st.sidebar.write(st.session_state)
