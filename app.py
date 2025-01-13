import streamlit as st
from typing import Dict, Any
import json
from datetime import datetime
from story_save_manager import StorySaveManager
from main import Character, NarrativeEngine, GameState
import time

# Initialize session state
if 'game_state' not in st.session_state:
    st.session_state.game_state = GameState()
    st.session_state.story_history = []
    st.session_state.save_manager = StorySaveManager()
    st.session_state.current_developments = None
    st.session_state.story_started = False

def initialize_game():
    """Initialize or reset the game state"""
    game = st.session_state.game_state
    
    # Initialize characters if not already done
    if not game.characters:
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
    if not game.narrative:
        game.narrative = NarrativeEngine()
    
    # Set initial story state if not set
    if not game.story_state:
        game.story_state = """
        Location: Abandoned AI research facility
        Time: Night
        Current situation: Sarah has discovered evidence of illegal AI experiments
        """
    
    st.session_state.story_started = True

def save_game(save_type: str = "manual"):
    """Save current game state"""
    game = st.session_state.game_state
    save_manager = st.session_state.save_manager
    
    game_state = game.prepare_save_data()
    metadata = {
        "playtime": game.get_playtime(),
        "save_date": datetime.now().isoformat(),
        "history_length": len(st.session_state.story_history)
    }
    
    if save_type == "quick":
        save_id = save_manager.quick_save(game_state)
        st.success("Game quick saved!")
    elif save_type == "auto":
        save_id = save_manager.create_autosave(game_state)
        st.info("Game auto-saved.")
    else:
        save_id = save_manager.save_game(
            story_state=game_state["story_state"],
            character_states=game_state["character_states"],
            narrative_state=game_state["narrative_state"],
            metadata=metadata
        )
        st.success(f"Game saved! Save ID: {save_id}")

def load_game(save_id: str):
    """Load game state from save"""
    try:
        save_data = st.session_state.save_manager.load_game(save_id)
        st.session_state.game_state.load_save_data(save_data)
        st.success("Game loaded successfully!")
        return True
    except FileNotFoundError:
        st.error("Save file not found!")
        return False
    except Exception as e:
        st.error(f"Error loading save: {str(e)}")
        return False

def display_story_developments():
    """Display current story developments and choices"""
    game = st.session_state.game_state
    
    # Generate new developments if needed
    if not st.session_state.current_developments:
        st.session_state.current_developments = game.narrative.generate_developments(
            story_state=game.story_state,
            character_actions="Sarah examining computer records, Dr. Webb lurking in shadows",
            theme="The ethical limits of scientific progress"
        )
    
    # Display choices
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

def process_choice(choice_index: int):
    """Process player's choice and update game state"""
    game = st.session_state.game_state
    chosen_development = st.session_state.current_developments["developments"][choice_index]
    
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
    
    # Add to story history
    st.session_state.story_history.append({
        "development": chosen_development["description"],
        "sarah": sarah_response,
        "webb": webb_response,
        "timestamp": datetime.now().isoformat()
    })
    
    # Clear current developments
    st.session_state.current_developments = None
    
    # Autosave
    save_game("auto")
    
    # Rerun to update UI
    st.experimental_rerun()

def display_story_history():
    """Display the story history"""
    st.markdown("### Story So Far")
    
    for i, event in enumerate(st.session_state.story_history):
        with st.expander(f"Scene {i+1}", expanded=(i == len(st.session_state.story_history)-1)):
            st.write("**Event:**", event["development"])
            st.write("**Sarah:**", event["sarah"])
            st.write("**Dr. Webb:**", event["webb"])

def render_sidebar():
    """Render the sidebar with game controls"""
    with st.sidebar:
        st.markdown("### Game Controls")
        
        if not st.session_state.story_started:
            if st.button("Start New Game"):
                initialize_game()
                st.experimental_rerun()
        
        # Save/Load controls
        if st.session_state.story_started:
            if st.button("Quick Save"):
                save_game("quick")
            
            if st.button("Save Game"):
                save_game("manual")
            
            # Load game section
            st.markdown("### Load Game")
            saves = st.session_state.save_manager.list_saves()
            if saves:
                selected_save = st.selectbox(
                    "Select save to load:",
                    options=list(saves.keys()),
                    format_func=lambda x: f"Save {x} ({saves[x]['timestamp']})"
                )
                if st.button("Load Selected Save"):
                    if load_game(selected_save):
                        st.experimental_rerun()
            else:
                st.info("No saves available")

def main():
    st.title("AI Interactive Storytelling")
    
    # Sidebar
    render_sidebar()
    
    # Main content
    if not st.session_state.story_started:
        st.markdown("""
        ### Welcome to the AI Interactive Story
        
        You are about to enter a dynamic narrative where your choices shape the story.
        The tale follows Sarah Chen, a former tech CEO, as she investigates mysterious
        AI phenomena in an abandoned research facility.
        
        Start a new game using the controls in the sidebar.
        """)
    else:
        # Display story history
        display_story_history()
        
        # Display current choices
        display_story_developments()
        
        # Display game state info
        with st.expander("Game Info"):
            st.write("Playtime:", st.session_state.game_state.get_playtime())
            st.write("Scenes:", len(st.session_state.story_history))
            st.write("Current Location:", st.session_state.game_state.story_state.strip())

if __name__ == "__main__":
    main()