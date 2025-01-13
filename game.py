from typing import Dict, Any, List, Union
import uuid
from langchain_ollama import OllamaLLM as Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver
import json
from story_save_manager import StorySaveManager
from datetime import datetime

class GameState:
    def __init__(self):
        self.save_manager = StorySaveManager()
        self.story_state = ""
        self.characters = {}
        self.narrative = None
        self.current_developments = None
        self.playtime_start = datetime.now()

    def get_playtime(self) -> str:
        delta = datetime.now() - self.playtime_start
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}:00"

    def prepare_save_data(self) -> Dict[str, Any]:
        """Prepare current game state for saving."""
        return {
            "story_state": {
                "current_scene": self.story_state,
                "timestamp": datetime.now().isoformat()
            },
            "character_states": {
                name: {
                    "personality": char.personality,
                    "background": char.background,
                    "memory": char.memory.memories if hasattr(char.memory, 'memories') else []
                }
                for name, char in self.characters.items()
            },
            "narrative_state": {
                "developments": self.current_developments["developments"] if self.current_developments else []
            }
        }

    def load_save_data(self, save_data: Dict[str, Any]) -> None:
        """Restore game state from save data."""
        self.story_state = save_data["story_state"]["current_scene"]
        
        # Recreate characters with saved state
        for name, state in save_data["character_states"].items():
            if name not in self.characters:
                self.characters[name] = Character(
                    name=name,
                    personality=state["personality"],
                    background=state["background"]
                )
            if hasattr(self.characters[name].memory, 'restore'):
                self.characters[name].memory.restore(state["memory"])

        # Restore narrative state if needed
        if "developments" in save_data["narrative_state"]:
            self.current_developments = {
                "developments": save_data["narrative_state"]["developments"]
            }

class Character:
    def __init__(self, name: str, personality: str, background: str, model: str = "llama3.2"):
        self.name = name
        self.personality = personality
        self.background = background
        self.llm = Ollama(model=model)
        
        # Character response template
        self.response_template = PromptTemplate(
            input_variables=["character_info", "situation", "input"],
            template="""
            You are playing the role of a character with the following traits:
            {character_info}
            
            Current situation: {situation}
            
            Respond to: {input}
            
            Respond in character, expressing emotions and staying true to your personality.
            """
        )
        
        # Create graph for character dialogue
        self.workflow = StateGraph(state_schema=MessagesState)
        
        # Define the function that generates character response
        def generate_response(state: MessagesState):
            messages = state["messages"]
            latest_message = messages[-1]
            
            character_info = f"""
            Name: {self.name}
            Personality: {self.personality}
            Background: {self.background}
            """
            
            # Format prompt with character info and latest message
            response = self.llm.invoke(
                self.response_template.format(
                    character_info=character_info,
                    situation=state.get("situation", ""),
                    input=latest_message.content
                )
            )
            
            # Return AI message
            return {"messages": [AIMessage(content=response)]}
        
        # Add nodes and edges to graph
        self.workflow.add_edge(START, "respond")
        self.workflow.add_node("respond", generate_response)
        
        # Add memory
        self.memory = MemorySaver()
        
        # Compile graph
        self.app = self.workflow.compile(checkpointer=self.memory)
        
        # Create unique thread ID for this character
        self.thread_id = uuid.uuid4()

    def respond(self, situation: str, input_text: str) -> str:
        # Create config with thread ID
        config = {"configurable": {"thread_id": self.thread_id}}
        
        # Create input state with situation and message
        input_state = {
            "messages": [HumanMessage(content=input_text)],
            "situation": situation
        }
        
        # Get response using graph
        for event in self.app.stream(input_state, config, stream_mode="values"):
            response = event["messages"][-1].content
            
        return response

class NarrativeEngine:
    def __init__(self, model: str = "llama3.2"):
        self.llm = Ollama(model=model)
        
        # Story progression template
        self.progression_template = PromptTemplate(
            input_variables=["story_state", "character_actions", "theme"],
            template="""
            You are a master storyteller crafting an interactive narrative.

            Current story state:
            {story_state}
            
            Recent character actions:
            {character_actions}
            
            Story theme: {theme}
            
            Respond ONLY with a JSON object in this exact format (no other text):
            {{"developments":[{{"description":"First dramatic event","new_situation":"Resulting scenario","possible_actions":["Specific action 1","Specific action 2","Specific action 3"]}},{{"description":"Second dramatic event","new_situation":"Resulting scenario","possible_actions":["Specific action 1","Specific action 2","Specific action 3"]}},{{"description":"Third dramatic event","new_situation":"Resulting scenario","possible_actions":["Specific action 1","Specific action 2","Specific action 3"]}}]}}

            Rules:
            - Generate exactly 3 developments
            - Make events dramatic and engaging
            - Keep consistent with theme: {theme}
            - Use only double quotes
            - No line breaks in JSON
            """
        )
        
        # Create LCEL chain with JSON output parser
        self.json_parser = JsonOutputParser()
        self.progression_chain = self.progression_template.pipe(self.llm).pipe(self.json_parser)

    def generate_developments(self, story_state: str, character_actions: str, theme: str) -> Dict[str, List[Dict[str, Any]]]:
        try:
            # Create a structured prompt for each development
            developments = []
            for i in range(3):
                development_prompt = PromptTemplate(
                    input_variables=["story_state", "character_actions", "theme", "number"],
                    template="""
                    Based on:
                    Story state: {story_state}
                    Character actions: {character_actions}
                    Theme: {theme}
                    
                    Generate development #{number} with:
                    1. A description of what happens next
                    2. The new situation that results
                    3. Three possible actions characters could take
                    
                    Respond in this exact format (no other text):
                    DESCRIPTION: [your description]
                    SITUATION: [your situation]
                    ACTION1: [first action]
                    ACTION2: [second action]
                    ACTION3: [third action]
                    """
                )
                
                # Get response for this development
                response = development_prompt.format_prompt(
                    story_state=story_state,
                    character_actions=character_actions,
                    theme=theme,
                    number=i+1
                )
                result = self.llm.invoke(response.to_string())
                
                # Parse the structured response
                lines = result.strip().split('\n')
                development = {}
                actions = []
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('DESCRIPTION:'):
                        development['description'] = line[12:].strip()
                    elif line.startswith('SITUATION:'):
                        development['new_situation'] = line[10:].strip()
                    elif line.startswith('ACTION'):
                        actions.append(line.split(':', 1)[1].strip())
                
                development['possible_actions'] = actions
                developments.append(development)
            
            # Return in the expected format
            return {"developments": developments}
            
        except Exception as e:
            print(f"Error details: {str(e)}")  # Log the actual error for debugging
            # Return a more informative development option
            return {
                "developments": [{
                    "description": "As Sarah delves deeper into the facility's records, she uncovers a series of encrypted files that could hold crucial information about the AI experiments.",
                    "new_situation": "Sarah finds herself in a dimly lit server room, surrounded by humming machines and blinking lights. The encrypted files beckon, but accessing them could trigger security systems.",
                    "possible_actions": [
                        "Attempt to decrypt the files carefully",
                        "Search for physical evidence in the room",
                        "Try to locate Dr. Webb for answers"
                    ]
                }]
            }

def create_story_scene():
    # Initialize game state
    game = GameState()
    
    # Initialize characters
    game.characters["Sarah"] = Character(
        name="Sarah Chen",
        personality="Determined, analytical, but carries emotional wounds from past failures",
        background="Former tech CEO, now investigating mysterious AI phenomena"
    )
    
    game.characters["Dr. Webb"] = Character(
        name="Dr. Marcus Webb",
        personality="Brilliant but morally ambiguous, believes the ends justify the means",
        background="AI researcher working on consciousness transfer"
    )
    
    # Initialize narrative engine
    game.narrative = NarrativeEngine()
    
    # Initial story state
    game.story_state = """
    Location: Abandoned AI research facility
    Time: Night
    Current situation: Sarah has discovered evidence of illegal AI experiments
    """
    
    # Main game loop
    while True:
        # Save/Load menu
        print("\nGame Menu:")
        print("1. Continue Story")
        print("2. Quick Save")
        print("3. Quick Load")
        print("4. Save Game")
        print("5. Load Game")
        print("6. Exit")
        
        choice = input("Select option (1-6): ")
        
        if choice == "2":  # Quick Save
            game_state = game.prepare_save_data()
            save_id = game.save_manager.quick_save(game_state)
            print(f"Game quick saved. Save ID: {save_id}")
            continue
            
        elif choice == "3":  # Quick Load
            try:
                save_data = game.save_manager.quick_load()
                game.load_save_data(save_data)
                print("Game loaded from quick save.")
                continue
            except FileNotFoundError:
                print("No quick save found.")
                continue
                
        elif choice == "4":  # Save Game
            game_state = game.prepare_save_data()
            metadata = {
                "playtime": game.get_playtime(),
                "save_date": datetime.now().isoformat()
            }
            save_id = game.save_manager.save_game(
                story_state=game_state["story_state"],
                character_states=game_state["character_states"],
                narrative_state=game_state["narrative_state"],
                metadata=metadata
            )
            print(f"Game saved. Save ID: {save_id}")
            continue
            
        elif choice == "5":  # Load Game
            # List available saves
            saves = game.save_manager.list_saves()
            if not saves:
                print("No saves found.")
                continue
                
            print("\nAvailable saves:")
            for save_id, save_info in saves.items():
                print(f"ID: {save_id}")
                print(f"Date: {save_info['timestamp']}")
                if "playtime" in save_info["metadata"]:
                    print(f"Playtime: {save_info['metadata']['playtime']}")
                print()
                
            save_id = input("Enter save ID to load (or 'cancel'): ")
            if save_id.lower() == 'cancel':
                continue
                
            try:
                save_data = game.save_manager.load_game(save_id)
                game.load_save_data(save_data)
                print("Game loaded successfully.")
                continue
            except FileNotFoundError:
                print("Save file not found.")
                continue
                
        elif choice == "6":  # Exit
            # Create autosave before exiting
            game_state = game.prepare_save_data()
            game.save_manager.create_autosave(game_state)
            print("Game autosaved. Goodbye!")
            break
            
        # Generate possible developments
        game.current_developments = game.narrative.generate_developments(
            story_state=game.story_state,
            character_actions="Sarah examining computer records, Dr. Webb lurking in shadows",
            theme="The ethical limits of scientific progress"
        )
        
        # Present options to the player
        print("\nPossible actions:")
        for i, dev in enumerate(game.current_developments["developments"]):
            print(f"{i+1}. {dev['description']}")
        
        # Get player choice
        while True:
            try:
                choice = int(input("\nChoose an action (1-3): ")) - 1
                if 0 <= choice <= 2:
                    break
                print("Please enter a number between 1 and 3")
            except ValueError:
                print("Please enter a valid number")
                
        chosen_development = game.current_developments["developments"][choice]
        
        # Update story state
        game.story_state = chosen_development["new_situation"]
        
        # Generate character responses
        sarah_response = game.characters["Sarah"].respond(
            game.story_state, 
            chosen_development["description"]
        )
        webb_response = game.characters["Dr. Webb"].respond(
            game.story_state, 
            sarah_response
        )
        
        # Display results
        print(f"\nSarah: {sarah_response}")
        print(f"\nDr. Webb: {webb_response}")
        
        # Create periodic autosave
        if datetime.now().minute % 15 == 0:  # Autosave every 15 minutes
            game_state = game.prepare_save_data()
            game.save_manager.create_autosave(game_state)

if __name__ == "__main__":
    create_story_scene()