"""WiFi Sensing Module - Physical Presence Detection"""
from typing import Dict
from dataclasses import dataclass
import time
import numpy as np

@dataclass
class PhysicalPresence:
    agent_id: str
    present: bool
    confidence: float
    location: str
    timestamp: int

class WiFiSensingAgent:
    def __init__(self):
        self.esp32_nodes = []
        self.csi_buffer = {}
        self.total_detections = 0
    
    def register_esp32_node(self, node_id: str, location: str):
        self.esp32_nodes.append({"id": node_id, "location": location})
    
    def collect_csi_data(self, agent_id: str) -> Dict:
        csi_data = {
            "agent_id": agent_id,
            "timestamp": int(time.time()),
            "csi_amplitude": np.random.uniform(0.5, 1.0, 64).tolist(),
            "csi_phase": np.random.uniform(-np.pi, np.pi, 64).tolist(),
            "rssi": np.random.uniform(-80, -30),
            "noise_floor": np.random.uniform(-95, -85)
        }
        if agent_id not in self.csi_buffer:
            self.csi_buffer[agent_id] = []
        self.csi_buffer[agent_id].append(csi_data)
        self.csi_buffer[agent_id] = self.csi_buffer[agent_id][-100:]
        return csi_data
    
    def detect_presence(self, agent_id: str) -> PhysicalPresence:
        csi_data = self.collect_csi_data(agent_id)
        amplitude = np.array(csi_data["csi_amplitude"])
        phase = np.array(csi_data["csi_phase"])
        amplitude_variance = np.var(amplitude)
        phase_coherence = np.mean(np.abs(np.diff(phase)))
        rssi_strength = (csi_data["rssi"] + 100) / 70        confidence = (0.4 * min(1.0, amplitude_variance * 10) + 
                     0.3 * min(1.0, phase_coherence * 5) + 
                     0.3 * rssi_strength)
        location = "room_near" if csi_data["rssi"] > -50 else "room_mid" if csi_data["rssi"] > -70 else "room_far"
        presence = PhysicalPresence(
            agent_id=agent_id,
            present=confidence > 0.6,
            confidence=confidence,
            location=location,
            timestamp=int(time.time())
        )
        self.total_detections += 1
        return presence
    
    def get_sensing_summary(self, agent_id: str) -> Dict:
        presence = self.detect_presence(agent_id)
        return {
            "agent_id": agent_id,
            "physical_presence": {
                "present": presence.present,
                "confidence": presence.confidence,
                "location": presence.location,
                "timestamp": presence.timestamp
            },
            "total_detections": self.total_detections,
            "timestamp": int(time.time())
        }

wifi_sensing = WiFiSensingAgent()
