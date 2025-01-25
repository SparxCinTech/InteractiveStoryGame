from typing import Dict, Any
from langchain.llms import BaseLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver
import uuid
from dataclasses import dataclass
from .config import GameConfig

class Character:
    def __init__(self, name: str, personality: str, background: str,
                 conflict: str = "", motivation: str = "", secret: str = "",
                 model: BaseLLM = None, config: 'GameConfig' = None):
        self.name = name
        self.personality = personality
        self.background = background
        self.conflict = conflict
        self.motivation = motivation
        self.secret = secret
        self.llm = model
        self.config = config
        
        template_config = config.templates['character_response']
        self.response_template = PromptTemplate(
            input_variables=template_config['input_variables'],
            template=template_config['template']
        )
        
        self.workflow = StateGraph(state_schema=MessagesState)
        self.memory = MemorySaver()
        self.thread_id = uuid.uuid4()
        
        def generate_response(state: MessagesState):
            messages = state["messages"]
            latest_message = messages[-1]
            
            character_info = "\n".join([
                f"Name: {self.name}",
                f"Personality: {self.personality}",
                f"Background: {self.background}",
                f"Internal Conflict: {self.conflict}",
                f"Primary Motivation: {self.motivation}",
                f"Hidden Secret: {self.secret}"
            ])
            
            response = self.llm.invoke(
                self.response_template.format(
                    character_info=character_info,
                    situation=state.get("situation", ""),
                    input=latest_message.content
                )
            )
            
            return {"messages": [AIMessage(content=response)]}
        
        self.workflow.add_edge(START, "respond")
        self.workflow.add_node("respond", generate_response)
        self.app = self.workflow.compile(checkpointer=self.memory)

    def respond(self, situation: str, input_text: str) -> str:
        input_state = {
            "messages": [HumanMessage(content=input_text)],
            "situation": situation
        }
        config = {"configurable": {"thread_id": self.thread_id}}
        
        for event in self.app.stream(input_state, config, stream_mode="values"):
            response = event["messages"][-1].content
            
        return response