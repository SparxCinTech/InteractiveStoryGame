from __future__ import annotations
import logging
from typing import Any, TypedDict
from traceback import format_exc
from typing import Any
from langchain.llms import BaseLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableSerializable

class DramaticAnalysis(TypedDict):
    conflicts: list[str]
    emotions: dict[str, str]
    plot_opportunities: list[str]
    themes: list[str]

class DramaManager:
    """Manages dramatic story progression and dialogue generation."""
    
    def __init__(self, model: BaseLLM, logger: logging.Logger | None = None):
        """Initialize the drama manager.
        
        Args:
            model: Language model to use for generation
        """
        self.llm = model
        self.logger = logger or logging.getLogger(__name__)
        self.json_parser = JsonOutputParser()

        # Configure chains with type hints
        self.drama_analysis_chain: RunnableSerializable = self._create_analysis_chain()

    def _create_analysis_chain(self) -> RunnableSerializable:
        """Create the dramatic analysis chain with validation."""
        return (
            self._create_analysis_template()
            | self.llm
            | self.json_parser
        )

    def _create_analysis_template(self) -> PromptTemplate:
        """Create and validate the drama analysis prompt template."""
        return PromptTemplate(
            input_variables=["responses", "current_state"],
            template=(
                "Analyze character responses for dramatic elements:\n\n"
                "Current State:\n{current_state}\n\n"
                "Character Responses:\n{responses}\n\n"
                "Identify:\n"
                "1. Key conflicts and tensions\n"
                "2. Character motivations/emotions\n"
                "3. Potential plot twists\n"
                "4. Dramatic themes\n\n"
                "Respond with JSON:\n"
                '{"analysis": {\n'
                '  "conflicts": ["..."],\n'
                '  "emotions": {"...": "..."},\n'
                '  "plot_opportunities": ["..."],\n'
                '  "themes": ["..."]\n}}\n'
            ),
            template_format="f-string"
        )
        
        # Template for enhancing drama in responses
        self.drama_enhancement_template = PromptTemplate(
            input_variables=["response", "analysis", "character"],
            template="""
            Enhance the following character response with more dramatic elements:
            
            Character: {character}
            Original Response: {response}
            Dramatic Analysis: {analysis}
            
            Make the response more dramatic by:
            1. Emphasizing emotional undertones
            2. Adding subtle hints at hidden motives
            3. Including dramatic gestures or actions
            4. Referencing underlying tensions
            
            Respond with enhanced dialogue only.
            """
        )
        
        self.json_parser = JsonOutputParser()
        self.drama_analysis_chain = self.drama_analysis_template.pipe(self.llm).pipe(self.json_parser)
    
    def analyze_dramatic_elements(
        self,
        character_responses: dict[str, str],
        current_state: str
    ) -> dict[str, DramaticAnalysis]:
        """Analyze responses for dramatic elements.
        
        Args:
            character_responses: Dict mapping character names to their responses
            current_state: Current story state
            
        Returns:
            Dict containing dramatic analysis
        """
        # Format responses for analysis
        responses_text = "\n".join(
            f"{char}: {response}"
            for char, response in character_responses.items()
        )
        
        try:
            # Generate dramatic analysis
            analysis = self.drama_analysis_chain.invoke({
                "responses": responses_text,
                "current_state": current_state
            })
            return analysis
            
        except Exception as e:
            print(f"Error analyzing dramatic elements: {str(e)}")
            return {
                "analysis": {
                    "conflicts": ["Unresolved tension"],
                    "emotions": {"default": "uncertain"},
                    "plot_opportunities": ["Continue current arc"],
                    "themes": ["Mystery"]
                }
            }
    
    def enhance_response(
        self,
        response: str,
        character: str,
        analysis: Dict[str, Any]
    ) -> str:
        """Enhance a character response with dramatic elements.
        
        Args:
            response: Original character response
            character: Name of the character
            analysis: Dramatic analysis to incorporate
            
        Returns:
            Enhanced response with more dramatic elements
        """
        try:
            enhanced = self.llm.invoke(
                self.drama_enhancement_template.format(
                    response=response,
                    character=character,
                    analysis=str(analysis)
                )
            )
            return enhanced.strip()
            
        except Exception as e:
            print(f"Error enhancing response: {str(e)}")
            return response
    
    def generate_dramatic_story(
        self,
        character_responses: Dict[str, str],
        current_state: str,
        narrative_engine: Any = None
    ) -> Dict[str, Any]:
        """Generate dramatic story developments from character responses.
        
        Args:
            character_responses: Dict mapping character names to their responses
            current_state: Current story state
            narrative_engine: Optional NarrativeEngine instance to use
            
        Returns:
            Dict containing story developments with enhanced drama
        """
        # First analyze dramatic elements
        analysis = self.analyze_dramatic_elements(
            character_responses,
            current_state
        )
        
        # Enhance each character response
        enhanced_responses = {
            char: self.enhance_response(response, char, analysis)
            for char, response in character_responses.items()
        }
        
        # Generate story developments if narrative engine provided
        if narrative_engine:
            developments = narrative_engine.generate_developments(
                story_state=current_state,
                character_actions=str(enhanced_responses),
                theme=", ".join(analysis["analysis"]["themes"])
            )
        else:
            developments = None
            
        return {
            "analysis": analysis,
            "enhanced_responses": enhanced_responses,
            "developments": developments
        }
    
    def generate_dramatic_dialogue(
        self,
        characters: List[str],
        topic: str,
        context: str,
        num_exchanges: int = 3
    ) -> List[Dict[str, str]]:
        """Generate dialogue with narrative-aware dramatic enhancements"""
        """Generate dramatic dialogue between characters.
        
        Args:
            characters: List of character names
            topic: Topic of conversation
            context: Current context/situation
            num_exchanges: Number of dialogue exchanges to generate
            
        Returns:
            List of dialogue exchanges
        """
        dialogue_template = PromptTemplate(
            input_variables=["characters", "topic", "context", "previous"],
            template="""
            Generate the next line of dramatic dialogue:
            
            Characters: {characters}
            Topic: {topic}
            Context: {context}
            
            Previous exchanges:
            {previous}
            
            Generate next line as: "Character: Dialogue"
            Make it dramatic and emotionally charged.
            """
        )
        
        dialogue = []
        previous = "Start of conversation"
        
        try:
            for _ in range(num_exchanges * len(characters)):
                # Generate next line
                next_line = self.llm.invoke(
                    dialogue_template.format(
                        characters=", ".join(characters),
                        topic=topic,
                        context=context,
                        previous=previous
                    )
                )
                
                # Parse character and line
                char, text = next_line.split(":", 1)
                dialogue.append({
                    "character": char.strip(),
                    "line": text.strip()
                })
                
                # Update previous for context
                previous = "\n".join(
                    f"{d['character']}: {d['line']}"
                    for d in dialogue[-3:]  # Keep last 3 exchanges for context
                )
                
            return dialogue
            
        except Exception as e:
            print(f"Error generating dialogue: {str(e)}")
            return [{
                "character": characters[0],
                "line": "We should discuss this further..."
            }]