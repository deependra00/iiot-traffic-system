import json
import paho.mqtt.client as mqtt

class IIoTPublisher:
    def __init__(self, broker="broker.emqx.io", port=1883, topic="iiot/traffic/junction_01"):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ITS_Edge_Gateway")
        
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            print(f"Connected to MQTT Broker: {self.broker}")
        except Exception as e:
            print(f"MQTT Connection Failed: {e}")

    def publish_telemetry(self, analytics_data):
        try:
            payload = {
                "device_id": "Edge_Camera_Node_01",
                "junction": "Main Highway Crossing",
                "metrics": analytics_data
            }
            message = json.dumps(payload)
            self.client.publish(self.topic, message)
        except Exception as e:
            print(f"Publish Error: {e}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()