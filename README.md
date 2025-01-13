# AI Interactive Storytelling Engine

An interactive storytelling engine powered by AI that creates dynamic narratives with branching storylines and character interactions.

## Overview

This project implements an AI-driven interactive storytelling system where:
- Stories evolve based on player choices
- Characters respond dynamically to situations
- Multiple possible story developments are generated at each step
- The narrative maintains consistency with themes and previous events

## Key Components

### Character System
- Dynamic character responses using AI
- Personality and background influence responses
- Conversation memory for contextual interactions
- Character-specific dialogue generation

### Narrative Engine
- Generates multiple possible story developments
- Creates branching narratives based on player choices
- Maintains story consistency and theme
- Provides meaningful choice consequences

### Story Management
- Tracks story state and progression
- Manages character interactions
- Handles narrative branching
- Maintains conversation history

## Installation

1. Ensure you have Python 3.10+ installed
2. Clone this repository
3. Install uv (next-generation Python package installer):
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
6. Install Ollama from https://ollama.ai
7. Pull required model:
```bash
ollama pull mistral
```

## Dependencies
Core dependencies:
- langchain==0.1.5
- langchain-community==0.0.13
- langchain-core==0.1.12
- langchain-ollama==0.0.5
- aiohttp==3.9.1
- pydantic==2.5.3

See requirements.txt for the complete list.

## Usage

Run the interactive story:
```bash
python main.py
```

The story will present:
1. Multiple possible story developments
2. Character responses to your choices
3. Options to continue or end the story

## Technical Details

### Technologies Used
- LangChain v0.1.5+ for AI integration
- Ollama for local LLM execution
- uv for dependency management
- Custom prompt templates for story generation
- Conversation memory for context retention

### Key Features
- Structured story development generation
- Dynamic character response system
- Memory-based conversation tracking
- Error handling and recovery
- Theme consistency maintenance

### Architecture
- Character class for managing individual characters
- NarrativeEngine class for story progression
- Prompt templates for consistent AI responses
- Memory systems for tracking context

## Example Story

The current implementation features a sci-fi narrative about:
- Sarah Chen: A former tech CEO investigating AI phenomena
- Dr. Marcus Webb: An AI researcher working on consciousness transfer
- Setting: An abandoned AI research facility
- Theme: The ethical limits of scientific progress

## Example Output
![app_image](docs/app.png)

## Contributing

Feel free to contribute by:
1. Opening issues for bugs or suggestions
2. Submitting pull requests with improvements
3. Adding new story scenarios or characters
4. Improving prompt templates

## License

This project is open source and available under the MIT License.