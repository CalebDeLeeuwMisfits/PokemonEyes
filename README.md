# PokemonEyes

# Pokemon Eye Tracking Controller - Integration Guide

## Overview
This system allows you to control Pokemon gameplay using eye tracking for movement and emotion detection for button controls. The web app acts as a bridge between your eye tracking/emotion detection systems and the PyBoy Game Boy emulator.

## System Architecture
```
[Eye Tracking System] ─────┐
                           ├──> [Flask Web App] ──> [PyBoy Emulator]
[Emotion Detection] ───────┘         :5000              (Pokemon)
```

## Prerequisites
- Python 3.7+
- Pokemon Game Boy ROM file (`.gb` format)
- Your working eye tracking system
- Your working emotion detection system
- Display resolution information

## Installation

1. **Clone/Copy the project files**
   ```bash
   # Create project directory
   mkdir pokemon-eye-control
   cd pokemon-eye-control
   ```

2. **Install Python dependencies**
   ```bash
   pip install pyboy flask flask-cors
   ```

3. **Configure the ROM**
   - Place your Pokemon ROM file in the project directory
   - Rename it to `pokemon.gb` OR update the `ROM_PATH` variable in the code

4. **Update screen configuration**
   ```python
   # In app.py, update these values to match your setup:
   SCREEN_WIDTH = 1920   # Your monitor width in pixels
   SCREEN_HEIGHT = 1080  # Your monitor height in pixels
   DEAD_ZONE = 100      # Center dead zone radius (adjust for sensitivity)
   ```

## Running the Application

1. **Start the web app**
   ```bash
   python app.py
   ```

2. **Access the control interface**
   - Open browser: `http://localhost:5000`
   - You'll see the status panel and manual controls

3. **PyBoy window**
   - A separate PyBoy window will open showing the game
   - Position this where you want it on your screen

## Integration Points

### 1. Eye Tracking Integration (Movement Control)

Your eye tracking system needs to send HTTP POST requests to the `/eye_data` endpoint.

**Endpoint**: `POST http://localhost:5000/eye_data`

**Request Format**:
```json
{
    "x": 1200,  // X coordinate of eye position on screen
    "y": 600    // Y coordinate of eye position on screen
}
```

**Example Integration Code**:
```python
import requests

# In your eye tracking callback/loop:
def on_eye_position_update(x, y):
    try:
        response = requests.post(
            'http://localhost:5000/eye_data',
            json={'x': x, 'y': y},
            timeout=0.1  # 100ms timeout to prevent blocking
        )
    except:
        pass  # Handle connection errors gracefully
```

**How Movement Works**:
- Screen is divided into 5 zones: up, down, left, right, and center (dead zone)
- Looking at edges of screen moves character in that direction
- Center area stops movement
- Adjust `DEAD_ZONE` value to change center area size

### 2. Emotion Detection Integration (Button Control)

Map detected emotions to game buttons using the `/control` endpoint.

**Endpoint**: `POST http://localhost:5000/control`

**Button Press Format**:
```json
{
    "action": "button",
    "button": "a"  // Options: "a", "b", "start", "select"
}
```

**Example Emotion Mapping**:
```python
import requests

def on_emotion_detected(emotion):
    button_map = {
        'smile': 'a',        # Smile = A button (confirm/talk)
        'frown': 'b',        # Frown = B button (cancel/run)
        'surprised': 'start', # Surprised = Start (menu)
        'wink': 'select'     # Wink = Select
    }
    
    if emotion in button_map:
        requests.post(
            'http://localhost:5000/control',
            json={
                'action': 'button',
                'button': button_map[emotion]
            }
        )
```

## Testing Procedures

### 1. Initial Setup Test
- [ ] Start the app and verify PyBoy window opens
- [ ] Check web interface loads at `http://localhost:5000`
- [ ] Test manual controls work (arrow keys and buttons)

### 2. Eye Tracking Test
- [ ] Enable eye tracking via web interface toggle
- [ ] Send test coordinates to verify movement:
  ```python
  # Test script
  import requests
  import time
  
  # Test each direction
  tests = [
      (960, 100),   # Look up
      (960, 980),   # Look down
      (100, 540),   # Look left
      (1820, 540),  # Look right
      (960, 540)    # Look center (stop)
  ]
  
  for x, y in tests:
      print(f"Testing position: {x}, {y}")
      requests.post('http://localhost:5000/eye_data', json={'x': x, 'y': y})
      time.sleep(2)
  ```

### 3. Emotion Control Test
- [ ] Test each emotion triggers correct button
- [ ] Verify button presses work in game menus
- [ ] Test rapid emotion changes don't cause issues

### 4. Full Integration Test
- [ ] Start a new game using eye control + emotions
- [ ] Navigate through professor's introduction
- [ ] Walk around starting area
- [ ] Enter/exit buildings
- [ ] Interact with NPCs
- [ ] Open and navigate menus

## Monitoring & Debugging

### Status Endpoint
`GET http://localhost:5000/status`

Returns:
```json
{
    "game_running": true,
    "eye_tracking_enabled": true,
    "current_direction": "up",
    "last_update": 0.523  // seconds since last eye update
}
```

### Common Issues & Solutions

1. **Character moves too fast/slow**
   - Adjust update frequency in your eye tracking loop
   - Modify `DEAD_ZONE` size

2. **Character won't stop moving**
   - Ensure center coordinates are being sent
   - Check dead zone is large enough

3. **Buttons not responding**
   - Verify emotion detection is sending correct button names
   - Check game isn't in a state that blocks input

4. **PyBoy window not appearing**
   - Check ROM file path is correct
   - Verify PyBoy installation: `pip show pyboy`

5. **Connection errors**
   - Ensure Flask app is running
   - Check firewall isn't blocking port 5000

## Performance Optimization

1. **Update Rates**
   - Eye tracking: 10-30 Hz recommended
   - Emotion detection: 5-10 Hz sufficient
   - Don't exceed 60 Hz total updates

2. **Reduce Latency**
   - Run all components on same machine
   - Use `localhost` instead of IP addresses
   - Set short timeouts on HTTP requests

3. **Resource Usage**
   - PyBoy uses ~10-20% CPU
   - Flask minimal overhead
   - Monitor your tracking systems' CPU usage

## Advanced Configuration

### Custom Dead Zone Shape
```python
# In get_direction_from_coords(), implement custom logic:
def get_direction_from_coords(x, y):
    # Example: Elliptical dead zone
    center_x, center_y = SCREEN_WIDTH/2, SCREEN_HEIGHT/2
    dx = (x - center_x) / (SCREEN_WIDTH/2)
    dy = (y - center_y) / (SCREEN_HEIGHT/2)
    
    if dx*dx + dy*dy < 0.2:  # 20% of screen as dead zone
        return None
    # ... rest of direction logic
```

### Emotion Cooldowns
```python
# Prevent button spam
last_button_time = {}
BUTTON_COOLDOWN = 0.5  # seconds

def handle_emotion_button(button):
    current_time = time.time()
    if button in last_button_time:
        if current_time - last_button_time[button] < BUTTON_COOLDOWN:
            return  # Skip if too soon
    
    last_button_time[button] = current_time
    # Send button press...
```

## Environment Variables

Optional configuration via environment:
```bash
export POKEMON_ROM_PATH="/path/to/pokemon.gb"
export POKEMON_DEAD_ZONE=150
export POKEMON_WEB_PORT=5000
export HEADLESS=1  # Run without display (testing only)
```

## Contact & Support

For issues with:
- Eye tracking integration → Check your eye tracking SDK docs
- Emotion detection → Verify emotion labels match button mapping
- PyBoy emulator → See https://github.com/Baekalfen/PyBoy
- Flask web app → Review error logs in terminal

Good luck with the integration! The manual controls on the web interface are great for testing each component separately before combining everything.
