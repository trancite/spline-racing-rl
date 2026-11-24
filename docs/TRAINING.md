# Training and using bots

[Back to the README](../README.md)

Training uses Stable-Baselines3 PPO with a Gymnasium environment. It does not open a game window, although the current imports also require Tkinter to be installed. Menu option `5` only runs inference with a saved policy.

## First session

Install the requirements and activate the environment as described in the [README](../README.md#quick-start). From the project root, you can start a small session with one environment:

```bash
python -c "from training import start_training; start_training(car_name='default_ai', circuit_names=['ovalo'], output_model_name='ppo_ovalo_demo', n_envs=1, n_stack=4, total_timesteps=100_000)"
```

This example uses existing data, keeps frame stacking compatible with the game, and saves under a different name from the bundled checkpoint. A short session lets you try the training process; learning to complete the track takes more experimentation.

When training finishes, it writes two files:

```text
training/models/ppo_ovalo_demo.zip
training/models/ppo_ovalo_demo.json
```

Pressing `Ctrl+C` during learning attempts to save with the `_interrupted` suffix. Names are reused: another session with the same name can overwrite its results.

## Configure a session

To customize parameters or use multiple processes, save a `train_local.py` file in the project root. Keep the `if __name__ == "__main__"` guard for process startup:

```python
from training import Trainer, TrainingConfig

if __name__ == "__main__":
    config = TrainingConfig(
        car_name="default_ai",
        circuit_names=["ovalo", "nascar_02"],
        output_model_name="ppo_my_experiment",
        n_envs=2,
        n_stack=4,
        total_timesteps=200_000,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=128,
        device="cpu",
        circuit_max_steps={"ovalo": 12000, "nascar_02": 14000},
    )
    Trainer(config).start()
```

Run it with `python train_local.py`. Adjust the number of environments to the resources available. PPO collects batches of steps, so the final number of interactions can exceed the requested target.

| Parameter | Effect |
| --- | --- |
| `car_name` | Name of a car JSON file, without its extension. |
| `circuit_names` | Names of circuit JSON files, without their extensions. |
| `output_model_name` | Output name for the ZIP and its JSON file. |
| `n_envs` | Number of environments; uses `SubprocVecEnv` when greater than one. |
| `n_stack` | Consecutive observations stacked together. Keep `4` for the examples and the current game loader. |
| `total_timesteps` | Target number of learning interactions. |
| `learning_rate`, `n_steps`, `batch_size` | Parameters the trainer passes to PPO when starting. |
| `device` | Device requested from Stable-Baselines3; CPU by default. |
| `circuit_max_steps` | Episode duration limits by circuit name. |

**The default names `simple_car` and `triangle` have no corresponding files in this copy of the project.** Always specify an existing car and circuits.

Also, `TrainingConfig` declares `gamma`, `ent_coef`, and `gae_lambda`, but the code for starting a new training session does not pass them to PPO. Changing them in that configuration is not enough to change learning. The JSON files do not accurately record all effective parameters either; see the [reproducibility limitations](#reproducibility-limitations).

## Available data

| Type | Directory | Bundled names |
| --- | --- | --- |
| Cars | `training/training_data/cars_for_training/` | `default_ai`, `simple_fast_car`, `simple_fast_turn_car` |
| Circuits | `training/training_data/circuits_for_training/` | `straight_line_01`, `nascar_02`, `sand_clock_03`, `dinosaur_04`, `hard_random_circuit`, `infinity`, `ovalo` |

You can list these names from Python:

```bash
python -c "from training import list_available_cars, list_available_circuits; print(list_available_cars()); print(list_available_circuits())"
```

Car files use the `{"cars": [...]}` container; the trainer takes the first car. Circuits contain `roads`, with their points and attributes. The format is described in [Architecture](ARCHITECTURE.md).

To train on a circuit from the editor, save a valid track and copy its JSON file into the training circuits directory. Then use its name without the extension in `circuit_names`. Campaign and training tracks live in separate directories: editing one does not update the other.

## Full session from the original script

```bash
python training/training_code/train.py
```

This command starts training immediately, without a configuration screen:

- Car `default_ai` and all seven training circuits.
- Target of 8,000,000 steps, 10 environments, 4 stacked observations, and CPU.
- Output name `ppo_all_circuits_default_ai`.
- Step limit per circuit calculated as `int(approx_length * 10)` using the first road in each JSON file.

There are no command-line arguments or `--help` option: adding it does not display help and can still start the session. If you interrupt this training session, its output name matches the bundled `_interrupted` checkpoint and can overwrite it. Use your own name for your sessions, as in the examples above.

## Resume training

To resume the model from the first example:

```bash
python -c "from training import resume_training; resume_training(car_name='default_ai', circuit_name='ovalo', model_zip_name='ppo_ovalo_demo', extra_timesteps=100_000)"
```

If you interrupted it, change the name to `ppo_ovalo_demo_interrupted`. This API looks for the ZIP in `training/models/`, restores `n_stack` from the JSON, and requires you to specify the car and circuits again. The result uses the `_resumed` suffix, or `_resumed_interrupted` if stopped during learning.

The resume helper defaults to ten environments and applies `n_steps=1024`, `batch_size=256`, and `ent_coef=0.05`, which differ from the first session. Check those parameters if you want to preserve the original training settings.

To control resource use, create a `Trainer(TrainingConfig(...))` as in the earlier example and call `trainer.resume("ppo_ovalo_demo", extra_timesteps=100_000)` instead of `start()`. Also check `ent_coef`, which this code does pass to PPO.

## Using a model in the game

1. Keep the `.zip` and `.json` files with the same base name in `training/models/`. The game loader also searches `training/done_models/`.
2. Change the `AI_BOT` constant in [`game/modes.py`](../game/modes.py) to the ZIP filename, for example `ppo_ovalo_demo.zip`.
3. Run `python main.py` and select option `5` or `6`.

There is no model selector in the menu. The bot's car is still loaded from `default_ai.json`; the model JSON does not automatically replace that configuration or apply its global physics settings.

Keep the same observation method and frame stacking used for training. The current inference branch for `n_stack=1` has an action unpacking problem; the examples use `4`. A model trained only on `ovalo` will be tested on the game's campaign tracks and may perform worse on those circuits.

`.gitignore` keeps the distributed checkpoint and excludes new models. To deliberately share another model, add **both** files with `git add -f` after reviewing them.

## What the agent sees and does

Each observation has 13 `float32` components:

| Indices | Data |
| --- | --- |
| `0–6` | Distances from seven rays to the track edges, from −90° to 90°. |
| `7` | Normalized longitudinal velocity. |
| `8` | Normalized angular velocity. |
| `9` | Normalized lateral velocity. |
| `10` | Heading error relative to the track tangent. |
| `11` | Lateral displacement from the track center. |
| `12` | Estimated change of direction ahead of the car. |

With four stacked observations, the policy receives 52 values. The three continuous actions are steering, throttle, and brake, in `[-1, 1]`; throttle and brake are converted to `[0, 1]` before being applied.

The reward combines relative progress and longitudinal velocity, and subtracts 1 per step. Leaving the track terminates the episode with −200. Completing a lap also terminates the episode; reaching the step limit truncates it. During training on multiple circuits, weighted selection favors tracks with fewer recorded successes in each environment.

## Bundled model

[`ppo_all_circuits_default_ai_interrupted.zip`](../training/models/ppo_all_circuits_default_ai_interrupted.zip) is a PPO checkpoint with an [accompanying configuration](../training/models/ppo_all_circuits_default_ai_interrupted.json). The checkpoint stores:

| Property | Value |
| --- | --- |
| Recorded interactions (`num_timesteps`) | 5,893,900 |
| Algorithm and policy | PPO, `MlpPolicy` |
| Input / output | 52 values from stacked observations / 3 actions |
| Environments | 10 |
| `learning_rate` / `n_steps` / `batch_size` | `0.0003` / `2048` / `128` |
| Saved effective `gamma` / `ent_coef` | `0.99` / `0.0` |

The external JSON describes a target of 8,000,000 steps and values of `gamma=0.999` and `ent_coef=0.1` that do not match the ZIP. This checkpoint comes from an interrupted training run.

The checkpoint's system information identifies Python 3.9.19, Stable-Baselines3 2.5.0, PyTorch 2.6.0, NumPy 2.0.2, and Gymnasium 1.0.0 on CPU. This describes the original environment; it does not establish compatibility with other installations.

Use the pinned requirements when loading this checkpoint. With NumPy 1.26.4, loading fails because `numpy._core.numeric` is unavailable.

## Reproducibility limitations

Under NumPy 2, ordinary step rewards can be NumPy `float32` scalars rather than Python `float` values. Stable-Baselines3's `check_env` rejects that return type.

- Saving writes the requested number of steps to the JSON, even after interruption; resuming records the requested additional steps rather than the actual cumulative total.
- PPO creation and metadata serialization do not pass through all declared hyperparameters. Resuming does pass `ent_coef`, but not all other parameters are synchronized.
- Statistics are collected after the environments are closed; when using processes, they can be empty.
- Circuit selection uses the global `random` generator and is not controlled solely by `reset(seed=...)`.
- Resetting the environment does not clear all auxiliary dynamic values before the first observation.
- `training/training_code/env.py` is the implementation used by the trainer. `training/env.py` is a variant with differences, including the initial heading; they are not interchangeable without review.

When comparing experiments, record the effective parameters, versions, actual steps and evaluation results separately.
