import json
import logging
from typing import Any
import paho.mqtt.client as mqtt
import socket
import threading

logger = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self, config: dict[str, str]):
        self.broker: str = config["broker"]
        self._connected_event: threading.Event = threading.Event()
        self.port: int = int(config.get("port", 1883))
        self.topic_prefix: str = config.get("topic_prefix", "ht2000")
        self.client_id: str = f"ht2000-{socket.gethostname()}"
        self.username: str | None = config.get("username")
        self.password: str | None = config.get("password")
        
        # type: ignore[attr-defined]
        self.client: mqtt.Client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id)
        if self.username:
            self.client.username_pw_set(self.username, self.password)
        
        self.client.on_connect = self._on_connect

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Any, rc: int, properties: Any = None) -> None:
        if rc != 0:
            raise Exception(f"Failed to connect to MQTT broker, return code {rc}")
        logger.info("Connected to MQTT broker")

    def start(self) -> None:
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def announce(self) -> None:
        payload = {
            "device": {
                "identifiers": ["ht2000"],
                "name": "HT2000 Sensor",
                "model": "HT2000",
                "manufacturer": "Slab"
            },
            "origin": {
                "name": "ht20002mqtt"
            },
            "state_topic": f"{self.topic_prefix}/state",
            "components": {
                "temperature": {
                    "platform": "sensor",
                    "device_class": "temperature",
                    "name": "Temperature",
                    "unique_id": "ht2000_temperature",
                    "unit_of_measurement": "°C",
                    "value_template": "{{ value_json.temperature }}",
                    "state_class": "measurement"
                },
                "humidity": {
                    "platform": "sensor",
                    "device_class": "humidity",
                    "name": "Humidity",
                    "unique_id": "ht2000_humidity",
                    "unit_of_measurement": "%",
                    "value_template": "{{ value_json.humidity }}",
                    "state_class": "measurement"
                },
                "co2": {
                    "platform": "sensor",
                    "device_class": "carbon_dioxide",
                    "name": "CO2",
                    "unique_id": "ht2000_co2",
                    "unit_of_measurement": "ppm",
                    "value_template": "{{ value_json.co2 }}",
                    "state_class": "measurement"
                }
            }
        }
        
        topic = f"homeassistant/device/{self.topic_prefix}/config"
        json_payload = json.dumps(payload, indent=4)
        self.client.publish(topic, json_payload, retain=True)
        logger.info(f"Announced device and components to {topic}")

    def publish_state(self, payload: dict[str, Any]) -> None:
        mqtt_payload = json.dumps(payload)
        self.client.publish(f"{self.topic_prefix}/state", mqtt_payload)

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()

