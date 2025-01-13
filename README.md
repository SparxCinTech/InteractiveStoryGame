# AI Interactive Storytelling Engine

An interactive storytelling engine powered by AI that creates dynamic narratives with branching storylines and character interactions.

![app_image](docs/app.png)

## Overview

This project implements an AI-driven interactive storytelling system where:
- Stories evolve based on player choices
- Characters respond dynamically using local LLMs
- Multiple possible story developments are generated at each step
- The narrative maintains consistency with themes and previous events

## Key Features

### AI Integration
- Multiple LLM support (Ollama, LM Studio)
- Model switching and configuration
- Local model execution
- Automatic model availability detection

### Web Interface
- Interactive Streamlit-based UI
- Story progression visualization
- Game state tracking and display
- Save/Load functionality with metadata
- Model selection and management
- Real-time character interactions

### Character System
- Dynamic character responses using AI
- Personality and background influence responses
- Conversation memory for contextual interactions
- Character-specific dialogue generation
- Model-specific response tuning

### Narrative Engine
- Multi-model story generation
- Branching narratives with choices
- Theme consistency maintenance
- Progress tracking and state management
- Automatic save points

## Installation

1. Ensure you have Python 3.10+ installed
2. Clone this repository
3. Install uv :
```bash
pip install uv
```
4. Create and activate virtual environment using uv:
```bash
uv venv
source .venv/bin/activate  # On Unix/macOS
.venv\Scripts\activate     # On Windows
```
5. Install project dependencies using uv:
```bash
uv pip install -r requirements.txt
```
6. Install and configure one or both LLM backends:
   - Ollama: Install from https://ollama.ai
     ```bash
     ollama pull mistral
     ```
   - LM Studio: Install from https://lmstudio.ai
     ```bash
     # Start LM Studio and load your chosen model
     ```

## Dependencies
Core dependencies:
- langchain==0.1.5
- langchain-community==0.0.13
- langchain-core==0.1.12
- langchain-ollama==0.0.5
- streamlit==1.32.0
- pydantic==2.5.3

See requirements.txt for complete list.

## Usage

### Starting the Interface
Run the Streamlit app:
```bash
streamlit run app.py
```

### Model Selection
1. Choose your preferred AI model:
   - Mistral (Ollama)
   - Mixtral (LM Studio)
2. Configure model parameters (optional)
3. Start new game or load saved game

### Playing the Story
1. Read the current situation
2. Choose from available actions
3. See character responses
4. Save progress or continue

### Save/Load Features
- Quick save/load
- Auto-save
- Manual saves with descriptions
- Model persistence in saves

## Components

### Model Providers
- Ollama support for local models
- LM Studio integration for additional models
- Model switching and fallbacks
- Parameter optimization

### Story Engine
- Dynamic narrative generation
- Character-driven responses
- Theme consistency
- Multiple choice paths
- State tracking

### Interface Features
- Model status monitoring
- Progress indicators
- Game state visualization
- Save management
- Error handling

## Project Structure
```
AIStoryTelling/
├── app.py              # Streamlit interface
├── game.py             # Core game logic
├── model_providers.py  # LLM integration
├── story_save_manager.py  # Save system
├── config/
│   └── models.yml      # Model configurations
├── saves/              # Save files
└── requirements.txt
```

## Development Status

### Completed Features ✅
- Multiple model support (Ollama, LM Studio)
- Model selection and configuration
- Save/Load system with model persistence
- Web interface with model monitoring
- Basic error handling and fallbacks

### In Progress 🚧
- Advanced model parameter tuning
- Response caching and optimization
- Extended model compatibility
- Analytics and metrics

See TODOS.md for detailed development roadmap.

## Contributing

Feel free to contribute by:
1. Opening issues for bugs or suggestions
2. Submitting pull requests with improvements
3. Adding new model integrations
4. Improving prompts and configurations

## License

This project is open source and available under the MIT License.