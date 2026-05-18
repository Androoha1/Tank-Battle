# Tank-Battle
### Multiplayer top-down tank battle game

## About
The goal of this project is to develop a top-down multiplayer tank battle game that allows two or more players to battle against each other in a “last man standing” setting for an infinite amount of rounds. The game is built using Python and the Pygame library.

The game places players in an enclosed area (map) where each player controls a tank and attempts to destroy all opposing tanks using projectiles, until there is one tank remaining. Once a round concludes, all participating tanks get resurrected, and a new round begins on a different map.

During the game, there is a chance for power-ups to appear, which can get collected by any tank, positively altering its attributes (such as movement speed) or projectile shot pattern for a short amount of time.

---

## Setup

### Prerequisites
- Python **3.12** or **3.13** (Python 3.14+ is not yet supported by pygame)

### 1. Clone the repository
```bash
git clone https://github.com/your-username/Tank-Battle.git
cd Tank-Battle
```

### 2. Create a virtual environment
```bash
py -3.12 -m venv .venv
```

### 3. Activate the virtual environment

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

---

## Running the game

```bash
python main.py        # 2 players (default)
python main.py 3      # 3 players
python main.py 4      # 4 players
```

---

## Controls

| Player | Move | Shoot |
|--------|------|-------|
| Player 1 | `W` `A` `S` `D` | `Left Shift` |
| Player 2 | Arrow keys | `Enter` |
| Player 3 | `I` `J` `K` `L` | `U` |
| Player 4 | Numpad `8` `4` `5` `6` | Numpad `0` |
