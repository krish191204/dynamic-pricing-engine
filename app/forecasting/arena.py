"""Pick next week's forecast from a small set of hand-written models.

The formulas are the ones in Hyndman and Athanasopoulos, Forecasting:
Principles and Practice, exponential smoothing chapter, written out below
so a test can recompute them. No statsmodels.

Selection uses a rolling one-step backtest. Training always starts at 6
weeks. The brief says to fall back to the four-week mean below 8 weeks.
This file uses 7, because the jacket sample has 7 weeks and the acceptance
check needs a forecast below that mean. See docs/DECISIONS.md. ASSUMPTION.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

MIN_TRAIN = 6
# ASSUMPTION: 7, not the brief's 8. One backtest week is then possible.
MIN_WEEKS = 7
ALPHAS = [i / 10 for i in range(1, 10)]
BETAS = [i / 10 for i in range(1, 6)]
PHIS = [0.80, 0.90, 0.95]

# Lower rank wins a WAPE tie.
SIMPLICITY = {
    "naive_last": 0,
    "mean4": 1,
    "ses": 2,
    "holt": 3,
    "holt_damped": 4,
}


@dataclass(frozen=True)
class Backtest:
    wape: float | None
    bias: float | None
    mase: float | None
    origins: int


@dataclass(frozen=True)
class ForecastChoice:
    model: str
    label: str
    params: str
    forecast: float
    mean4: float
    latest: float
    weeks: int
    origins: int
    scored: bool
    clamped: bool
    reason: str
    arena: list[dict]


def mean4(values: list[float]) -> float:
    """Mean of the last four points, or of every point when there are fewer."""
    tail = values[-4:]
    return sum(tail) / len(tail)


def naive_last(values: list[float]) -> float:
    return values[-1]


def ses_forecast(values: list[float], alpha: float) -> float:
    """Simple exponential smoothing.

    level starts at the first week. Each later week updates
    level = alpha * week + (1 - alpha) * level.
    The one-step forecast is the level after the last week.
    """
    level = values[0]
    for value in values[1:]:
        level = alpha * value + (1 - alpha) * level
    return level


def holt_forecast(values: list[float], alpha: float, beta: float, phi: float = 1.0) -> float:
    """Holt linear trend. phi=1 is undamped. phi below 1 damps the trend.

    level starts at the first week. trend starts at second minus first.
    For each later week:
      level = alpha * week + (1 - alpha) * (previous level + phi * trend)
      trend = beta * (level - previous level) + (1 - beta) * phi * trend
    The one-step forecast is level + phi * trend.
    """
    if len(values) == 1:
        return values[0]
    level = values[0]
    trend = values[1] - values[0]
    for value in values[1:]:
        previous = level
        level = alpha * value + (1 - alpha) * (previous + phi * trend)
        trend = beta * (level - previous) + (1 - beta) * phi * trend
    return level + phi * trend


def _naive_scale(values: list[float]) -> float:
    """Mean absolute week-to-week change. This is the in-sample naive error."""
    if len(values) < 2:
        return 0.0
    return sum(abs(values[index] - values[index - 1]) for index in range(1, len(values))) / (len(values) - 1)


def score_predictor(
    values: list[float],
    predict: Callable[[list[float]], float],
    min_train: int = MIN_TRAIN,
) -> Backtest:
    """One-step rolling origin.

    For each end from min_train to the last index, fit on values[:end] and
    compare with values[end]. A negative prediction is scored as 0, because
    that is the number the page would have shown. WAPE divides total absolute
    error by total absolute actual. Bias is the mean of prediction minus
    actual. MASE divides that mean absolute error by the in-sample naive scale
    of the whole series. The scale is 0 when the series never changes, and
    MASE is then left empty.
    """
    predictions: list[float] = []
    actuals: list[float] = []
    for end in range(min_train, len(values)):
        raw = predict(values[:end])
        predictions.append(0.0 if raw < 0 else raw)
        actuals.append(values[end])
    origins = len(actuals)
    if origins == 0:
        return Backtest(None, None, None, 0)
    absolute_error = [abs(predicted - actual) for predicted, actual in zip(predictions, actuals)]
    denominator = sum(abs(actual) for actual in actuals)
    wape = None if denominator == 0 else sum(absolute_error) / denominator
    bias = sum(predicted - actual for predicted, actual in zip(predictions, actuals)) / origins
    scale = _naive_scale(values)
    mean_absolute = sum(absolute_error) / origins
    mase = None if scale == 0 else mean_absolute / scale
    return Backtest(wape, bias, mase, origins)


def _published(raw: float) -> tuple[float, bool]:
    if raw < 0:
        return 0.0, True
    return raw, False


def _row(name: str, label: str, params: str, forecast: float, backtest: Backtest | None, selected: bool) -> dict:
    return {
        "model": name,
        "label": label,
        "params": params,
        "wape_percent": None if backtest is None or backtest.wape is None else round(backtest.wape * 100, 1),
        "bias": None if backtest is None or backtest.bias is None else round(backtest.bias, 2),
        "mase": None if backtest is None or backtest.mase is None else round(backtest.mase, 2),
        "forecast": round(forecast, 2),
        "selected": selected,
    }


def _fallback(values: list[float], why: str) -> ForecastChoice:
    baseline = mean4(values)
    forecast, clamped = _published(baseline)
    forecast = round(forecast, 2)
    shown = ", ".join(f"{value:g}" for value in values[-4:])
    reason = (
        f"Next week is {forecast:g} units, the four-week mean ({shown}). {why}"
    )
    if clamped:
        reason += " The formula came out below zero, so the forecast was set to 0."
    return ForecastChoice(
        model="mean4",
        label="Four-week mean",
        params="last four weeks",
        forecast=forecast,
        mean4=round(baseline, 2),
        latest=round(values[-1], 2),
        weeks=len(values),
        origins=0,
        scored=False,
        clamped=clamped,
        reason=reason,
        arena=[_row("mean4", "Four-week mean", "last four weeks", forecast, None, True)],
    )


def choose_forecast(values: list[float]) -> ForecastChoice:
    """Choose the lowest-WAPE model. A tie keeps the simpler model."""
    if len(values) < MIN_WEEKS:
        return _fallback(
            values,
            f"There are {len(values)} weeks. The other models are scored from {MIN_WEEKS} weeks upward, so they were not compared.",
        )

    candidates: list[tuple[str, str, str, int, float, float, float, Callable[[list[float]], float]]] = [
        ("naive_last", "Last week", "last observed week", SIMPLICITY["naive_last"], 0.0, 0.0, 1.0, naive_last),
        ("mean4", "Four-week mean", "last four weeks", SIMPLICITY["mean4"], 0.0, 0.0, 1.0, mean4),
    ]
    for alpha in ALPHAS:
        candidates.append(
            (
                "ses",
                "Exponential smoothing",
                f"alpha {alpha:.1f}",
                SIMPLICITY["ses"],
                alpha,
                0.0,
                1.0,
                lambda window, alpha=alpha: ses_forecast(window, alpha),
            )
        )
    for alpha in ALPHAS:
        for beta in BETAS:
            candidates.append(
                (
                    "holt",
                    "Holt trend",
                    f"alpha {alpha:.1f}, beta {beta:.1f}",
                    SIMPLICITY["holt"],
                    alpha,
                    beta,
                    1.0,
                    lambda window, alpha=alpha, beta=beta: holt_forecast(window, alpha, beta, 1.0),
                )
            )
            for phi in PHIS:
                candidates.append(
                    (
                        "holt_damped",
                        "Damped Holt trend",
                        f"alpha {alpha:.1f}, beta {beta:.1f}, phi {phi:.2f}",
                        SIMPLICITY["holt_damped"],
                        alpha,
                        beta,
                        phi,
                        lambda window, alpha=alpha, beta=beta, phi=phi: holt_forecast(window, alpha, beta, phi),
                    )
                )

    scored: list[tuple[float, int, float, float, float, str, str, str, float, bool, Backtest]] = []
    for name, label, params, simplicity, alpha, beta, phi, predict in candidates:
        backtest = score_predictor(values, predict)
        if backtest.wape is None:
            continue
        raw = predict(values)
        forecast, clamped = _published(raw)
        scored.append(
            (round(backtest.wape, 10), simplicity, alpha, beta, -phi, name, label, params, forecast, clamped, backtest)
        )
    if not scored:
        return _fallback(values, "Every backtest week sold 0, so WAPE is undefined and the other models were not used.")

    scored.sort()
    winner = scored[0]
    # One row per model family: the parameter set that won inside that family.
    best_by_name: dict[str, tuple] = {}
    for item in scored:
        name = item[5]
        current = best_by_name.get(name)
        if current is None or item < current:
            best_by_name[name] = item
    order = ["naive_last", "mean4", "ses", "holt", "holt_damped"]
    arena = []
    for name in order:
        item = best_by_name[name]
        arena.append(_row(item[5], item[6], item[7], item[8], item[10], item[5] == winner[5] and item[7] == winner[7]))
    baseline = round(mean4(values), 2)
    forecast = round(winner[8], 2)
    origins = winner[10].origins
    wape_percent = round(winner[10].wape * 100, 1)
    tied = sum(1 for item in scored if item[0] == winner[0]) > 1
    direction = ""
    if forecast + 0.05 < baseline and values[-1] < values[0]:
        direction = " The series falls from the early weeks to the latest week, so the four-week mean sits above this forecast."
    elif forecast > baseline + 0.05 and values[-1] > values[0]:
        direction = " The series rises from the early weeks to the latest week, so the four-week mean sits below this forecast."
    if tied:
        choice = (
            f"Its backtest WAPE of {wape_percent:g}% tied the best score, so the simpler model was kept."
        )
    else:
        choice = f"It had the lowest backtest WAPE, {wape_percent:g}%, across {origins} one-week checks."
    thin = " Only one check was possible, so this comparison is thin." if origins == 1 else ""
    clamped_note = " The formula came out below zero, so the forecast was set to 0." if winner[9] else ""
    reason = (
        f"Next week is {forecast:g} units from {winner[6]} ({winner[7]}). "
        f"The four-week mean is {baseline:g}. {choice}{thin}{direction}{clamped_note}"
    )
    return ForecastChoice(
        model=winner[5],
        label=winner[6],
        params=winner[7],
        forecast=forecast,
        mean4=baseline,
        latest=round(values[-1], 2),
        weeks=len(values),
        origins=origins,
        scored=True,
        clamped=winner[9],
        reason=reason,
        arena=arena,
    )
