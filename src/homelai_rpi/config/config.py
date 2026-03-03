from dataclasses import dataclass
import logging
from pathlib import Path
import os
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_keyword():
    """Load the wake word from the keyword.json file."""
    _package_path = Path(__file__).parent.parent.parent.parent
    keyword_path = os.path.join(_package_path, "config/keyword.json")
    try:
        with open(keyword_path, "r", encoding="utf8") as f:
            data = json.load(f)
            return data.get("keyword", "oreja")
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning(f"Failed to load keyword from {keyword_path}, using default 'oreja'")
        return "oreja"

@dataclass
class Config:
    _package_path: Path = Path(__file__).parent.parent.parent.parent
    """Configuration constants."""
    VOSK_MODEL_PATH: str = os.path.join(_package_path, "models/vosk/vosk-model-small-es-0.42")
    GRAMMARS_PATH: str = os.path.join(_package_path, "config/grammars.json")
    KEYWORD_PATH: str = os.path.join(_package_path, "config/keyword.json")
    VALID_ENTITIES_PATH: str = os.path.join(_package_path, "config/valid_entities.json")
    VALID_INTENTS_PATH: str = os.path.join(_package_path, "config/valid_intents.json")
    NLU_URL: str = "http://localhost:8000/predict"

    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_KEEPALIVE: int = 60
    MQTT_AUDIO_TOPIC: str = "esp32/audio/#"
    MQTT_ERROR_TOPIC: str = "homelai/error"
    MQTT_BASE_TOPIC: str = "homelai/intent/"
    WAKE_WORD: str = load_keyword()
    MIN_CONFIDENCE: float = 0.6
    SAMPLE_RATE: int = 16000
