from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List, Dict
import operator
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ChatMessage
from langchain.callbacks.base import BaseCallbackHandler

from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel

import sqlite3

import streamlit as st

import os

class AgentState(TypedDict):
    agent: str
    userState: Dict
    lnode: str
    initialMsg: str
    response: str
    reason: str
    fullResponse: str
#
# Classes for structured responses from LLM
#
class Category(BaseModel):
    requestCategory: str
    requestResponse: str
    responseReason: str

class QualifiedResponse(BaseModel):
    responseMsg: str
    responseReason: str

class requestHandler():
    def __init__(self,api_key):
        api_key=api_key
        self.model=ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)
        #self.model=ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)

        builder = StateGraph(AgentState)
        builder.add_node('front_end',self.frontEnd)
        builder.add_node('provide_human_response',self.provideHumanResponse)
        builder.add_node('make_up_story',self.makeUpStory)

        builder.set_entry_point('front_end')
        builder.add_conditional_edges('front_end',self.main_router,
        {"raise":END, 
        "time-off":END, 
        "other":"provide_human_response",
        })                                        
        
        builder.add_edge('provide_human_response',"make_up_story")
        builder.add_edge('make_up_story',END)
        memory = SqliteSaver(conn=sqlite3.connect(":memory:", check_same_thread=False))
        self.graph = builder.compile(
            checkpointer=memory,
            # interrupt_after=['planner', 'generate', 'reflect', 'research_plan', 'research_critique']
        )
        #png=self.graph.get_graph().draw_png('graph.png')
        print("Completed requestHandler init")

    def frontEnd(self, state: AgentState):
        print(f"START: frontEnd")
        my_prompt=f"""
                You are a highly trained HR Professional answering requests from employees.
                Please classify the employees's request.
                If the request is to ask for a compensation change, questionCategory is 'raise'
                If the request is to ask for time-off, questionCategory is 'time-off'
                For all other requests, questionCategory is 'other'

                After classifying the employee's request, provide a response to the employee.
                1. If questionCategory is 'raise', requestResponse is 'Sorry' and make up a reason for denial as responseReason.
                2. If questionCategory is 'time-off', requestResponse is 'No way' and make up a reason for denial as responseReason.
                3. If questionCategory is 'other', requestResponse is 'YES' and tell a joke as as the responseReason. 
                """
        llmResponse=self.model.with_structured_output(Category).invoke([
            SystemMessage(content=my_prompt),
            HumanMessage(content=state['initialMsg']),
        ])
        print(f"Response: {llmResponse}")
        category=llmResponse.requestCategory
        response=llmResponse.requestResponse
        reason=llmResponse.responseReason
        print(f"Category: {category}")
        print(f"END: frontEnd")
        return {
            'lnode':'front_end',
            'category':category,
            'response':response,
            'reason':reason,
            'fullResponse':f"{response} because {reason}",      
        }

    def main_router(self, state: AgentState):
        print(f"\n\nSTART: mainRouter with msg {state['initialMsg']} and category {state['category']}")
        if state['category'] == 'raise':
            return "raise"
        elif state['category'] == 'time-off':
            return "time-off"
        elif state['category'] == 'other':
            return "other"
        else:
            print(f"Unknown category {state['category']}")
            return END
    
    def provideHumanResponse(self, state: AgentState):
        print(f"\n\nSTART: provideHumanResponse with msg {state['initialMsg']}")
        st.sidebar.write(f"User said: {state['initialMsg']}. What should the response be?")
        while True:
            rsp=st.text_input("Response")
            if rsp:
                return {
                'lnode':'human_input',
                'category':category,
                'response':response,
                'reason':reason,
                'fullResponse':f"{rsp} because {reason}",      
                }

    def makeUpStory(self, state: AgentState):
        print(f"\n\nSTART: makeUpStory with msg {state['initialMsg']}")