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
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            return cls(**data)