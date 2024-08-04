import streamlit as st
import os
from graph import requestHandler
import random


os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_API_KEY"]=st.secrets['LANGCHAIN_API_KEY']
os.environ["LANGSMITH_API_KEY"]=st.secrets['LANGCHAIN_API_KEY']

DEBUGGING=1

def start_chat():
    st.title('Test Human Agent Handler')
    avatars={"system":"💻🧠","user":"🧑‍💼","assistant":"🎓"}

    if "messages" not in st.session_state:
        st.session_state.messages = []

    #
    # Keeping context of conversations.
    # In practice, this will be say from the Slack - perhaps hash of user-id and channel-id.
    #
    if "thread-id" not in st.session_state:
        st.session_state.thread_id = random.randint(1000, 9999)
    thread_id = st.session_state.thread_id

    st.session_state.container=st.empty()

    # Reminder
    st.sidebar.write("""
    Use cases:
    1. Ask for raise: Say NO
    2. As for time-off: Say YES
    3. Other questions: Ask Human for response
    4. ...
    """)


    for message in st.session_state.messages:
        if message["role"] != "system":
            avatar=avatars[message["role"]]
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=avatars["user"]):
            st.markdown(prompt)
        abot=requestHandler(st.secrets['OPENAI_API_KEY'])
        thread={"configurable":{"thread_id":thread_id}}
        for s in abot.graph.stream({'initialMsg':prompt},thread):
            st.sidebar.write(abot.graph.get_state(thread))
            if DEBUGGING:
                print(f"GRAPH RUN: {s}")
                #st.write(s)
            for k,v in s.items():
                if DEBUGGING:
                    print(f"Key: {k}, Value: {v}")
                if resp := v.get("fullResponse"):
                    with st.chat_message("assistant", avatar=avatars["assistant"]):
                        st.write(resp)
                    st.session_state.messages.append({"role": "assistant", "content": resp})

if __name__ == '__main__':
    start_chat()
 