# Ninja Game

A 2D platformer built with Python and Pygame where you play as a ninja fighting through enemy-filled maps.

## Gameplay

- Navigate through 3 maps of increasing difficulty (3, 12, and 27 enemies)
- Defeat all enemies on a map by dashing into them
- Avoid enemy projectiles — one hit and you restart the level
- Wall jump and wall slide to reach difficult areas
- Progress is saved automatically when you clear a map

## Controls

| Key | Action |
|-----|--------|
| Left/Right Arrows | Move |
| Up Arrow | Jump / Double Jump / Wall Jump |
| X | Dash (kills enemies on contact, brief invulnerability) |
| Enter | Confirm (menus) |
| Escape | Return to level select |

## How to Play

### From Source

```
pip install pygame-ce
python game.py
```

### From Executable

Run `dist/game/game.exe`. The `data/` folder must be in the same directory as the executable.

## Building the Executable

```
pip install pyinstaller
pyinstaller game.spec
```

Then copy the `data/` folder into `dist/game/`.

## Project Structure

```
├── game.py                 Main game (menus, game loop, save system)
├── editor.py               Level editor
├── game.spec               PyInstaller build config
├── scripts/
│   ├── entities.py         Player, Enemy, and physics
│   ├── tilemap.py          Tile-based map system
│   ├── utils.py            Image loading and animation
│   ├── clouds.py           Parallax cloud backgrounds
│   ├── particle.py         Particle effects
│   └── spark.py            Spark/flash effects
└── data/
    ├── maps/               Level files (0.json, 1.json, 2.json)
    ├── images/             Sprites, tiles, and backgrounds
    ├── sfx/                Sound effects
    ├── music.wav           Background music
    └── save.json           Save file (created on first map clear)
```

## Game Mechanics

- **Acceleration**: Player movement ramps up and slows down smoothly rather than being instant
- **Wall Slide**: Touching a wall while airborne slows your fall
- **Wall Jump**: Jump off walls by pressing up while sliding and holding toward the wall
- **Dash**: Press X to dash in the direction you're facing. During the fast phase of the dash, you're invulnerable and kill enemies on contact
- **Double Jump**: One extra jump available while airborne

## Requirements

- Python 3.10+
- pygame-ce
    