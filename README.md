[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/cbelel/gta6-twitch-ccu-forecast-01/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/cbelel/gta6-twitch-ccu-forecast-01/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

# GTA VI Launch-Day Twitch CCU Forecast

This repository contains a robust, pure Python 3.13 program (`main.py`) designed for the make.fun bounty [Forecast GTA VI's launch-day Twitch viewers hour by hour](https://make.fun/bounty/gta6-twitch-ccu-forecast-01).

## Overview & Forecasting Method

The program forecasts launch-day concurrent viewership (CCU) for hour 2 through hour 24 on release day, anchored on the known hour-1 viewers and learned dynamics from past comparable game launches.

1. **Hour-1 Anchor**: Establishes baseline scale $p_1$ from known hour-1 viewers.
2. **Pre-Release Baseline & Ratio**: Computes pre-release hype ratios relative to pre-launch category search activity.
3. **Donor Selection**: Filters historical comparable game launches tagged with `"Tier: comparable"` whose launch ratios align closely with the target game.
4. **Shape & Spread**: Computes hourly median log-ratios and robust interquartile range (IQR) spreads across selected donors.
5. **Quantile Projections**: Generates 5 probabilistic quantiles (0.05, 0.25, 0.5, 0.75, 0.95) using normal z-scores, enforcing monotonicity and clamping.

## Design & Guarantees

- **Standard Library Only**: Implements all data processing, datetime arithmetic, and statistics natively without external dependencies.
- **Strictly Deterministic**: Sorting inputs by filename and avoiding random states or timestamp dependencies ensures byte-identical output across runs.
- **High Performance**: Executes well under the 8-second time limit per case using minimal memory.

## Local Execution

To run the program locally:

```bash
export MAKEFUN_INPUT_DIR=/path/to/input
export MAKEFUN_OUTPUT_DIR=/path/to/output
python3 main.py
```

<sub>Entered on [make.fun](https://make.fun/?ref=qaefpkbd&utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards</sub>
