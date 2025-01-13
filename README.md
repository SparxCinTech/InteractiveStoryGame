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
3. Install dependencies:
```bash
pip install langchain-ollama langchain-core
```
4. Install Ollama and download the required model:
```bash
ollama pull llama3.2
```

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
- LangChain for AI integration
- Ollama for local LLM execution
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

## Contributing

Feel free to contribute by:
1. Opening issues for bugs or suggestions
2. Submitting pull requests with improvements
3. Adding new story scenarios or characters
4. Improving prompt templates

## License

This project is open source and available under the MIT License.