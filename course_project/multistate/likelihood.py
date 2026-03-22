import torch
import numpy as np
import pandas as pd

from torchdiffeq import odeint


def log_likelihood_constantQ(model, data, rates, method="dopri5"):
    """
    calculate log-likelihood using ODE-derived transition probabilities (constant Q)
    """
    Q = model.generator_matrix(rates)
    t0s, dts, state_froms, state_tos = build_intervals(data)
    ll = torch.tensor(0.0, dtype=rates.dtype)
    for dt in np.unique(dts):
        if dt == 0.0:   # P(0) = I, contributes 0 to log-likelihood
            continue
        mask = dts == dt
        P = transition_probs_constantQ(Q, dt, method=method)
        state_from = torch.tensor(state_froms[mask], dtype=torch.long)
        state_to = torch.tensor(state_tos[mask], dtype=torch.long)
        ll = ll + torch.log(torch.clamp(P[state_from, state_to], min=1e-38)).sum()
    return ll


def log_likelihood_time_varyingQ(model, data, Q_fn, dtype, method="dopri5"):
    """
    calculate log-likelihood using ODE-derived transition probabilities (time-varying Q)
    """
    t0s, dts, state_froms, state_tos = build_intervals(data)
    ll = torch.tensor(0.0, dtype=dtype)
    unique_intervals = np.unique(np.stack([t0s, dts], axis=1), axis=0)

    for t0, dt in unique_intervals:
        if dt == 0.0:   # P(0) = I, contributes 0 to log-likelihood
            continue
        mask = (t0s == t0) & (dts == dt)
        P = transition_probs_time_varyingQ(Q_fn, float(t0), float(dt), model.n_states, dtype, method=method)
        state_from = torch.tensor(state_froms[mask], dtype=torch.long)
        state_to = torch.tensor(state_tos[mask], dtype=torch.long)
        ll = ll + torch.log(torch.clamp(P[state_from, state_to], min=1e-38)).sum()
    return ll


def build_intervals(data, id_col="id", time_col="obs_time", state_col="state"):
    """
    build flat interval arrays (t0s, dts, state_froms, state_tos) from panel data
        where t0s are the interval start times
    """
    data_sorted = data.sort_values([id_col, time_col])
    t0s = []
    dts = []
    state_froms = []
    state_tos = []
    for _, group in data_sorted.groupby(id_col, sort=False):
        times = group[time_col].values
        states = group[state_col].values
        for i in range(len(times)-1):
            t0s.append(times[i])
            dts.append(times[i+1]-times[i])
            state_froms.append(states[i])
            state_tos.append(states[i+1])
    return np.array(t0s), np.array(dts), np.array(state_froms), np.array(state_tos)


def transition_probs_constantQ(Q, dt, method="dopri5"):
    """
    Solve the Kolmogorov forward ODE
    dP/dt = P @ Q, P(0) = I

    This is equivalent to P(dt) = expm(Q * dt) for time-homogeneous Q
    """
    n = Q.shape[0]
    P0 = torch.eye(n, dtype=Q.dtype)
    t_span = torch.tensor([0.0, dt], dtype=Q.dtype)
    sol = odeint(lambda t, P: P @ Q, P0, t_span, method=method)
    return sol[-1]


def transition_probs_time_varyingQ(Q_fn, t0, dt, n_states, dtype, method="dopri5"):
    """
    Solve the Kolmogorov forward ODE for P(t0, t0+dt)
    dp/dt = P @ Q(t0+dt), P(0) = I
    """
    P0 = torch.eye(n_states, dtype=dtype)
    t_span = torch.tensor([0.0, dt], dtype=torch.float64)  # float64 prevents step-size underflow
    sol = odeint(lambda t, P: P @ (Q_fn(float(t0) + float(t))), P0, t_span, method=method)
    return sol[-1]