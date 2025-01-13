import streamlit as st
from typing import Dict, Any, List
from datetime import datetime
from story_save_manager import StorySaveManager
from game import GameState, Character, NarrativeEngine, GameConfig
from model_providers import ModelManager

# Initialize session state
if 'config' not in st.session_state:
    st.session_state.config = GameConfig.load()
    st.session_state.game_state = None
    st.session_state.story_history = []
    st.session_state.save_manager = StorySaveManager()
    st.session_state.model_manager = ModelManager()
    st.session_state.current_developments = None
    st.session_state.story_started = False
    st.session_state.selected_model = None

def get_available_models() -> Dict[str, bool]:
    return {name: available 
            for name, available in st.session_state.model_manager.list_available_models().items() 
            if available}

def initialize_game() -> bool:
    try:
        st.session_state.game_state = GameState(st.session_state.config)
        game = st.session_state.game_state
        model = st.session_state.model_manager.get_model(st.session_state.selected_model)
        game.narrative = NarrativeEngine(model=model, config=st.session_state.config)
        
        for char_config in st.session_state.config.characters.values():
            game.characters[char_config['name']] = Character(
                name=char_config['name'],
                personality=char_config['personality'],
                background=char_config['background'],
                model=model,
                config=st.session_state.config
            )
        
        st.session_state.story_started = True
        return True
        
    except Exception as e:
        st.error(f"Error initializing game: {str(e)}")
        return False

def save_game(save_type: str = "manual") -> None:
    game = st.session_state.game_state
    game_state = game.prepare_save_data()
    metadata = {
        "playtime": game.get_playtime(),
        "save_date": datetime.now().isoformat(),
        "history_length": len(st.session_state.story_history),
        "model": st.session_state.selected_model
    }
    
    try:
        if save_type == "quick":
            save_id = st.session_state.save_manager.quick_save(game_state)
            st.success("Game quick saved!")
        elif save_type == "auto":
            save_id = st.session_state.save_manager.create_autosave(game_state)
            st.info("Game auto-saved.")
        else:
            save_id = st.session_state.save_manager.save_game(
                story_state=game_state["story_state"],
                character_states=game_state["character_states"],
                narrative_state=game_state["narrative_state"],
                metadata=metadata
            )
            st.success(f"Game saved! Save ID: {save_id}")
    except Exception as e:
        st.error(f"Error saving game: {str(e)}")

def load_game(save_id: str) -> bool:
    try:
        save_data = st.session_state.save_manager.load_game(save_id)
        
        if "metadata" in save_data and "model" in save_data["metadata"]:
            st.session_state.selected_model = save_data["metadata"]["model"]
        
        if not st.session_state.game_state:
            initialize_game()
            
        st.session_state.game_state.load_save_data(save_data)
        st.success("Game loaded successfully!")
        return True
    except FileNotFoundError:
        st.error("Save file not found!")
        return False
    except Exception as e:
        st.error(f"Error loading save: {str(e)}")
        return False

def display_story_developments() -> None:
    game = st.session_state.game_state
    config = st.session_state.config
    
    if not st.session_state.current_developments:
        with st.spinner("Generating story developments..."):
            st.session_state.current_developments = game.narrative.generate_developments(
                story_state=game.story_state,
                character_actions=config.initial_state['character_actions'],
                theme=config.game_settings['default_theme']
            )
    
    st.markdown("### What happens next?")
    developments = st.session_state.current_developments["developments"]
    choice = st.radio(
        "Choose your next action:",
        options=range(len(developments)),
        format_func=lambda x: developments[x]["description"],
        key="choice_radio"
    )
    
    if st.button("Make Choice"):
        process_choice(choice)

def process_choice(choice_index: int) -> None:
    game = st.session_state.game_state
    chosen_development = st.session_state.current_developments["developments"][choice_index]
    game.story_state = chosen_development["new_situation"]
    
    characters = list(st.session_state.config.characters.values())
    protagonist = characters[0]
    antagonist = characters[1]
    
    with st.spinner("Generating character responses..."):
        protagonist_response = game.characters[protagonist['name']].respond(
            game.story_state, 
            chosen_development["description"]
        )
        antagonist_response = game.characters[antagonist['name']].respond(
            game.story_state, 
            protagonist_response
        )
    
    st.session_state.story_history.append({
        "development": chosen_development["description"],
        "protagonist": protagonist_response,
        "antagonist": antagonist_response,
        "timestamp": datetime.now().isoformat()
    })
    
    st.session_state.current_developments = None
    save_game("auto")
    st.rerun()

def display_story_history() -> None:
    st.markdown("### Story So Far")
    characters = list(st.session_state.config.characters.values())
    
    for i, event in enumerate(st.session_state.story_history):
        with st.expander(f"Scene {i+1}", expanded=(i == len(st.session_state.story_history)-1)):
            st.write("**Event:**", event["development"])
            st.write(f"**{characters[0]['name']}:**", event["protagonist"])
            st.write(f"**{characters[1]['name']}:**", event["antagonist"])

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Game Controls")
        
        if not st.session_state.story_started:
            available_models = get_available_models()
            if available_models:
                model_options = list(available_models.keys())
                default_model = next((model for model in model_options if "mistral" in model.lower()), model_options[0])
                st.session_state.selected_model = st.selectbox(
                    "Select AI Model:",
                    options=model_options,
                    index=model_options.index(default_model),
                    format_func=lambda x: f"{x} ({x.split('-')[1].upper()})"
                )
                
                if st.button("Start New Game"):
                    if initialize_game():
                        st.rerun()
            else:
                st.error("No AI models available. Please ensure Ollama or LM Studio is running.")
        
        if st.session_state.story_started:
            st.button("Quick Save", on_click=lambda: save_game("quick"))
            st.button("Save Game", on_click=lambda: save_game("manual"))
            
            st.markdown("### Current Model")
            st.info(f"Using: {st.session_state.selected_model}")
            
            st.markdown("### Load Game")
            saves = st.session_state.save_manager.list_saves()
            if saves:
                selected_save = st.selectbox(
                    "Select save to load:",
                    options=list(saves.keys()),
                    format_func=lambda x: (
                        f"Save {x} - "
                        f"{saves[x]['metadata'].get('model', 'unknown model')} "
                        f"({saves[x]['timestamp']})"
                    )
                )
                st.button("Load Selected Save", on_click=lambda: load_game(selected_save))
            else:
                st.info("No saves available")

def main():
    st.title("AI Interactive Storytelling")
    render_sidebar()
    
    if not st.session_state.story_started:
        st.markdown("""
        ### Welcome to the AI Interactive Story
        
        You are about to enter a dynamic narrative where your choices shape the story.
        Select an AI model and start a new game using the controls in the sidebar.
        """)
        
        st.markdown("### Available AI Models")
        available_models = get_available_models()
        if available_models:
            for name in available_models:
                st.success(f"{name}: Available")
        else:
            st.error("No AI models available. Please ensure Ollama or LM Studio is running.")
    else:
        display_story_history()
        display_story_developments()
        
        with st.expander("Game Info"):
            st.write("Model:", st.session_state.selected_model)
            st.write("Playtime:", st.session_state.game_state.get_playtime())
            st.write("Scenes:", len(st.session_state.story_history))
            st.write("Current Location:", st.session_state.game_state.story_state.strip())

if __name__ == "__main__":
    main()