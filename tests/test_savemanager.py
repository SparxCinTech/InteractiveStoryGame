import pytest
from story_save_manager import StorySaveManager
import os
import shutil

@pytest.fixture
def save_manager():
    """Create a test save manager and clean up after tests."""
    test_save_dir = "test_saves"
    manager = StorySaveManager(save_directory=test_save_dir)
    yield manager
    # Cleanup
    if os.path.exists(test_save_dir):
        shutil.rmtree(test_save_dir)

def test_basic_save_load(save_manager):
    # Test data
    test_state = {
        "story_state": {
            "current_scene": "abandoned_lab",
            "time": "night",
            "events": ["discovery_of_files", "power_outage"]
        },
        "character_states": {
            "sarah": {
                "location": "server_room",
                "mood": "determined",
                "inventory": ["flashlight", "keycard"]
            },
            "dr_webb": {
                "location": "hidden",
                "mood": "calculating"
            }
        },
        "narrative_state": {
            "tension_level": "high",
            "active_plots": ["mystery_files", "power_failure"],
            "available_actions": ["investigate_noise", "check_files", "find_exit"]
        }
    }

    # Save the game
    save_id = save_manager.save_game(
        story_state=test_state["story_state"],
        character_states=test_state["character_states"],
        narrative_state=test_state["narrative_state"],
        metadata={"chapter": 1, "playtime": "00:45:30"}
    )

    # Load the game
    loaded_state = save_manager.load_game(save_id)

    # Verify save/load worked correctly
    assert loaded_state["story_state"] == test_state["story_state"]
    assert loaded_state["character_states"] == test_state["character_states"]
    assert loaded_state["narrative_state"] == test_state["narrative_state"]
    assert loaded_state["metadata"]["chapter"] == 1

def test_quick_save_load(save_manager):
    test_state = {
        "story_state": {"scene": "lab"},
        "character_states": {"sarah": {"mood": "focused"}},
        "narrative_state": {"tension": "medium"}
    }

    # Create quick save
    save_manager.quick_save(test_state, slot=1)

    # Load quick save
    loaded_state = save_manager.quick_load(slot=1)

    assert loaded_state["story_state"] == test_state["story_state"]
    assert loaded_state["metadata"]["type"] == "quicksave"

def test_autosave(save_manager):
    test_state = {
        "story_state": {"scene": "corridor"},
        "character_states": {"sarah": {"mood": "nervous"}},
        "narrative_state": {"tension": "high"}
    }

    # Create autosave
    save_id = save_manager.create_autosave(test_state)

    # Load autosave
    loaded_state = save_manager.load_game(save_id)

    assert loaded_state["story_state"] == test_state["story_state"]
    assert loaded_state["metadata"]["type"] == "autosave"

def test_list_saves(save_manager):
    # Create a few saves
    test_state = {
        "story_state": {},
        "character_states": {},
        "narrative_state": {}
    }

    save_manager.quick_save(test_state, slot=1)
    save_manager.create_autosave(test_state)
    
    # List saves
    saves = save_manager.list_saves()
    
    assert len(saves) == 2
    assert any(save["metadata"]["type"] == "quicksave" for save in saves.values())
    assert any(save["metadata"]["type"] == "autosave" for save in saves.values())