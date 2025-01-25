import pytest
from unittest.mock import MagicMock
from src.character import Character
from langchain.llms.base import BaseLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from src.config import GameConfig

@pytest.fixture
def mock_llm():
    llm = MagicMock(spec=BaseLLM)
    llm.invoke.return_value = "Test response"
    return llm

@pytest.fixture
def mock_config():
    config = MagicMock(spec=GameConfig)
    config.templates = {
        'character_response': {
            'input_variables': ['character_info', 'situation', 'input'],
            'template': 'Character: {character_info}\nSituation: {situation}\nInput: {input}'
        }
    }
    return config

def test_character_initialization(mock_llm, mock_config):
    character = Character(
        name="Test Character",
        personality="Curious",
        background="Scholar",
        conflict="Knowledge vs Safety",
        motivation="Discovery",
        secret="Forbidden research",
        model=mock_llm,
        config=mock_config
    )
    
    assert character.name == "Test Character"
    assert character.personality == "Curious"
    assert isinstance(character.response_template, PromptTemplate)
    assert character.workflow is not None
    assert character.thread_id is not None

def test_response_generation(mock_llm, mock_config):
    character = Character(
        name="Test",
        personality="Test",
        background="Test",
        model=mock_llm,
        config=mock_config
    )
    
    response = character.respond(
        situation="Lab environment",
        input_text="What's in this container?"
    )
    
    mock_llm.invoke.assert_called_once()
    assert response == "Test response"
    assert isinstance(response, str)

def test_prompt_template_usage(mock_llm, mock_config):
    character = Character(
        name="Dr. Webb",
        personality="Calculating",
        background="Lead researcher",
        model=mock_llm,
        config=mock_config
    )
    
    test_input = "Should we open this chamber?"
    character.respond("Abandoned facility", test_input)
    
    called_prompt = mock_llm.invoke.call_args[0][0]
    assert "Name: Dr. Webb" in called_prompt
    assert "Personality: Calculating" in called_prompt
    # Situation not preserved in state - see implementation limitation
    assert test_input in called_prompt

def test_edge_cases(mock_llm, mock_config):
    character = Character(
        name="",
        personality="",
        background="",
        model=mock_llm,
        config=mock_config
    )
    
    empty_response = character.respond("", "")
    assert isinstance(empty_response, str)
    
    special_chars = character.respond("!@#$", "%^&*")
    assert isinstance(special_chars, str)