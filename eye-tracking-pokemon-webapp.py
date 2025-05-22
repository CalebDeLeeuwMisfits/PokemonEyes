import os
import json
import threading
import time
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from pyboy import PyBoy
from pyboy.utils import WindowEvent

app = Flask(__name__)
CORS(app)  # Enable CORS for eye tracking software integration

# Global variables
pyboy_instance = None
game_thread = None
current_direction = None
last_eye_update = 0
eye_tracking_enabled = False

# Configuration
ROM_PATH = "pokemon.gb"  # Path to your Pokemon ROM file
SCREEN_WIDTH = 1920  # Your monitor width
SCREEN_HEIGHT = 1080  # Your monitor height
DEAD_ZONE = 100  # Center dead zone radius in pixels

# Eye tracking zones (divide screen into regions)
def get_direction_from_coords(x, y):
    """Convert eye tracking coordinates to direction"""
    center_x = SCREEN_WIDTH / 2
    center_y = SCREEN_HEIGHT / 2
    
    # Check if in dead zone
    if abs(x - center_x) < DEAD_ZONE and abs(y - center_y) < DEAD_ZONE:
        return None
    
    # Calculate angle from center
    dx = x - center_x
    dy = y - center_y
    
    # Determine direction based on angle
    if abs(dx) > abs(dy):
        return "right" if dx > 0 else "left"
    else:
        return "down" if dy > 0 else "up"

def run_game():
    """Run the PyBoy emulator in a separate thread"""
    global pyboy_instance, current_direction, eye_tracking_enabled
    
    try:
        pyboy_instance = PyBoy(
            ROM_PATH,
            window_type="SDL2" if not os.environ.get("HEADLESS") else "headless",
            debug=False,
            game_wrapper=True
        )
        
        pyboy_instance.set_emulation_speed(1)
        
        # Main game loop
        while True:
            if eye_tracking_enabled and current_direction:
                # Press the appropriate button based on eye direction
                if current_direction == "up":
                    pyboy_instance.send_input(WindowEvent.PRESS_ARROW_UP)
                elif current_direction == "down":
                    pyboy_instance.send_input(WindowEvent.PRESS_ARROW_DOWN)
                elif current_direction == "left":
                    pyboy_instance.send_input(WindowEvent.PRESS_ARROW_LEFT)
                elif current_direction == "right":
                    pyboy_instance.send_input(WindowEvent.PRESS_ARROW_RIGHT)
                
                # Tick once to register the press
                pyboy_instance.tick()
                
                # Release the button
                if current_direction == "up":
                    pyboy_instance.send_input(WindowEvent.RELEASE_ARROW_UP)
                elif current_direction == "down":
                    pyboy_instance.send_input(WindowEvent.RELEASE_ARROW_DOWN)
                elif current_direction == "left":
                    pyboy_instance.send_input(WindowEvent.RELEASE_ARROW_LEFT)
                elif current_direction == "right":
                    pyboy_instance.send_input(WindowEvent.RELEASE_ARROW_RIGHT)
            
            # Continue game execution
            pyboy_instance.tick()
            
            # Small delay to prevent overwhelming the CPU
            time.sleep(0.016)  # ~60 FPS
            
    except Exception as e:
        print(f"Game error: {e}")
    finally:
        if pyboy_instance:
            pyboy_instance.stop()

@app.route('/')
def index():
    """Serve the control interface"""
    return render_template('index.html')

@app.route('/eye_data', methods=['POST'])
def receive_eye_data():
    """Endpoint to receive eye tracking data"""
    global current_direction, last_eye_update
    
    try:
        data = request.json
        x = data.get('x', 0)
        y = data.get('y', 0)
        
        # Update direction based on eye position
        new_direction = get_direction_from_coords(x, y)
        
        if new_direction != current_direction:
            current_direction = new_direction
            last_eye_update = time.time()
        
        return jsonify({
            'status': 'success',
            'direction': current_direction,
            'x': x,
            'y': y
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/control', methods=['POST'])
def control():
    """Manual control endpoint for testing"""
    global current_direction
    
    try:
        data = request.json
        action = data.get('action')
        
        if action == 'press':
            direction = data.get('direction')
            if direction in ['up', 'down', 'left', 'right']:
                current_direction = direction
                
        elif action == 'release':
            current_direction = None
            
        elif action == 'button':
            button = data.get('button')
            if pyboy_instance:
                if button == 'a':
                    pyboy_instance.send_input(WindowEvent.PRESS_BUTTON_A)
                    pyboy_instance.tick()
                    pyboy_instance.send_input(WindowEvent.RELEASE_BUTTON_A)
                elif button == 'b':
                    pyboy_instance.send_input(WindowEvent.PRESS_BUTTON_B)
                    pyboy_instance.tick()
                    pyboy_instance.send_input(WindowEvent.RELEASE_BUTTON_B)
                elif button == 'start':
                    pyboy_instance.send_input(WindowEvent.PRESS_BUTTON_START)
                    pyboy_instance.tick()
                    pyboy_instance.send_input(WindowEvent.RELEASE_BUTTON_START)
                elif button == 'select':
                    pyboy_instance.send_input(WindowEvent.PRESS_BUTTON_SELECT)
                    pyboy_instance.tick()
                    pyboy_instance.send_input(WindowEvent.RELEASE_BUTTON_SELECT)
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/toggle_eye_tracking', methods=['POST'])
def toggle_eye_tracking():
    """Toggle eye tracking on/off"""
    global eye_tracking_enabled
    
    eye_tracking_enabled = not eye_tracking_enabled
    return jsonify({
        'status': 'success',
        'eye_tracking_enabled': eye_tracking_enabled
    })

@app.route('/status', methods=['GET'])
def status():
    """Get current status"""
    return jsonify({
        'game_running': pyboy_instance is not None,
        'eye_tracking_enabled': eye_tracking_enabled,
        'current_direction': current_direction,
        'last_update': time.time() - last_eye_update if last_eye_update else None
    })

# Create templates directory and HTML file
if not os.path.exists('templates'):
    os.makedirs('templates')

# HTML template
html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Pokemon Eye Tracking Controller</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .status {
            background-color: #f8f8f8;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .controls {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            max-width: 300px;
            margin: 20px auto;
        }
        button {
            padding: 15px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            background-color: #4CAF50;
            color: white;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #45a049;
        }
        button:active {
            background-color: #3d8b40;
        }
        .toggle-btn {
            background-color: #2196F3;
            width: 100%;
            margin: 20px 0;
        }
        .toggle-btn.active {
            background-color: #f44336;
        }
        .eye-indicator {
            width: 200px;
            height: 200px;
            border: 2px solid #333;
            border-radius: 10px;
            margin: 20px auto;
            position: relative;
            background-color: #fafafa;
        }
        .eye-dot {
            width: 20px;
            height: 20px;
            background-color: #4CAF50;
            border-radius: 50%;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            transition: all 0.1s ease;
        }
        .info {
            text-align: center;
            color: #666;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Pokemon Eye Tracking Controller</h1>
        
        <div class="status">
            <h3>Status</h3>
            <p>Game Running: <span id="game-status">Unknown</span></p>
            <p>Eye Tracking: <span id="eye-status">Disabled</span></p>
            <p>Current Direction: <span id="direction">None</span></p>
        </div>
        
        <button class="toggle-btn" onclick="toggleEyeTracking()">
            Toggle Eye Tracking
        </button>
        
        <div class="eye-indicator">
            <div class="eye-dot" id="eye-dot"></div>
        </div>
        
        <div class="info">
            <p>Manual Controls (for testing)</p>
        </div>
        
        <div class="controls">
            <div></div>
            <button onmousedown="sendControl('press', 'up')" onmouseup="sendControl('release')">↑</button>
            <div></div>
            <button onmousedown="sendControl('press', 'left')" onmouseup="sendControl('release')">←</button>
            <button onclick="sendButton('a')">A</button>
            <button onmousedown="sendControl('press', 'right')" onmouseup="sendControl('release')">→</button>
            <div></div>
            <button onmousedown="sendControl('press', 'down')" onmouseup="sendControl('release')">↓</button>
            <button onclick="sendButton('b')">B</button>
        </div>
        
        <div style="text-align: center; margin-top: 20px;">
            <button onclick="sendButton('start')" style="margin-right: 10px;">Start</button>
            <button onclick="sendButton('select')">Select</button>
        </div>
    </div>
    
    <script>
        let eyeTrackingEnabled = false;
        
        function sendControl(action, direction = null) {
            fetch('/control', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: action, direction: direction})
            });
        }
        
        function sendButton(button) {
            fetch('/control', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'button', button: button})
            });
        }
        
        function toggleEyeTracking() {
            fetch('/toggle_eye_tracking', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    eyeTrackingEnabled = data.eye_tracking_enabled;
                    updateUI();
                });
        }
        
        function updateStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('game-status').textContent = 
                        data.game_running ? 'Running' : 'Not Running';
                    document.getElementById('eye-status').textContent = 
                        data.eye_tracking_enabled ? 'Enabled' : 'Disabled';
                    document.getElementById('direction').textContent = 
                        data.current_direction || 'None';
                    
                    eyeTrackingEnabled = data.eye_tracking_enabled;
                    updateUI();
                });
        }
        
        function updateUI() {
            const toggleBtn = document.querySelector('.toggle-btn');
            if (eyeTrackingEnabled) {
                toggleBtn.classList.add('active');
                toggleBtn.textContent = 'Disable Eye Tracking';
            } else {
                toggleBtn.classList.remove('active');
                toggleBtn.textContent = 'Enable Eye Tracking';
            }
        }
        
        // Simulate eye movement for testing
        function simulateEyeMovement(x, y) {
            const indicator = document.getElementById('eye-dot');
            const containerWidth = 200;
            const containerHeight = 200;
            
            // Map screen coordinates to indicator position
            const relX = (x / window.screen.width) * containerWidth;
            const relY = (y / window.screen.height) * containerHeight;
            
            indicator.style.left = relX + 'px';
            indicator.style.top = relY + 'px';
            
            // Send to server
            fetch('/eye_data', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({x: x, y: y})
            });
        }
        
        // Update status every second
        setInterval(updateStatus, 1000);
        updateStatus();
    </script>
</body>
</html>'''

# Write HTML template
with open('templates/index.html', 'w') as f:
    f.write(html_content)

if __name__ == '__main__':
    # Start the game in a separate thread
    game_thread = threading.Thread(target=run_game, daemon=True)
    game_thread.start()
    
    # Give the game a moment to start
    time.sleep(2)
    
    print("\n=== Pokemon Eye Tracking Controller ===")
    print(f"Make sure to place your Pokemon ROM at: {ROM_PATH}")
    print("Starting web server at http://localhost:5000")
    print("\nEye tracking endpoint: POST http://localhost:5000/eye_data")
    print("Expected JSON format: {'x': <x_coordinate>, 'y': <y_coordinate>}")
    print("\nPress Ctrl+C to stop\n")
    
    # Run the Flask app
    app.run(debug=False, host='0.0.0.0', port=5000)