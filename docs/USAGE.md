# Usage guide

[Back to the README](../README.md)

## Launching the game

After setting up the environment and requirements in the [README](../README.md#quick-start), run this from the project root:

```bash
python main.py
```

Keep the terminal open: it displays game messages and is used to name tracks in the editor. The window starts at 900 × 900. Keeping that size is recommended because the interface and coordinate transformation do not fully adapt to resizing.

## Modes

Navigate the menu with `↑` / `↓` and `Enter`, or use the numbers `1` to `6`.

| Mode | What it does |
| --- | --- |
| 1 · Campaign Single Player | Drive through the four campaign tracks using the arrow keys. |
| 2 · Campaign Multiplayer | Two players on the same computer: arrow keys and WASD, with a shared camera. |
| 3 · Creating Mode | Build and save tracks using the mouse and keyboard. |
| 4 · Your Custom Circuits | Race the JSON tracks saved in `data/custom_circuits/`. Requires at least one valid track. |
| 5 · Training Mode (AI Demo) | Watch the trained bot drive through the campaign. Does not train or modify the policy. |
| 6 · Player vs AI | Race the bot using the arrow keys, with a shared camera. |

The campaign runs in this order: `straight_line_01`, `nascar_02`, `sand_clock_03` and `dinosaur_04`. When a participant finishes, the next track is scheduled to load after three seconds. After the last track, the campaign returns to the first.

There is no network multiplayer or collision handling between cars. Participants can share the same starting position.

## Driving controls

| Action | Player 1 | Player 2, local two-player mode only |
| --- | --- | --- |
| Accelerate | `↑` | `w` |
| Brake | `↓` | `s` |
| Steer left | `←` | `a` |
| Steer right | `→` | `d` |

WASD inputs are processed in lowercase. Holding the brake can eventually make the car reverse. If the controls do not respond, give the game window keyboard focus.

- `Esc`: return to the menu; this does not pause the race.
- `V`: switch between follow and overview cameras in the solo campaign, two-player campaign, custom tracks and the editor's direct test drive. Not implemented in the AI modes.
- To exit the program, close its window.

## Creating a track

1. Select option `3`.
2. Click to place track points. Click near an existing point to remove it.
3. With at least two points, use `1` to `9` to change the interpolation degree. The degree is limited by the available points; if interpolation fails, the code attempts an alternative degree.
4. Press `P` to close the track. The first point is repeated at the end to represent the closure.
5. Press `S` to save. Switch to the **terminal** and enter a simple name without an extension or folder separators, such as `my_track`. Press Enter in the terminal.
6. Return to the game, press `Esc` and select option `4`.

The `data/custom_circuits/` folder is created when you save. Leaving the name empty generates one with a timestamp. Saving with an existing name replaces that file.

Only save tracks with **at least two distinct points**. Saving without any points can produce a `null` file that cannot be played; a track with a single point is also invalid.

Pressing `Enter` in the editor starts a direct test drive, but this path does not initialize all track data, particularly closure and distances. Use option `4` to test a saved track. Save before testing: leaving the editor or starting a test clears its contents.

## Cars and physics

Configure the cars in these files:

- [`data/cars/one_player.json`](../data/cars/one_player.json): solo player and human driver in player-versus-AI mode.
- [`data/cars/two_players.json`](../data/cars/two_players.json): two local players.
- [`training/training_data/cars_for_training/default_ai.json`](../training/training_data/cars_for_training/default_ai.json): bot in the AI modes.

| Car field | Meaning |
| --- | --- |
| `id` | Display name and identifier for records. Use distinct IDs for each participant. |
| `max_speed` | Maximum speed in km/h. |
| `acceleration` | Seconds to reach 100 km/h, used in the acceleration conversion; lower values accelerate faster. |
| `turn_speed` | Angular steering speed in radians per second. |
| `grip` | Car grip, internally transformed as `g / (1 - g)`; `1` is treated specially as infinite grip. Use values between 0 and 1. |
| `controls` | `wasd` for WASD; the other current configurations use arrow keys. |
| `color`, `width`, `height` | Appearance and dimensions. |

The starting position in the JSON is replaced with the first checkpoint when races load. Global settings for friction, surface grip, the window, camera and colors are in [`core/config.py`](../core/config.py). See the [architecture and data formats](ARCHITECTURE.md) for more detail.

## Local records

Best times are written to `data/records/leaderboard.json`, indexed by track and car ID. To reset them, delete that file while the game is closed; it is created again when a result is recorded.

The on-screen leaderboard represents progress in the current race. The HUD is shared between participants and only announces and records one finish per race; it is not a complete history of every participant's results.

Records, user-created tracks and experimental models are excluded by default through `.gitignore`. To deliberately share an example track, review its JSON and add it with `git add -f data/custom_circuits/my_track.json`.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `ModuleNotFoundError` for NumPy, SciPy, Gymnasium or SB3 | Activate the environment and run `python -m pip install -r requirements.txt`. These packages are also needed to launch the game without bots. |
| Missing `_tkinter` or `python -m tkinter` fails | Install the Tk support package for your Python installation and system. |
| Display-related `TclError` | The game needs a graphical session; a remote terminal without a display is not enough. |
| The editor appears to freeze while saving | It is waiting for a name in the terminal. Enter the name there and confirm with Enter. |
| `NO CUSTOM MAPS FOUND!` | Create and save a track in option `3` first. |
| Error when opening custom tracks | Check that files are not `null`, contain `roads` and have at least two distinct points per road. Remove or fix the invalid file. |
| The bot does not move or `Model not found` appears | Check that the ZIP selected by `AI_BOT` in `game/modes.py` exists and keep its JSON alongside it. |
| Loading the bot fails with `No module named 'numpy._core.numeric'` | The included checkpoint was saved with NumPy 2. Install the pinned requirements in a separate environment and start the game with that environment's Python. |
| Dimension errors when using another model | Check the observations, frame stacking and car; follow the [training guide](TRAINING.md#using-a-model-in-the-game). |

After crossing the finish line, wait for the track to change before returning to the menu. The scheduled transition can still run if you leave during those three seconds.
