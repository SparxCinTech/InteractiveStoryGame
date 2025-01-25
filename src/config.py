from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class GameConfig:
    templates: Dict[str, Any]
    game_settings: Dict[str, Any]
    fallbacks: Dict[str, Any]
    characters: Dict[str, Any]
    initial_state: Dict[str, Any]

    @classmethod
    def load(cls, path: str = "config/game_config.yml") -> 'GameConfig':
        import yaml
        from yaml import Loader
        with open(path, 'r') as f:
            data = yaml.load(f, Loader=Loader)  # Use full loader for complex types
            return cls(
                templates=data.get('templates', {}),
                game_settings=data.get('game_settings', {}),
                fallbacks=data.get('fallbacks', {}),
                characters=data.get('characters', {}),
                initial_state=data.get('initial_state', {
                    'character_actions': {},
                    'story_state': 'Starting point'
                })
            )