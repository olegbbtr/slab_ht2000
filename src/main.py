from datetime import datetime
import sys
import time
import yaml
import logging
from typing import Any
from ht2000_usb import HT2000
from mqtt import MQTTClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(config_path="config.yaml"):
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config file: {e}")
        sys.exit(1)

def main():
    # Load configuration
    config = load_config()
    mqtt_config = config.get("mqtt", {})
    device_config = config.get("device", {})
    
    # MQTT Setup
    mqtt_client = MQTTClient(mqtt_config)
    mqtt_client.start()
    time.sleep(2)
    mqtt_client.announce()
    
    sensor = HT2000()
    poll_interval = int(device_config.get("poll_interval", 1))

    while True:
        result = sensor.process()
        if result:
            # Prepare payload
            payload: dict[str, Any] = result.copy() # type: ignore
            payload["timestamp"] = datetime.now().isoformat()
            
            # Publish to MQTT
            mqtt_client.publish_state(payload)

        time.sleep(poll_interval)

if __name__ == "__main__":
    main()
