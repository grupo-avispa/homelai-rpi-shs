from vosk import Model, KaldiRecognizer
import json
import numpy as np
from ..config import Config, logger

class VoskRecognizer:
    """Handles speech-to-text using Vosk."""
    
    def __init__(self, config: Config):
        self.config = config
        self.model = self._load_model()
        self.keyword = self._load_keyword()
        self.grammar = self._load_grammar()
        self.recognizer = KaldiRecognizer(
            self.model,
            self.config.SAMPLE_RATE,
            json.dumps(self.grammar)
        )
    
    def _load_model(self) -> Model:
        """Load Vosk model."""
        try:
            return Model(self.config.VOSK_MODEL_PATH)
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            raise
    
    def _load_keyword(self) -> str:
        """Load keyword from configuration file."""
        try:
            with open(self.config.KEYWORD_PATH, "r", encoding="utf8") as f:
                keyword_data = json.load(f)
                return keyword_data.get("keyword", "oreja")
        except Exception as e:
            logger.error(f"Failed to load keyword: {e}")
            # Fallback to default keyword
            return "oreja"
    
    def _load_grammar(self) -> dict:
        """Load grammar configuration and substitute keyword."""
        try:
            with open(self.config.GRAMMARS_PATH, "r", encoding="utf8") as f:
                grammar_templates = json.load(f)
            
            # Substitute {keyword} with actual keyword in all grammar strings
            grammar = [template.replace("{keyword}", self.keyword) for template in grammar_templates]
            return grammar
        except Exception as e:
            logger.error(f"Failed to load grammar: {e}")
            raise
    
    def recognize(self, pcm_bytes: bytes) -> str:
        """Convert audio bytes to text."""
        pcm_int16 = np.frombuffer(pcm_bytes, dtype=np.int16)
        text = ""
        if self.recognizer.AcceptWaveform(pcm_int16.tobytes()):
            result = json.loads(self.recognizer.Result())
            text = result.get("text", "")
        
        final_result = json.loads(self.recognizer.FinalResult())
        final_text = final_result.get('text', "")
        if not final_text:
            final_text = text
        
        return final_text.strip() if final_text else ""