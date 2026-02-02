# HomeLAI-RPI

Voice-controlled home automation system using Speech-to-Text (STT) and Natural Language Processing (NLP) on Raspberry Pi.

## Overview

HomeLAI-RPI is a voice recognition service that processes audio from ESP32 devices, converts speech to text using Vosk, extracts intents using DIET classifier, and publishes commands via MQTT for home automation control.

## Architecture

```
ESP32 Device → MQTT Audio → Raspberry Pi → Vosk STT → DIET NLU → MQTT Intent → Home Automation
```

### Component Flow

1. **Audio Capture**: ESP32 devices capture voice commands and publish PCM audio data via MQTT
2. **Speech Recognition**: Vosk converts audio to text (Spanish language model)
3. **Intent Recognition**: DIET classifier processes text to extract intents and entities
4. **Command Publishing**: Validated commands are published to MQTT topics for device control

## Features

- Wake word detection ("oreja")
- Real-time speech-to-text conversion
- Intent and entity extraction
- Multi-room support
- Grammar-based speech recognition
- Configurable confidence threshold
- Error handling and logging
- MQTT-based communication

## Requirements

### Hardware

- Raspberry Pi (tested on Raspberry Pi 4 - 8GB RAM)
- ESP32-S3-Korvo-2 V3
- Network connectivity (WiFi/Ethernet)

### Software

- Python 3.10
- MQTT Broker (Mosquitto)
- DIET Classifier NLU Server
- uv (Python package manager)

## Installation

### 1. Install uv

If you don't have `uv` installed, install it using:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or with pip:

```bash
pip install uv
```

### 2. Clone the Repository

```bash
git clone https://github.com/grupo-avispa/homelai-rpi.git
cd homelai-rpi
```

### 3. Install Dependencies

Using `uv`, install the project and its dependencies:

```bash
uv sync
```

This will create a virtual environment and install all required dependencies from `pyproject.toml`.

### 4. Download Vosk Model

Download the Spanish Vosk model and place it in the models directory:

```bash
cd models/vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip
unzip vosk-model-small-es-0.42.zip
cd ../..
```

### 5. Set Up DIET Classifier NLU Server

Clone and set up the DIET classifier:

```bash
cd ..
git clone https://github.com/opfernandez/diet_classifier_pytorch.git
cd diet_classifier_pytorch
uv sync
```

Train the model (if needed) or use a pre-trained model:

```bash
cd scripts
uv run ./train.py
```

Start the DIET inference server:

```bash
uv run ./inference_server.py
```

The server will listen on `localhost:5005` by default.

### 6. Configure MQTT Broker

Ensure Mosquitto or another MQTT broker is running and accessible at `homelai-pi.local:1883`.

Install Mosquitto if needed:

```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

## Configuration

### Config Files

#### `config/grammars.json`

Defines the grammar rules for speech recognition to improve accuracy.

#### `config/valid_entities.json`

Lists valid entities organized by categories:

```json
{
  "sala": ["salon", "cocina", "dormitorio", "garaje"],
  "dispositivo": ["luz", "persiana", "temperatura", "puerta"]
}
```

#### `config/valid_intents.json`

Lists valid intents organized by categories.

### Application Configuration

Edit `src/homelai_rpi/config/config.py` to modify the configuration:

```python
@dataclass
class Config:
    VOSK_MODEL_PATH: str = "models/vosk/vosk-model-small-es-0.42"
    MQTT_BROKER: str = "homelai-pi.local"
    MQTT_PORT: int = 1883
    NLU_HOST: str = "localhost"
    NLU_PORT: int = 5005
    WAKE_WORD: str = "oreja"
    MIN_CONFIDENCE: float = 0.6
    SAMPLE_RATE: int = 16000
```

## Usage

### Start the DIET Classifier Server

First, ensure the DIET classifier inference server is running:

```bash
cd ../diet_classifier_pytorch/scripts
uv run ./inference_server.py
```

### Start the HomeLAI Service

In a new terminal, start the voice recognition service:

```bash
cd homelai-rpi/scripts
uv run ./run.py
```

### MQTT Topics

#### Subscribed Topics

- `esp32/audio/<room>`: Receives PCM audio data from ESP32 devices

#### Published Topics

- `homelai/intent/<intent_name>`: Publishes recognized intents with entity/room payload
- `homelai/error`: Publishes error messages

### Voice Command Format

Commands must follow this structure:

```
<wake_word> <command>
```

Examples:
- "oreja enciende la luz del salon"
- "oreja apaga la luz del dormitorio"
- "oreja sube la persiana de la cocina"
- "oreja desbloquea el garaje"

## DIET Classifier NLU

### About DIET Classifier

This project uses [DIET Classifier PyTorch](https://github.com/opfernandez/diet_classifier_pytorch.git), a lightweight PyTorch implementation of the DIET (Dual Intent and Entity Transformer) architecture for intent classification and entity recognition.

### Training Data

Training data is located in `diet_classifier_pytorch/data/data.yml`. Add new intents and examples:

```yaml
nlu:
- intent: encender_luz
  examples: |
    - enciende la luz
    - prende la luz de [salon](sala)
    - activa la luz del [dormitorio](sala)
```

### Training the Model

To train or retrain the model:

```bash
cd diet_classifier_pytorch/scripts
uv run ./train.py
```

The trained model will be saved to `diet_classifier_pytorch/models/diet_model.pt`.

### Validation

To validate the model performance:

```bash
cd diet_classifier_pytorch/scripts
uv run ./validation.py
```

## Code Structure

### Main Application (`scripts/run.py`)

Main application file containing:

- **VoiceAssistant**: Main coordinator class that orchestrates the voice recognition pipeline
- **MQTT handling**: Subscribes to audio topics and publishes intents
- **Audio processing**: Coordinates STT and NLU processing

### Modules

#### `src/homelai_rpi/vosk/vosk_recognizer.py`

Handles speech-to-text conversion using Vosk:
- **VoskRecognizer**: Manages Vosk model and recognition
- **recognize()**: Converts PCM audio to text with grammar support

#### `src/homelai_rpi/diet/diet_client.py`

Handles communication with DIET NLU server:
- **DIETClient**: Socket-based client for DIET classifier
- **request()**: Sends text and receives intent/entity predictions
- **validate()**: Validates intents and entities against configuration

#### `src/homelai_rpi/config/config.py`

Configuration management:
- **Config**: Configuration dataclass with all system parameters
- **logger**: Centralized logging configuration

## Performance

Typical processing times on Raspberry Pi 4:

- STT (Vosk): 100-400ms
- NLU (DIET): 10-50ms
- Total: 110-450ms

## Logging

Logs include:

- Speech recognition results
- Intent and entity extraction
- Confidence scores
- Processing times
- Error messages

Log format:
```
2025-11-26 10:30:45 - __main__ - INFO - Command: enciende la luz del salon
2025-11-26 10:30:45 - __main__ - INFO - STT completed in 123.32 ms
2025-11-26 10:30:45 - __main__ - INFO - Intent: encender_luz, Confidence: 0.89
```

## Troubleshooting

### Vosk Model Not Found

Ensure the model path in `Config.VOSK_MODEL_PATH` matches the downloaded model location.

### DIET Classifier Connection Error

Verify DIET server is running:
```bash
# Check if the server is responding
nc -zv localhost 5005
```

Or check the server logs in the terminal where you started `inference_server.py`.

### Low Confidence Scores

- Add more training examples to `diet_classifier_pytorch/data/data.yml`
- Retrain the model: `cd diet_classifier_pytorch/scripts && uv run ./train.py`
- Adjust `MIN_CONFIDENCE` threshold in configuration
- Improve audio quality from ESP32 devices

### MQTT Connection Issues

Check broker status:
```bash
systemctl status mosquitto
```

Test MQTT connection:
```bash
mosquitto_sub -h homelai-pi.local -t "esp32/audio/#"
```

## Development

### Project Structure

```
homelai-rpi/
├── config/              # Configuration files
│   ├── grammars.json   # Speech recognition grammar
│   ├── valid_entities.json
│   └── valid_intents.json
├── models/
│   └── vosk/           # Vosk speech models
├── scripts/
│   └── run.py          # Main application entry point
└── src/
    └── homelai_rpi/    # Package source code
        ├── config/     # Configuration module
        ├── diet/       # DIET client module
        └── vosk/       # Vosk recognizer module
```

### Adding New Entities

1. Update training data in `diet_classifier_pytorch/data/data.yml`
2. Add entity examples to `config/grammars.json`
3. Update `config/valid_entities.json` with new entities
4. Retrain the DIET model

### Adding New Intents

1. Update training data in `diet_classifier_pytorch/data/data.yml`
2. Update `config/valid_intents.json` with new intents
3. Retrain the DIET model

## Related Projects

- [DIET Classifier PyTorch](https://github.com/opfernandez/diet_classifier_pytorch.git) - NLU model for intent and entity recognition

## License

This project is licensed under the MIT License - see the LICENSE file for details.
