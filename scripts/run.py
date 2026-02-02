"""
Voice recognition service using Vosk STT and DIET NLU via MQTT.
Processes audio from ESP32 devices and publishes intents.
"""

import paho.mqtt.client as mqtt
import time
from typing import Optional
from homelai_rpi.config import Config, logger
from homelai_rpi.vosk.vosk_recognizer import VoskRecognizer
from homelai_rpi.diet.diet_client import DIETClient

class VoiceAssistant:
    """Main voice assistant coordinator."""
    
    def __init__(self, config: Config):
        self.config = config
        self.vosk = VoskRecognizer(config)
        self.nlu = DIETClient(config)
        self.mqtt_client = self._setup_mqtt()
    
    def _setup_mqtt(self) -> mqtt.Client:
        """Configure MQTT client."""
        client = mqtt.Client()
        client.on_message = self._on_message
        return client
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        start_time = time.perf_counter()
        
        try:
            room = self._extract_room(msg.topic)
            text = self._process_audio(msg.payload)
            
            if not text:
                self._publish_error("No speech recognized")
                return
            
            command = self._validate_wake_word(text)
            if not command:
                return
            
            self._process_command(command, room, start_time)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self._publish_error(f"Processing error: {str(e)}")
    
    def _extract_room(self, topic: str) -> str:
        """Extract room name from MQTT topic."""
        return topic.split("/")[-1]
    
    def _process_audio(self, audio_bytes: bytes) -> str:
        """Convert audio to text."""
        start = time.perf_counter()
        text = self.vosk.recognize(audio_bytes)
        duration = (time.perf_counter() - start) * 1000
        logger.info(f"STT completed in {duration:.2f} ms")
        return text
    
    def _validate_wake_word(self, text: str) -> Optional[str]:
        """Check for wake word and extract command."""
        words = text.split()
        
        if not words or words[0] != self.config.WAKE_WORD:
            logger.info("Wake word not detected")
            self._publish_error("Wake word not detected")
            return None
        
        command = " ".join(words[1:])
        if not command:
            logger.info("No command after wake word")
            self._publish_error("No command after wake word")
            return None
        
        logger.info(f"Command: {command}")
        return command
    
    def _process_command(self, command: str, room: str, start_time: float):
        """Process voice command with NLU."""
        start = time.perf_counter()
        intent, entity = self.nlu.parse(command)
        duration = (time.perf_counter() - start) * 1000
        logger.info(f"NLU processing completed in {duration:.2f} ms")
        
        if not intent:
            self._publish_error("No intent recognized")
            return
        
        payload = self._determine_payload(intent, entity, room)
        if payload:
            topic = f"{self.config.MQTT_BASE_TOPIC}{intent}"
            self.mqtt_client.publish(topic, payload)
            logger.info(f"Published to {topic}: {payload}")
            
            total_duration = (time.perf_counter() - start_time) * 1000
            logger.info(f"Total processing time: {total_duration:.2f} ms")
    
    def _determine_payload(self, intent: str, entity: Optional[str], room: str) -> Optional[str]:
        """Determine MQTT payload based on intent and entity."""
        if entity and self.nlu.is_valid_entity(entity, room):
            return entity
        elif self.nlu.is_room_intent(intent):
            return room
        else:
            logger.warning("No valid entity found")
            self._publish_error("No valid entity found")
            return None
    
    def _publish_error(self, message: str):
        """Publish error message to MQTT."""
        self.mqtt_client.publish(self.config.MQTT_ERROR_TOPIC, message)
        logger.error(message)
    
    def start(self):
        """Start the voice assistant service."""
        logger.info("Connecting to MQTT broker...")
        self.mqtt_client.connect(
            self.config.MQTT_BROKER,
            self.config.MQTT_PORT,
            self.config.MQTT_KEEPALIVE
        )
        
        self.mqtt_client.subscribe(self.config.MQTT_AUDIO_TOPIC)
        logger.info(f"Subscribed to {self.config.MQTT_AUDIO_TOPIC}")
        logger.info("Waiting for ESP32 messages...")
        
        self.mqtt_client.loop_forever()


def main():
    """Main entry point."""
    try:
        config = Config()
        assistant = VoiceAssistant(config)
        assistant.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()