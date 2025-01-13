from typing import Dict, Any, Optional
import json
import os
from datetime import datetime
import uuid

class StorySaveManager:
    def __init__(self, save_directory: str = "saves"):
        """Initialize the save manager with a directory for save files.
        
        Args:
            save_directory (str): Directory to store save files
        """
        self.save_directory = save_directory
        os.makedirs(save_directory, exist_ok=True)
        
    def _get_save_path(self, save_id: str) -> str:
        """Get the full path for a save file."""
        return os.path.join(self.save_directory, f"save_{save_id}.json")
    
    def save_game(self, 
                 story_state: Dict[str, Any],
                 character_states: Dict[str, Any],
                 narrative_state: Dict[str, Any],
                 save_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save the current game state to a file.
        
        Args:
            story_state: Current state of the story
            character_states: States of all characters
            narrative_state: State of the narrative engine
            save_id: Optional ID for the save file (new one generated if None)
            metadata: Optional additional metadata about the save
            
        Returns:
            str: The save ID used
        """
        if save_id is None:
            save_id = str(uuid.uuid4())
            
        # Prepare save data
        save_data = {
            "save_id": save_id,
            "timestamp": datetime.now().isoformat(),
            "story_state": story_state,
            "character_states": character_states,
            "narrative_state": narrative_state,
            "metadata": metadata or {}
        }
        
        # Write to file
        save_path = self._get_save_path(save_id)
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
            
        return save_id
    
    def load_game(self, save_id: str) -> Dict[str, Any]:
        """Load a game state from a save file.
        
        Args:
            save_id: ID of the save to load
            
        Returns:
            Dict containing the saved game state
            
        Raises:
            FileNotFoundError: If save file doesn't exist
        """
        save_path = self._get_save_path(save_id)
        
        if not os.path.exists(save_path):
            raise FileNotFoundError(f"No save file found with ID: {save_id}")
            
        with open(save_path, 'r', encoding='utf-8') as f:
            save_data = json.load(f)
            
        return save_data
    
    def list_saves(self) -> Dict[str, Dict[str, Any]]:
        """List all available save files with their metadata.
        
        Returns:
            Dict mapping save IDs to their metadata
        """
        saves = {}
        
        for filename in os.listdir(self.save_directory):
            if filename.startswith("save_") and filename.endswith(".json"):
                save_id = filename[5:-5]  # Remove "save_" prefix and ".json" suffix
                try:
                    save_data = self.load_game(save_id)
                    saves[save_id] = {
                        "timestamp": save_data["timestamp"],
                        "metadata": save_data["metadata"]
                    }
                except (json.JSONDecodeError, KeyError):
                    continue  # Skip corrupted saves
                    
        return saves
    
    def delete_save(self, save_id: str) -> bool:
        """Delete a save file.
        
        Args:
            save_id: ID of the save to delete
            
        Returns:
            bool: True if file was deleted, False if it didn't exist
        """
        save_path = self._get_save_path(save_id)
        
        if os.path.exists(save_path):
            os.remove(save_path)
            return True
        return False

    def quick_save(self, game_state: Dict[str, Any], slot: int = 0) -> str:
        """Create a quick save in a numbered slot.
        
        Args:
            game_state: Current game state to save
            slot: Quick save slot number
            
        Returns:
            str: The save ID used
        """
        save_id = f"quicksave_{slot}"
        metadata = {
            "type": "quicksave",
            "slot": slot,
        }
        
        return self.save_game(
            story_state=game_state["story_state"],
            character_states=game_state["character_states"],
            narrative_state=game_state["narrative_state"],
            save_id=save_id,
            metadata=metadata
        )
    
    def quick_load(self, slot: int = 0) -> Dict[str, Any]:
        """Load a quick save from a numbered slot.
        
        Args:
            slot: Quick save slot number
            
        Returns:
            Dict containing the saved game state
            
        Raises:
            FileNotFoundError: If quick save doesn't exist
        """
        return self.load_game(f"quicksave_{slot}")
    
    def create_autosave(self, game_state: Dict[str, Any]) -> str:
        """Create an automatic save with timestamp.
        
        Args:
            game_state: Current game state to save
            
        Returns:
            str: The save ID used
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_id = f"autosave_{timestamp}"
        metadata = {
            "type": "autosave",
            "timestamp": timestamp,
        }
        
        return self.save_game(
            story_state=game_state["story_state"],
            character_states=game_state["character_states"],
            narrative_state=game_state["narrative_state"],
            save_id=save_id,
            metadata=metadata
        )