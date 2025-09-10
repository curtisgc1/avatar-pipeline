#!/usr/bin/env python3
"""
Home Assistant Integration for Avatar Pipeline
Provides voice control for smart home devices through Home Assistant
"""

import requests
import json
import os
from pathlib import Path

class HomeAssistantIntegration:
    def __init__(self):
        self.hass_url = os.getenv("HASS_URL", "http://homeassistant.local:8123")
        self.hass_token = os.getenv("HASS_TOKEN", "")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.hass_token}",
            "Content-Type": "application/json"
        })

    def get_states(self):
        """Get all entity states from Home Assistant"""
        try:
            response = self.session.get(f"{self.hass_url}/api/states")
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Home Assistant connection error: {e}")
            return []

    def call_service(self, domain, service, entity_id=None, **kwargs):
        """Call a Home Assistant service"""
        try:
            data = kwargs.copy()
            if entity_id:
                data["entity_id"] = entity_id

            response = self.session.post(
                f"{self.hass_url}/api/services/{domain}/{service}",
                json=data
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Service call error: {e}")
            return False

    def get_lights(self):
        """Get all light entities"""
        states = self.get_states()
        return [s for s in states if s["entity_id"].startswith("light.")]

    def control_light(self, command, entity_id=None):
        """Control lights - turn on/off/dim"""
        if not entity_id:
            # Find the first available light
            lights = self.get_lights()
            if not lights:
                return "No lights found"
            entity_id = lights[0]["entity_id"]

        if "on" in command.lower():
            success = self.call_service("light", "turn_on", entity_id)
            return f"Light {entity_id} turned on" if success else "Failed to turn on light"
        elif "off" in command.lower():
            success = self.call_service("light", "turn_off", entity_id)
            return f"Light {entity_id} turned off" if success else "Failed to turn off light"
        elif "dim" in command.lower() or "brightness" in command.lower():
            # Extract brightness level
            import re
            match = re.search(r'(\d+)', command)
            if match:
                brightness = min(int(match.group(1)), 255)
                success = self.call_service("light", "turn_on", entity_id,
                                          brightness=brightness)
                return f"Light brightness set to {brightness}" if success else "Failed to set brightness"
        return "Unknown light command"

    def get_climate(self):
        """Get climate control entities"""
        states = self.get_states()
        return [s for s in states if s["entity_id"].startswith("climate.")]

    def control_climate(self, command):
        """Control climate (HVAC)"""
        climates = self.get_climate()
        if not climates:
            return "No climate control found"

        entity_id = climates[0]["entity_id"]

        if "heat" in command.lower():
            success = self.call_service("climate", "set_hvac_mode", entity_id,
                                      hvac_mode="heat")
            return "Heating activated" if success else "Failed to activate heating"
        elif "cool" in command.lower():
            success = self.call_service("climate", "set_hvac_mode", entity_id,
                                      hvac_mode="cool")
            return "Cooling activated" if success else "Failed to activate cooling"
        elif "off" in command.lower():
            success = self.call_service("climate", "set_hvac_mode", entity_id,
                                      hvac_mode="off")
            return "Climate control turned off" if success else "Failed to turn off climate"
        return "Unknown climate command"

    def get_switches(self):
        """Get all switch entities"""
        states = self.get_states()
        return [s for s in states if s["entity_id"].startswith("switch.")]

    def control_switch(self, command, entity_id=None):
        """Control switches"""
        if not entity_id:
            switches = self.get_switches()
            if not switches:
                return "No switches found"
            entity_id = switches[0]["entity_id"]

        if "on" in command.lower():
            success = self.call_service("switch", "turn_on", entity_id)
            return f"Switch {entity_id} turned on" if success else "Failed to turn on switch"
        elif "off" in command.lower():
            success = self.call_service("switch", "turn_off", entity_id)
            return f"Switch {entity_id} turned off" if success else "Failed to turn off switch"
        return "Unknown switch command"

# Plugin interface for main pipeline
def handle_home_assistant(pipeline, user_text):
    """Handle Home Assistant commands"""
    text = user_text.lower()

    # Initialize HA integration
    ha = HomeAssistantIntegration()
    if not ha.hass_token:
        pipeline.current_text = "AI: Home Assistant not configured"
        return True

    # Light commands
    if any(word in text for word in ["light", "lights", "lamp", "lamps"]):
        result = ha.control_light(text)
        pipeline.current_text = f"AI: {result}"
        return True

    # Climate commands
    if any(word in text for word in ["heat", "cool", "temperature", "thermostat", "climate"]):
        result = ha.control_climate(text)
        pipeline.current_text = f"AI: {result}"
        return True

    # Switch commands
    if any(word in text for word in ["switch", "turn", "fan", "outlet", "device"]):
        result = ha.control_switch(text)
        pipeline.current_text = f"AI: {result}"
        return True

    return False

# Export for plugin system
commands = {
    "light": handle_home_assistant,
    "lights": handle_home_assistant,
    "heat": handle_home_assistant,
    "cool": handle_home_assistant,
    "switch": handle_home_assistant,
    "turn": handle_home_assistant
}
