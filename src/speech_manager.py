import asyncio
import hashlib
import os
from pathlib import Path
from typing import Dict, Optional, Union, Tuple
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from dataclasses import dataclass
from datetime import datetime, timedelta
import random

@dataclass
class VoiceConfig:
    """Configuration for character voices."""
    voice_id: str  # Voice ID (e.g., "af_sarah", "am_michael")
    speed: float = 1.0  # Speed multiplier
    lang: str = "en-us"  # Language

class SpeechManager:
    """Manages text-to-speech functionality for the game."""
    
    def __init__(self, 
                 cache_dir: str = "cache/audio",
                 model_path: str = "models/kokoro/kokoro-v0_19.onnx",
                 voices_path: str = "models/kokoro/voices.json"):
        """Initialize the speech manager.
        
        Args:
            cache_dir: Directory to store cached audio files
            model_path: Path to kokoro ONNX model file
            voices_path: Path to voices configuration file
        """
        # Ensure model files exist
        if not os.path.exists(model_path) or not os.path.exists(voices_path):
            raise FileNotFoundError(
                f"Required files not found. Please ensure {model_path} and "
                f"{voices_path} exist in the current directory."
            )
        
        # Initialize Kokoro TTS
        self.tts = Kokoro(model_path, voices_path)
        
        # Setup cache directory
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_expiry = timedelta(hours=24)
        
        # Default voice configurations for characters
        self.voice_configs: Dict[str, VoiceConfig] = {
            "Sarah Chen": VoiceConfig(voice_id="af_sarah"),
            "Dr. Marcus Webb": VoiceConfig(voice_id="am_michael"),
            "default": VoiceConfig(voice_id="af")
        }
        
        # Get sample rate by generating a small test audio
        _, self.sample_rate = self.tts.create("test", voice="af")
        
        # Start cache cleanup task
        asyncio.create_task(self._cleanup_cache())

    async def _cleanup_cache(self) -> None:
        """Periodically clean up expired cache files."""
        while True:
            try:
                now = datetime.now()
                for cache_file in self.cache_dir.glob("*.wav"):
                    file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if now - file_time > self.cache_expiry:
                        cache_file.unlink()
            except Exception as e:
                print(f"Error during cache cleanup: {e}")
            await asyncio.sleep(3600)

    def _get_cache_path(self, text: str, voice_config: VoiceConfig) -> Path:
        """Generate cache file path for given text and voice configuration."""
        config_str = f"{voice_config.voice_id}_{voice_config.speed}_{voice_config.lang}"
        hash_input = f"{text}_{config_str}".encode('utf-8')
        filename = hashlib.md5(hash_input).hexdigest() + ".wav"
        return self.cache_dir / filename

    def assign_voice(self, character_name: str, voice_config: VoiceConfig) -> None:
        """Assign a voice configuration to a character."""
        self.voice_configs[character_name] = voice_config

    def _create_silence(self, duration: float = 0.5) -> np.ndarray:
        """Create silence of specified duration."""
        return np.zeros(int(duration * self.sample_rate))

    async def generate_speech(
        self,
        text: str,
        character_name: Optional[str] = None,
        voice_config: Optional[VoiceConfig] = None,
        add_pause: bool = True,
        min_pause: float = 0.2,
        max_pause: float = 0.5
    ) -> Tuple[np.ndarray, int]:
        """Generate speech for given text using character's voice configuration.
        
        Args:
            text: Text to convert to speech
            character_name: Name of the character (optional)
            voice_config: Override voice configuration (optional)
            add_pause: Whether to add pause after speech
            min_pause: Minimum pause duration in seconds
            max_pause: Maximum pause duration in seconds
            
        Returns:
            Tuple of (audio samples, sample rate)
        """
        # Get voice configuration
        if voice_config is None:
            voice_config = self.voice_configs.get(
                character_name,
                self.voice_configs["default"]
            )
        
        # Check cache first
        cache_path = self._get_cache_path(text, voice_config)
        if cache_path.exists():
            audio, sample_rate = sf.read(cache_path)
        else:
            # Generate speech using Kokoro TTS
            try:
                audio, sample_rate = await asyncio.to_thread(
                    self.tts.create,
                    text,
                    voice=voice_config.voice_id,
                    speed=voice_config.speed,
                    lang=voice_config.lang
                )
                
                # Save to cache
                sf.write(cache_path, audio, sample_rate)
                
            except Exception as e:
                print(f"Error generating speech: {e}")
                raise
        
        # Add pause if requested
        if add_pause:
            pause_duration = random.uniform(min_pause, max_pause)
            pause = self._create_silence(pause_duration)
            audio = np.concatenate([audio, pause])
        
        return audio, sample_rate

    async def generate_conversation(
        self,
        sentences: list[dict[str, str]],
        output_path: str = "conversation.wav"
    ) -> None:
        """Generate a conversation from multiple sentences.
        
        Args:
            sentences: List of dicts with "voice" and "text" keys
            output_path: Path to save the output audio file
        """
        audio_parts = []
        sample_rate = None
        
        for sentence in sentences:
            voice_config = VoiceConfig(
                voice_id=sentence["voice"],
                speed=1.0,
                lang="en-us"
            )
            
            audio, rate = await self.generate_speech(
                sentence["text"],
                voice_config=voice_config,
                add_pause=True
            )
            
            audio_parts.append(audio)
            if sample_rate is None:
                sample_rate = rate
        
        # Combine all audio parts
        final_audio = np.concatenate(audio_parts)
        
        # Save the complete conversation
        sf.write(output_path, final_audio, sample_rate)

async def test_speech_manager():
    """Test various features of the speech manager."""
    speech_mgr = SpeechManager()
    
    try:
        # Test conversation generation
        sentences = [
            {
                "voice": "af_sarah",
                "text": "Hello! I'm Sarah Chen, and I've discovered something concerning."
            },
            {
                "voice": "am_michael",
                "text": "Dr. Webb here. Your findings are quite... interesting."
            },
            {
                "voice": "af_sarah",
                "text": "These AI experiments... they're not what they seem."
            }
        ]
        
        print("Generating conversation...")
        await speech_mgr.generate_conversation(sentences, "test_conversation.wav")
        print("Created test_conversation.wav")
        
        # Test individual speech generation
        print("\nTesting individual speech generation...")
        audio, rate = await speech_mgr.generate_speech(
            "The ethical implications are far-reaching.",
            "Sarah Chen"
        )
        sf.write("sarah_speech.wav", audio, rate)
        print("Created sarah_speech.wav")
        
        # Test custom voice
        custom_voice = VoiceConfig(
            voice_id="af_nicole",
            speed=0.9,
            lang="en-us"
        )
        
        audio, rate = await speech_mgr.generate_speech(
            "This is a test of a custom voice configuration.",
            voice_config=custom_voice
        )
        sf.write("custom_voice.wav", audio, rate)
        print("Created custom_voice.wav")
        
    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        print("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(test_speech_manager())