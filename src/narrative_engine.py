from typing import Any, Dict, List
from langchain.llms import BaseLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from config import GameConfig
from drama_manager import DramaManager

class NarrativeEngine:
    """Orchestrates complex story progression with branching narratives."""
    
    def __init__(self, model: BaseLLM, config: Any, drama_manager: DramaManager):
        self.llm = model
        self.config = config
        self.drama_manager = drama_manager
        self.history = []
        self.branching_factor = 1.0  # Tracks narrative divergence
        
        # Configure templates
        self.progression_chain = self._create_progression_chain()
        self.development_chain = self._create_development_chain()

    def _create_progression_chain(self):
        template_config = self.config.templates['story_progression']
        return (
            PromptTemplate(
                input_variables=template_config['input_variables'],
                template=template_config['template']
            )
            | self.llm
            | JsonOutputParser()
        )

    def _create_development_chain(self):
        dev_config = self.config.templates['development']
        return (
            PromptTemplate(
                input_variables=dev_config['input_variables'],
                template=dev_config['template']
            )
            | self.llm
        )

    def generate_developments(self, context: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate story developments with dramatic enhancements and branching paths."""
        try:
            # Analyze dramatic potential first
            drama_analysis = self.drama_manager.analyze_dramatic_elements(
                context['character_responses'],
                context['current_state']
            )

            # Generate base developments
            developments = []
            for i in range(self.config.game_settings['max_choices']):
                response = self.development_chain.invoke({
                    "story_state": context['current_state'],
                    "character_actions": str(context['character_responses']),
                    "theme": context['theme'],
                    "number": i+1,
                    "history": self._format_history(),
                    "analysis": drama_analysis['analysis']
                })
                developments.append(self._parse_development(response, drama_analysis))
            print(f"Developments: {developments}")
            # Apply butterfly effect to future branches
            if 'choices_made' in context:
                self._update_branching_factor(context['choices_made'])
            
            return {"developments": developments}
            
        except Exception as e:
            print(f"Error generating developments: {str(e)}")
            return self.config.fallbacks['default_development']

    def _parse_development(self, response: str, analysis: Dict) -> Dict:
        """Parse LLM response into structured development with dramatic elements."""
        development = {
            "tags": [],
            "description": "Default narrative progression",
            "possible_actions": [],
            "new_situation": "Continuing story"
        }
        actions = []
        
        for line in response.strip().split('\n'):
            line = line.strip()
            if line.startswith('DESCRIPTION:'):
                development['description'] = self.drama_manager.enhance_response(
                    line[12:].strip(), 
                    "Narrator",
                    analysis
                )
            elif line.startswith('SITUATION:'):
                development['new_situation'] = line[10:].strip()
            elif line.startswith('TWIST:'):
                development['twist'] = line[6:].strip()
                development['tags'].append('plot_twist')
            elif line.startswith('ACTION'):
                actions.append({
                    "text": line.split(':', 1)[1].strip(),
                    "impact": self._calculate_action_impact()
                })

        development['possible_actions'] = actions
        return development

    def _calculate_action_impact(self) -> float:
        """Determine narrative impact based on branching history."""
        return min(1.0, 0.2 + (self.branching_factor * 0.3))

    def _update_branching_factor(self, choices: List[int]):
        """Adjust branching based on previous choice diversity."""
        unique_choices = len(set(choices[-3:]))  # Look at last 3 choices
        self.branching_factor *= 1 + (unique_choices * 0.1)

    def _format_history(self) -> str:
        """Create condensed history summary for LLM context."""
        return "\n".join(
            f"Chapter {i+1}: {event['description'][:50]}..." 
            for i, event in enumerate(self.history[-3:])
        )

    def record_development(self, development: Dict):
        """Track narrative history for continuity."""
        self.history.append({
            "description": development['description'],
            "choices": len(development['possible_actions']),
            "tags": development.get('tags', [])
        })