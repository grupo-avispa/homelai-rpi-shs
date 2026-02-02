import requests
from typing import Optional, Tuple
import json
from ..config import Config, logger

class DIETClient:
    """Handles communication with NLU server."""
    
    def __init__(self, config: Config):
        self.config = config
        self.valid_entities = self._load_json(config.VALID_ENTITIES_PATH)
        self.valid_intents = self._load_json(config.VALID_INTENTS_PATH)
        self.url = config.NLU_URL
    
    def _load_json(self, filepath: str) -> dict:
        """Load JSON file."""
        try:
            with open(filepath, "r", encoding="utf8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            raise
    
    def request(self, text: str) -> dict:
        """Get intent and entity from DIET NLU model."""
        try:
            # Send request
            response = requests.post(
                self.url,
                json={"text": text},
                timeout=5
            )

            if response.status_code != 200:
                return {'error': 'Unknown error', 'status': 'error'}
            
            return response.json()
        
        except Exception as e:
            return {'error': str(e), 'status': 'error'}

    def parse(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse text to get intent and entity."""

        try:
            response = self.request(text)
            if response.get('status') != 'success':
                logger.error(f'NLU error: {response.get("error")}')
                return None, None
            result = response.get('result', {})
            intent = result.get('intent')
            if not intent:
                logger.warning("Intent not found in NLU response")
                return None, None
            
            confidence = result.get('intent_confidence', 0.0)
            
            logger.info(f"Intent: {intent}, Confidence: {confidence:.2f}")
            
            if confidence < self.config.MIN_CONFIDENCE:
                logger.warning(f"Low confidence: {confidence:.2f}")
                return None, None
            
            entities = result.get('entities', [])
            if not entities:
                logger.info("No entities found")
                return intent, None
            
            if len(entities) > 1:
                logger.info("Multiple entities found, using the first one")

            entity_dict = entities[0]
            entity = self._extract_entity(entity_dict)
            
            return intent, entity
            
        except Exception as e:
            logger.error(f"Error parsing text: {e}")
            return None, None
    
    def _extract_entity(self, entity: dict) -> Optional[str]:
        """Extract entity value and type."""

        entity_name = entity.get('type')
        entity_value = entity.get('words')
        if not entity_name or not entity_value:
            logger.warning("Incomplete entity information")
            return None
        logger.info(f"Entity: {entity_name}, Value: {entity_value}")
        return entity_value
    
    def is_valid_entity(self, entity: Optional[str], room: str) -> bool:
        """Check if entity is valid."""

        if not entity:
            return False
        return (entity in self.valid_entities.get("sala", []) or 
                entity in self.valid_entities.get("dispositivo", []))
    
    def is_room_intent(self, intent: str) -> bool:
        """Check if intent requires room information."""

        return intent in self.valid_intents.get("sala", [])