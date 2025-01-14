import streamlit as st
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from story_save_manager import StorySaveManager
from game import GameState, Character, NarrativeEngine, GameConfig
from model_providers import ModelManager
from speech_manager import SpeechManager
from drama_manager import DramaManager

async def init_speech_manager():
    try:
        speech_mgr = SpeechManager()
        return speech_mgr
    except Exception as e:
        st.error(f"Error initializing speech: {str(e)}")
        return None

def init_session_state():
    if 'config' not in st.session_state:
        st.session_state.config = GameConfig.load()
        st.session_state.game_state = None
        st.session_state.story_history = []
        st.session_state.save_manager = StorySaveManager()
        st.session_state.model_manager = ModelManager()
        st.session_state.current_developments = None
        st.session_state.story_started = False
        st.session_state.selected_model = None
        st.session_state.speech_enabled = False
        st.session_state.speech_manager = None
        st.session_state.drama_manager = None
        st.session_state.audio_cache = {}
        st.session_state.playing_audio = None
        st.session_state.custom_choice = ""
        
        # Initialize speech manager
        if 'speech_manager' not in st.session_state:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            st.session_state.speech_manager = loop.run_until_complete(init_speech_manager())

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
        
        # Initialize DramaManager with same model
        st.session_state.drama_manager = DramaManager(model=model)
        
        for char_config in st.session_state.config.characters.values():
            game.characters[char_config['name']] = Character(
                name=char_config['name'],
                personality=char_config['personality'],
                background=char_config['background'],
                model=model,
                config=st.session_state.config
            )
        
        if st.session_state.speech_enabled:
            init_speech_manager()
            
        st.session_state.story_started = True
        return True
        
    except Exception as e:
        st.error(f"Error initializing game: {str(e)}")
        return False

def save_game(save_type: str = "manual") -> None:
    try:
        game = st.session_state.game_state
        game_state = game.prepare_save_data()
        metadata = {
            "playtime": game.get_playtime(),
            "save_date": datetime.now().isoformat(),
            "history_length": len(st.session_state.story_history),
            "model": st.session_state.selected_model
        }
        
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

async def generate_speech_for_response(text: str, character_name: str) -> None:
    if st.session_state.speech_manager:
        try:
            audio, rate = await st.session_state.speech_manager.generate_speech(
                text=text,
                character_name=character_name
            )
            # Create unique filename for this response
            filename = f"cache/audio/response_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{character_name.replace(' ', '_')}.wav"
            import soundfile as sf
            sf.write(filename, audio, rate)
            return filename
        except Exception as e:
            st.error(f"Error generating speech: {str(e)}")
            return None
    return None

async def generate_character_responses(development: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    responses = {}
    game = st.session_state.game_state
    
    # First get base responses
    for char_config in st.session_state.config.characters.values():
        char_name = char_config['name']
        response = game.characters[char_name].respond(
            game.story_state, 
            development["description"]
        )
        responses[char_name] = response
    
    # Use DramaManager to enhance responses if available
    if st.session_state.drama_manager:
        try:
            dramatic_result = await st.session_state.drama_manager.generate_dramatic_story(
                character_responses=responses,
                current_state=game.story_state,
                narrative_engine=game.narrative
            )
            
            enhanced_responses = {}
            for char_name, response in dramatic_result['enhanced_responses'].items():
                enhanced_responses[char_name] = {
                    'text': response,
                    'audio_path': None,
                    'emotional_state': dramatic_result['analysis']['analysis']['emotions'].get(char_name, 'neutral')
                }
            
            # Add dramatic analysis
            enhanced_responses['_dramatic_analysis'] = dramatic_result['analysis']
            responses = enhanced_responses
        except Exception as e:
            st.warning(f"Drama enhancement failed: {str(e)}")
    else:
        # Convert basic responses to enhanced format
        enhanced_responses = {}
        for char_name, response in responses.items():
            enhanced_responses[char_name] = {
                'text': response,
                'audio_path': None,
                'emotional_state': 'neutral'
            }
        responses = enhanced_responses
    
    # Generate audio if enabled
    if st.session_state.speech_enabled:
        for char_name, response_data in responses.items():
            if char_name != '_dramatic_analysis':  # Skip analysis data
                audio_path = await generate_speech_for_response(
                    text=response_data['text'],
                    character_name=char_name
                )
                responses[char_name]['audio_path'] = audio_path
    
    return responses

def process_choice(choice_index: int) -> None:
    game = st.session_state.game_state
    chosen_development = st.session_state.current_developments["developments"][choice_index]
    
    if "possible_actions" in chosen_development and chosen_development["possible_actions"]:
        game.story_state = chosen_development["new_situation"]
    
    with st.spinner("Generating character responses..."):
        # Use asyncio.run() to handle coroutine
        character_responses = asyncio.run(generate_character_responses(chosen_development))
    
    development_audio = None
    if st.session_state.speech_enabled:
        development_audio = asyncio.run(generate_speech_for_response(chosen_development["description"]))
    
    st.session_state.story_history.append({
        "development": chosen_development["description"],
        "audio": development_audio,
        "responses": character_responses,
        "timestamp": datetime.now().isoformat(),
        "is_custom": not bool(chosen_development.get("possible_actions", []))
    })
    
    st.session_state.current_developments = None
    save_game("auto")
    st.rerun()

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
    max_choices = config.game_settings['max_choices']
    
    # Initialize custom choice in session state if not present
    if 'custom_choice' not in st.session_state:
        st.session_state.custom_choice = ""
    
    # Create columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        choice = st.radio(
            "Choose a default action:",
            options=range(len(developments[:max_choices])),
            format_func=lambda x: developments[x]["description"],
            key="choice_radio"
        )
    
    with col2:
        st.markdown("### Or write your own:")
        custom_text = st.text_area(
            "Custom action",
            value=st.session_state.custom_choice,
            height=100,
            placeholder="Write your own action here...",
            key="custom_choice_input"
        )
        st.session_state.custom_choice = custom_text
    
    if st.button("Make Choice"):
        if st.session_state.custom_choice.strip():
            # Create a custom development with user's text
            custom_development = {
                "description": st.session_state.custom_choice,
                "new_situation": game.story_state,  # Keep current situation
                "possible_actions": []  # No predefined actions for custom choice
            }
            # Insert custom development at chosen index
            developments.insert(choice, custom_development)
            process_choice(choice)
            # Clear custom choice after using it
            st.session_state.custom_choice = ""
        else:
            process_choice(choice)

def display_story_history() -> None:
    st.markdown("### Story So Far")
    
    for i, event in enumerate(st.session_state.story_history):
        with st.expander(f"Scene {i+1}", expanded=(i == len(st.session_state.story_history)-1)):
            # Display development text and audio button
            col1, col2 = st.columns([8, 2])
            with col1:
                st.write("**Event:**", event["development"])
            with col2:
                if event.get("audio"):
                    if st.button("🔊 Play", key=f"play_dev_{i}"):
                        st.session_state.playing_audio = event["audio"]
            
            # Display dramatic analysis if available
            responses = event.get("responses", {})
            if isinstance(responses, dict) and '_dramatic_analysis' in responses:
                with st.expander("Dramatic Analysis"):
                    analysis = responses["_dramatic_analysis"]["analysis"]
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Conflicts:**")
                        for conflict in analysis["conflicts"]:
                            st.write(f"- {conflict}")
                    with col2:
                        st.write("**Themes:**")
                        for theme in analysis["themes"]:
                            st.write(f"- {theme}")
            
            # Display character responses
            if isinstance(responses, dict):
                for char_name, response in responses.items():
                    if char_name != '_dramatic_analysis':  # Skip analysis data
                        col1, col2 = st.columns([8, 2])
                        with col1:
                            if isinstance(response, dict):
                                emotion = f" ({response.get('emotional_state', 'neutral')})"
                                st.write(f"**{char_name}**{emotion}:")
                                st.write(response['text'])
                            else:
                                st.write(f"**{char_name}:**", response)
                        
                        with col2:
                            audio_path = response.get('audio_path') if isinstance(response, dict) else None
                            if audio_path:
                                if st.button("🔊 Play", key=f"play_{char_name}_{i}"):
                                    st.session_state.playing_audio = audio_path
            
            # Display audio player if something is playing
            if st.session_state.playing_audio:
                st.audio(st.session_state.playing_audio)

def render_model_selection() -> None:
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

def render_game_controls() -> None:
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

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Game Controls")
        
        if not st.session_state.story_started:
            render_model_selection()
        else:
            render_game_controls()

def display_model_status() -> None:
    st.markdown("### Available AI Models")
    available_models = get_available_models()
    if available_models:
        for name in available_models:
            st.success(f"{name}: Available")
    else:
        st.error("No AI models available. Please ensure Ollama or LM Studio is running.")

def render_welcome_screen() -> None:
    st.markdown("""
    ### Welcome to the AI Interactive Story
    
    You are about to enter a dynamic narrative where your choices shape the story.
    Select an AI model and start a new game using the controls in the sidebar.
    """)
    display_model_status()

def render_game_screen() -> None:
    display_story_history()
    display_story_developments()
    
    with st.expander("Game Info"):
        st.write("Model:", st.session_state.selected_model)
        st.write("Playtime:", st.session_state.game_state.get_playtime())
        st.write("Scenes:", len(st.session_state.story_history))
        st.write("Current Location:", st.session_state.game_state.story_state.strip())

def main():
    st.title("AI Interactive Storytelling")
    init_session_state()
    render_sidebar()
    
    if not st.session_state.story_started:
        render_welcome_screen()
    else:
        render_game_screen()

if __name__ == "__main__":
    main()