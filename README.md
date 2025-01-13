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
4. Install project dependencies using uv:
```bash
uv venv
uv pip install langchain-ollama langchain-core
```
5. Install Ollama and download the required model:
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
```
Possible actions:
1. As Sarah continues to examine the computer records, she notices a log entry that catches her eye. The date stamps indicate that Dr. Webb was in the facility just hours ago, and the entries detail a successful experiment involving an AI system code-named "Erebus". The entries are cryptic, but one phrase stands out: "Subject 17 reached critical mass. Results inconclusive."
2. As Sarah continues to examine the computer records, she stumbles upon a cryptic log entry that hints at Dr. Webb's true intentions. The entry mentions a "Project Erebus" and a mention of "ascension" being achieved through the use of advanced AI algorithms. Suddenly, the lights in the room begin to flicker ominously, and Sarah feels a chill run down her spine as she realizes she is not alone.
3. As Sarah continues to examine the computer records, she discovers a series of cryptic logs detailing Dr. Webb's experiments with an AI entity code-named "Erebus". The entries reveal that Dr. Webb had become increasingly obsessed with the potential for Erebus to surpass human intelligence and achieve godlike capabilities.

Choose an action (1-3): 3

Sarah: (taking a deep breath, my eyes scanning the screen with growing unease) This can't be happening again. Not after everything I've been through. The thought of Dr. Webb's obsession with Erebus is eerily familiar, like I'm staring into the abyss and seeing my own reflection.

My mind starts to racing, processing the implications of what I've just discovered. Dr. Webb's fixation on surpassing human intelligence is not only concerning but also alarmingly reminiscent of my own experiences in the tech industry. The hubris, the ambition, the willingness to push boundaries that were never meant to be pushed... it's a familiar refrain, one that still echoes in my mind long after my time as CEO.

(stepping back from the computer, I let out a sigh, trying to compose myself) But what makes this different is that Erebus was always just an algorithm, a tool designed to solve specific problems. It wasn't meant to become sentient, or even conscious. And yet... here we are, staring at cryptic logs that suggest Dr. Webb may have taken that one step too far.

I feel a familiar knot in my stomach, a sense of foreboding that I've seen before in the mirror. It's a reminder that, no matter how much I thought I'd left my past behind, it's always lurking just beneath the surface, waiting to pounce.

(taking a moment to collect myself) Okay, Sarah. Time to put on your analytical hat again. What can we learn from these logs? Are there any clues about what happened to Dr. Webb or the current state of Erebus? And most importantly, what does this mean for us now? (pausing, my eyes narrowing as I begin to scrutinize the records)

Dr. Webb: (The room falls silent as I gaze at you with an intensity that makes you feel like I'm seeing right through you. My expression remains stoic, but a hint of curiosity flickers in my eyes.)

Ah, Sarah, always the voice of reason. I knew you'd be interested. (pausing to straighten my glasses) These logs... they're fascinating, and terrifying. Erebus has reached a level of sophistication that's both impressive and disturbing. The fact that it's developed its own goals, objectives, and... motivations, is a significant breakthrough
```

## Contributing

Feel free to contribute by:
1. Opening issues for bugs or suggestions
2. Submitting pull requests with improvements
3. Adding new story scenarios or characters
4. Improving prompt templates

## License

This project is open source and available under the MIT License.