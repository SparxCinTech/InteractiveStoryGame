import pytest
from unittest.mock import MagicMock, patch
from src.narrative_engine import NarrativeEngine
from langchain.llms.base import BaseLLM
from langchain_core.prompts import PromptTemplate
from src.config import GameConfig
from src.drama_manager import DramaManager

@pytest.fixture
def mock_llm():
    llm = MagicMock(spec=BaseLLM)
    llm.invoke.return_value = "Test response"
    return llm

@pytest.fixture
def mock_config():
    config = MagicMock(spec=GameConfig)
    config.templates = {
        'story_progression': {
            'input_variables': ['state', 'history'],
            'template': 'Progression template'
        },
        'development': {
            'input_variables': ['story_state', 'character_actions', 'theme', 
                              'number', 'history', 'analysis'],
            'template': 'Development template'
        }
    }
    config.game_settings = {'max_choices': 3}
    config.fallbacks = {'default_development': {'developments': []}}
    return config

@pytest.fixture
def mock_drama_manager():
    manager = MagicMock(spec=DramaManager)
    manager.analyze_dramatic_elements.return_value = {
        'analysis': 'drama_analysis',
        'enhancements': ['enhancement1', 'enhancement2']
    }
    manager.enhance_response.side_effect = lambda x, *_: f"ENHANCED: {x}"
    return manager

@pytest.fixture
def narrative_engine(mock_llm, mock_config, mock_drama_manager):
    return NarrativeEngine(
        model=mock_llm,
        config=mock_config,
        drama_manager=mock_drama_manager
    )

def test_chain_initialization(narrative_engine):
    # Verify PromptTemplate exists in chain steps
    assert any(isinstance(step, PromptTemplate) for step in narrative_engine.progression_chain.steps)
    assert any(isinstance(step, PromptTemplate) for step in narrative_engine.development_chain.steps)

def test_development_generation(narrative_engine, mock_drama_manager):
    test_context = {
        'current_state': {'scene': 'lab'},
        'character_responses': {'sarah': 'response'},
        'theme': 'scientific ethics',
        'choices_made': [1, 2, 1],
    }
    
    result = narrative_engine.generate_developments(test_context)
    
    assert len(result['developments']) == 3
    mock_drama_manager.analyze_dramatic_elements.assert_called_once_with(
        test_context['character_responses'],
        test_context['current_state']
    )
    assert narrative_engine.branching_factor > 1.0  # Verify butterfly effect

def test_development_parsing(narrative_engine):
    sample_response = """
    DESCRIPTION: A loud crash echoes
    SITUATION: Power systems failing
    TWIST: Hidden chamber revealed
    ACTION1: Investigate noise
    ACTION2: Check security feeds
    """
    
    parsed = narrative_engine._parse_development(
        sample_response,
        {'analysis': 'high tension'}
    )
    
    assert "ENHANCED: A loud crash echoes" in parsed['description']
    assert parsed['new_situation'] == "Power systems failing"
    assert 'plot_twist' in parsed['tags']
    assert len(parsed['possible_actions']) == 2
    assert all(0.2 <= a['impact'] <= 1.0 for a in parsed['possible_actions'])

def test_error_handling(narrative_engine, mock_llm):
    mock_llm.invoke.side_effect = Exception("Test error")
    result = narrative_engine.generate_developments({
        'current_state': {},
        'character_responses': {},
        'theme': '',
        'choices_made': []
    })
    
    assert result == {'developments': []}

def test_history_tracking(narrative_engine):
    test_development = {
        'description': 'Test event',
        'possible_actions': [{'text': 'Action 1'}, {'text': 'Action 2'}],
        'tags': ['test']
    }
    
    narrative_engine.record_development(test_development)
    assert len(narrative_engine.history) == 1
    history_entry = narrative_engine.history[0]
    assert history_entry['description'] == 'Test event'
    assert history_entry['choices'] == 2
    assert 'test' in history_entry['tags']

def test_branching_calculation(narrative_engine):
    # Initial state
    assert narrative_engine.branching_factor == 1.0
    
    # Test increasing diversity
    narrative_engine._update_branching_factor([1, 2, 3])
    assert narrative_engine.branching_factor == 1.0 * 1.3
    
    # Test repeating choices
    narrative_engine._update_branching_factor([1, 1, 1])
    assert narrative_engine.branching_factor == pytest.approx(1.43, rel=0.01)  # 1.3 * 1.1 = 1.43

def test_empty_response_parsing(narrative_engine):
    parsed = narrative_engine._parse_development("", {})
    assert parsed['description'] == "Default narrative progression"
    assert len(parsed['possible_actions']) == 0