from typing import Dict, Any, List
import uuid
import yaml
from dataclasses import dataclass
from langchain.llms import BaseLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from .story_save_manager import StorySaveManager
from .character import Character
from .narrative_engine import NarrativeEngine
from .drama_manager import DramaManager
from .config import GameConfig
from datetime import datetime


class GameState:
    def __init__(self, config: GameConfig):
        self.config = config
        self.save_manager = StorySaveManager()
        self.story_state = self._format_initial_state()
        self.characters = {}
        self.narrative = None
        self.current_developments = None
        self.playtime_start = datetime.now()

    def _format_initial_state(self) -> str:
        return "\n".join([
            f"Location: {self.config.initial_state['location']}",
            f"Time: {self.config.initial_state['time']}",
            f"Current situation: {self.config.initial_state['situation']}"
        ])

    def get_playtime(self) -> str:
        delta = datetime.now() - self.playtime_start
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}:00"

    def prepare_save_data(self) -> Dict[str, Any]:
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
        self.story_state = save_data["story_state"]["current_scene"]
        
        for name, state in save_data["character_states"].items():
            if name not in self.characters:
                char_config = self.config.characters.get(name.lower(), {})
                self.characters[name] = Character(
                    name=state.get('name', char_config.get('name')),
                    personality=state.get('personality', char_config.get('personality')),
                    background=state.get('background', char_config.get('background')),
                    conflict=char_config.get('conflict', ''),
                    motivation=char_config.get('motivation', ''),
                    secret=char_config.get('secret', ''),
                    model=self.narrative.llm,
                    config=self.config
                )
            if hasattr(self.characters[name].memory, 'restore'):
                self.characters[name].memory.restore(state["memory"])

        if "developments" in save_data["narrative_state"]:
            self.current_developments = {
                "developments": save_data["narrative_state"]["developments"]
            }



def create_story_scene():
    from model_providers import ModelManager
    config = GameConfig.load()
    game = GameState(config)
    model_manager = ModelManager()
    base_model = model_manager.get_model()
    game.narrative = NarrativeEngine(model=base_model, config=config)
    
    for char_id, char_config in config.characters.items():
        game.characters[char_config['name']] = Character(
            name=char_config['name'],
            personality=char_config['personality'],
            background=char_config['background'],
            conflict=char_config.get('conflict', ''),
            motivation=char_config.get('motivation', ''),
            secret=char_config.get('secret', ''),
            model=base_model,
            config=config
        )
    
    while True:
        print("\nGame Menu:")
        print("1. Continue Story")
        print("2. Quick Save")
        print("3. Quick Load")
        print("4. Save Game")
        print("5. Load Game")
        print("6. Exit")
        
        choice = input("Select option (1-6): ")
        
        if choice == "2":
            save_id = game.save_manager.quick_save(game.prepare_save_data())
            print(f"Game quick saved. Save ID: {save_id}")
        elif choice == "3":
            try:
                game.load_save_data(game.save_manager.quick_load())
                print("Game loaded from quick save.")
            except FileNotFoundError:
                print("No quick save found.")
        elif choice == "4":
            metadata = {"playtime": game.get_playtime(), "save_date": datetime.now().isoformat()}
            save_id = game.save_manager.save_game(
                **game.prepare_save_data(),
                metadata=metadata
            )
            print(f"Game saved. Save ID: {save_id}")
        elif choice == "5":
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
            if save_id.lower() != 'cancel':
                try:
                    game.load_save_data(game.save_manager.load_game(save_id))
                    print("Game loaded successfully.")
                except FileNotFoundError:
                    print("Save file not found.")
        elif choice == "6":
            game.save_manager.create_autosave(game.prepare_save_data())
            print("Game autosaved. Goodbye!")
            break
        else:
            game.current_developments = game.narrative.generate_developments(
                story_state=game.story_state,
                character_actions=config.initial_state['character_actions'],
                theme=config.game_settings['default_theme']
            )
            
            print("\nPossible actions:")
            for i, dev in enumerate(game.current_developments["developments"]):
                print(f"{i+1}. {dev['description']}")
            
            while True:
                try:
                    choice = int(input(f"\nChoose an action (1-{config.game_settings['max_choices']}): ")) - 1
                    max_choices = config.game_settings['max_choices']
                    if 0 <= choice < max_choices:
                        break
                    print(f"Please enter a number between 1 and {max_choices}")
                except ValueError:
                    print("Please enter a valid number")
            
            chosen_development = game.current_developments["developments"][choice]
            game.story_state = chosen_development["new_situation"]
            
            import random
            character_list = list(game.characters.keys())
            random.shuffle(character_list)
            lead_character = game.characters.get(character_list.pop())
            last_character_response = lead_character.respond(
                game.story_state, 
                chosen_development["description"]
            )
            print(f"\n{lead_character.name}: {last_character_response}")
            while character_list:
                random.shuffle(character_list)
                next_character = game.characters.get(character_list.pop())
                last_character_response = next_character.respond(
                    game.story_state, 
                    last_character_response
                )
                print(f"\n{next_character.name}: {last_character_response}")
            
            
            if datetime.now().minute % config.game_settings['autosave_interval'] == 0:
                game.save_manager.create_autosave(game.prepare_save_data())

if __name__ == "__main__":
    create_story_scene()