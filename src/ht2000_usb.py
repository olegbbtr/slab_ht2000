
import time
from typing import final
import sys
from datetime import datetime
import hid

# Constants
VID = 0x10c4
PID = 0x82cd

@final
class HT2000:
    def __init__(self):
        self._device: hid.device | None = None

    def open(self):
        self._device = hid.device()
        self._device.open(VID, PID)
        

    def read(self) -> dict[str, float | datetime]:
        if not self._device:
            raise ValueError("Device not open")
    
        # Send Feature Report: ID 0x05, data 0xff, 0xff, 0xff
        self._device.send_feature_report([0x05, 0xff, 0xff, 0xff])

        # Get Feature Report: ID 0x05
        buf = self._device.get_feature_report(0x05, 256)

        if len(buf) < 30:
            raise ValueError(f"Report 0x05 too short: {len(buf)} bytes")
        seconds = (buf[1] << 24) | (buf[2] << 16) | (buf[3] << 8) | buf[4]
        seconds -= 2004450700
        
        dt = datetime.fromtimestamp(seconds)
        
        temp_val = (buf[7] << 8) | buf[8]
        temperature = (temp_val - 400) / 10.0
        
        hum_val = (buf[9] << 8) | buf[10]
        humidity = hum_val / 10.0

        co2 = float((buf[24] << 8) | buf[25])

        if humidity == 0 or temperature == 40 or co2 == 0:
            raise ValueError("Data is invalid")

        return {
            "timestamp": dt,
            "temperature": temperature,
            "humidity": humidity,
            "co2": co2
        }
            
    def close(self):
        if not self._device:
            return
        
        self._device.close()
        self._device = None

    def process(self) -> dict[str, float | datetime]:
        while True:
            try: 
                if not self._device:
                    self.open()
                
                result = self.read()
                print(f"ts={result['timestamp']}	temp={result['temperature']:.6f}	hum={result['humidity']:.6f}	co2={result['co2']:.6f}")
                return result
            except Exception as e:
                self.close()
                print(f"Failed to open device: {e}. Waiting 30s", file=sys.stderr)
                time.sleep(30)
                continue
        




