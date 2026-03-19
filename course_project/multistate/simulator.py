import torch
import numpy as np
import pandas as pd

from .model import MultistateModel


def simulate_data(
    model: MultistateModel,
    rates: torch.Tensor,
    n_subjects: int = 300,
    obs_times: np.ndarray = None,
    rng: np.random.Generator = None,
) -> pd.DataFrame:
    if rng is None:
        rng = np.random.default_rng(42)
    if obs_times is None:
        obs_times = np.array([0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0])

    Q = model.generator_matrix(rates).numpy()
    rows = []
    for sid in range(n_subjects):
        sojourns = _simulate_trajectory(
            Q, model.n_states, model.absorbing, obs_times, rng
        )
        rows.extend(_build_subject_rows(sid, sojourns, obs_times, model.absorbing))

    return pd.DataFrame(rows)


def _simulate_trajectory(Q, n_states, absorbing, obs_times, rng):
    """
    simulate individual trajectory up to obs_times[-1]

    returns a list of (from_state, to_state_or_none, entry, exit, censored)
    """
    sojourns = []
    state, t = 0, 0.0

    while state not in absorbing and t < obs_times[-1]:
        exit_rate = -Q[state, state]
        if exit_rate == 0:
            break
        sojourn_duration = rng.exponential(1 / exit_rate)
        t_exit = t + sojourn_duration

        if t_exit > obs_times[-1]:
            # administrative censoring at obs_times[-1]
            sojourns.append((state, None, t, obs_times[-1], True))
            break

        # possible transitions from current state
        candidates = [j for j in range(n_states) if j != state and Q[state, j] > 0]
        weights = np.array([Q[state, j] for j in candidates])
        weights /= weights.sum()
        next_state = rng.choice(candidates, p=weights)
        sojourns.append((state, next_state, t, t_exit, False))
        state = next_state
        t = t_exit

    return sojourns


def _state_at(sojourns, query_t):
    """
    return the state at query time t given the list of sojourns
    (from_state, to_state_or_none, entry, exit, censored)
    """
    for from_state, to_state, t_entry, t_exit, censored in sojourns:
        if t_entry <= query_t <= t_exit:
            return from_state
    if sojourns:
        last = sojourns[-1]
        return last[1] if last[1] is not None else last[0]
    return 0


def _find_absorbing_event(sojourns, absorbing):
    """
    return (exact_time, absorbing_state) if an absorbing event occurs within obs_times, else (None, None)
    """
    for from_state, to_state, t_entry, t_exit, censored in sojourns:
        if to_state is not None and to_state in absorbing:
            return t_exit, to_state
    return None, None


def _build_subject_rows(subject_id, sojourns, obs_times, absorbing):
    """
    build rows for one subject given the sojourns and obs_times

    for each scheduled observation time, record (id, obs_time, state)

    if an absorbing event occured, replace the first obs_time >= event_time
    with the exact event time and stop building rows after that
    """
    exact_time, absorbing_state = _find_absorbing_event(sojourns, absorbing)
    rows = []
    for obs_t in obs_times:
        if exact_time is not None and obs_t >= exact_time:
            rows.append(
                {"id": subject_id, "obs_time": exact_time, "state": absorbing_state}
            )
            break
        rows.append(
            {"id": subject_id, "obs_time": obs_t, "state": _state_at(sojourns, obs_t)}
        )
    return rows
