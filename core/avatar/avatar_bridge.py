#!/usr/bin/env python3
"""
Bridge Component for Avatar Pipeline
Provides communication layer between different systems and services
"""

import asyncio
import json
import websockets
import redis
import requests
import threading
import time
from queue import Queue
import os

class AvatarBridge:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.message_queue = Queue()
        self.running = False

        # Bridge endpoints
        self.endpoints = {
            "stt": "http://localhost:9000",
            "llm": "http://localhost:8000",
            "tts": "http://localhost:5002",
            "home_assistant": os.getenv("HASS_URL", "http://homeassistant.local:8123")
        }

        # WebSocket connections for real-time communication
        self.websocket_connections = {}

    def start(self):
        """Start the bridge services"""
        self.running = True

        # Start Redis pub/sub listener
        threading.Thread(target=self._redis_listener, daemon=True).start()

        # Start message processor
        threading.Thread(target=self._message_processor, daemon=True).start()

        # Start WebSocket server for external connections
        threading.Thread(target=self._websocket_server, daemon=True).start()

        print("🔗 Avatar Bridge started")

    def stop(self):
        """Stop the bridge services"""
        self.running = False
        print("🔗 Avatar Bridge stopped")

    def _redis_listener(self):
        """Listen for Redis pub/sub messages"""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe('avatar_commands', 'avatar_responses', 'avatar_events')

        for message in pubsub.listen():
            if not self.running:
                break
            if message['type'] == 'message':
                self.message_queue.put({
                    'type': 'redis',
                    'channel': message['channel'],
                    'data': message['data']
                })

    def _message_processor(self):
        """Process messages from the queue"""
        while self.running:
            try:
                message = self.message_queue.get(timeout=1)
                self._handle_message(message)
            except:
                continue

    def _handle_message(self, message):
        """Handle different types of messages"""
        msg_type = message.get('type')

        if msg_type == 'redis':
            self._handle_redis_message(message)
        elif msg_type == 'websocket':
            self._handle_websocket_message(message)
        elif msg_type == 'api':
            self._handle_api_message(message)

    def _handle_redis_message(self, message):
        """Handle Redis messages"""
        channel = message.get('channel')
        data = json.loads(message.get('data', '{}'))

        if channel == 'avatar_commands':
            # Process commands and route to appropriate services
            self._route_command(data)
        elif channel == 'avatar_events':
            # Broadcast events to WebSocket clients
            self._broadcast_event(data)

    def _handle_websocket_message(self, message):
        """Handle WebSocket messages"""
        # Process messages from external clients
        pass

    def _handle_api_message(self, message):
        """Handle API messages"""
        # Process REST API calls
        pass

    def _route_command(self, command):
        """Route commands to appropriate services"""
        cmd_type = command.get('type')

        if cmd_type == 'stt':
            self._process_stt_command(command)
        elif cmd_type == 'llm':
            self._process_llm_command(command)
        elif cmd_type == 'tts':
            self._process_tts_command(command)
        elif cmd_type == 'home_assistant':
            self._process_ha_command(command)

    def _process_stt_command(self, command):
        """Process STT commands"""
        try:
            # Send to STT service
            response = requests.post(
                f"{self.endpoints['stt']}/asr",
                files={'audio_file': ('audio.wav', command.get('audio_data'))}
            )
            if response.status_code == 200:
                result = response.json()
                self.redis_client.publish('avatar_responses', json.dumps({
                    'type': 'stt_result',
                    'text': result.get('text', ''),
                    'original_command': command
                }))
        except Exception as e:
            print(f"STT processing error: {e}")

    def _process_llm_command(self, command):
        """Process LLM commands"""
        try:
            response = requests.post(
                f"{self.endpoints['llm']}/v1/chat/completions",
                json={
                    'model': 'qwen2.5-3b',
                    'messages': [{'role': 'user', 'content': command.get('text', '')}],
                    'max_tokens': 100
                }
            )
            if response.status_code == 200:
                result = response.json()
                reply = result['choices'][0]['message']['content']
                self.redis_client.publish('avatar_responses', json.dumps({
                    'type': 'llm_result',
                    'response': reply,
                    'original_command': command
                }))
        except Exception as e:
            print(f"LLM processing error: {e}")

    def _process_tts_command(self, command):
        """Process TTS commands"""
        try:
            response = requests.post(
                f"{self.endpoints['tts']}/synthesize",
                json={'text': command.get('text', '')}
            )
            if response.status_code == 200:
                result = response.json()
                self.redis_client.publish('avatar_responses', json.dumps({
                    'type': 'tts_result',
                    'audio_data': result.get('audio'),
                    'original_command': command
                }))
        except Exception as e:
            print(f"TTS processing error: {e}")

    def _process_ha_command(self, command):
        """Process Home Assistant commands"""
        try:
            # Forward to Home Assistant integration
            ha_response = requests.post(
                f"{self.endpoints['home_assistant']}/api/services",
                headers={'Authorization': f"Bearer {os.getenv('HASS_TOKEN', '')}"},
                json=command.get('ha_command', {})
            )
            self.redis_client.publish('avatar_responses', json.dumps({
                'type': 'ha_result',
                'success': ha_response.status_code == 200,
                'original_command': command
            }))
        except Exception as e:
            print(f"Home Assistant processing error: {e}")

    def _broadcast_event(self, event):
        """Broadcast events to WebSocket clients"""
        # Send events to connected WebSocket clients
        pass

    async def _websocket_handler(self, websocket):
        """Handle WebSocket connections"""
        client_id = id(websocket)
        self.websocket_connections[client_id] = websocket

        try:
            async for message in websocket:
                data = json.loads(message)
                self.message_queue.put({
                    'type': 'websocket',
                    'client_id': client_id,
                    'data': data
                })
        except:
            pass
        finally:
            del self.websocket_connections[client_id]

    def _websocket_server(self):
        """Start WebSocket server"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            start_server = websockets.serve(
                self._websocket_handler,
                "localhost",
                8765
            )

            loop.run_until_complete(start_server)
            loop.run_forever()
        except Exception as e:
            print(f"WebSocket server error: {e}")

    def send_command(self, command_type, **kwargs):
        """Send command through the bridge"""
        command = {'type': command_type, **kwargs}
        self.redis_client.publish('avatar_commands', json.dumps(command))

    def get_status(self):
        """Get bridge status"""
        return {
            'running': self.running,
            'redis_connected': self.redis_client.ping(),
            'endpoints': self.endpoints,
            'websocket_clients': len(self.websocket_connections)
        }

# Global bridge instance
bridge = AvatarBridge()

def start_bridge():
    """Start the bridge service"""
    bridge.start()

def stop_bridge():
    """Stop the bridge service"""
    bridge.stop()

if __name__ == "__main__":
    # Run bridge standalone for testing
    bridge.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        bridge.stop()
