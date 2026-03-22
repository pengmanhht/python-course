import numpy as np
import pandas as pd

import torch
import pyro
import pyro.distributions as dist
from pyro.infer import SVI, Trace_ELBO
from pyro.infer.autoguide import AutoNormal

from dataclasses import dataclass, field
from typing import List, Tuple

from .likelihood import log_likelihood_constantQ, log_likelihood_time_varyingQ

@dataclass
class MultistateModel:
    """
    define the structure of a multistate model
    Attributes:
        - states: a list of state labels, e.g. ["Healthy", "Sick", "Dead"]
        - transitions: a list of tuples, [(from_state, to_state)], e.g. [(0, 1), (1, 2), (0, 2)]
        - absorbing: a list of state indices that are absorbing
    """

    states: List[str]
    transitions: List[Tuple[int, int]]
    absorbing: List[int] = field(default_factory=list)

    # validate the state indices match the number of states
    def __post_init__(self):
        n = len(self.states)
        # validate transitions
        for i, j in self.transitions:
            assert 0 <= i < n and 0 <= j < n and i != j, (
                f"invalid transition ({i}, {j}) for {n} states"
            )
        # validate absorbing states
        for s in self.absorbing:
            assert 0 <= s < n, f"invalid absorbing state index {s}"

    @property
    def n_states(self):
        return len(self.states)

    @property
    def n_transitions(self):
        return len(self.transitions)

    def generator_matrix(self, rates: torch.Tensor) -> torch.Tensor:
        """
        generate the generator matrix Q from the transition rates
        Q[i, j] = rates[k], which corresponds to self.transitions[k]
        """
        n = self.n_states
        Q = torch.zeros(n, n, dtype=rates.dtype)
        for k, (i, j) in enumerate(self.transitions):
            Q[i, j] = rates[k]
        # set diagonal entries so that rows sum to zero
        Q -= torch.diag(Q.sum(dim=1))
        return Q
    

    def simulate(self, n_subjects=300, obs_times=None, rng=None, hazard="exponential", **kwargs):
        """
        simulate panel data from the multistate model
        columns: id, obs_time, state
        """
        if hazard == "exponential":
            return simulate_exponential_transitions(self, n_subjects, obs_times, rng, **kwargs)
        elif hazard == "weibull":
            return simulate_weibull_transitions(self, n_subjects, obs_times, rng, **kwargs)
        else:
            raise ValueError(f"unsupported hazard type: {hazard}")
    

    def create_pyro_model(self, data, hazard="exponential", lr=0.01):
        """
        create a Pyro model for the multistate model
        """
        if hazard == "exponential":
            model = make_exponential_model(self, data)
        elif hazard == "weibull":
            model = make_weibull_model(self, data)
        else:
            raise ValueError(f"unsupported hazard type: {hazard}")
        
        guide = AutoNormal(model)
        svi = SVI(model, guide, optim=pyro.optim.ClippedAdam({"lr": lr}), loss=Trace_ELBO())

        return model, guide, svi
    

    def fit(self, data, hazard="exponential", lr=0.01, num_steps=3000):
        pyro.clear_param_store()
        model, guide, svi = self.create_pyro_model(data, hazard, lr)
        losses = []
        for step in range(num_steps):
            losses.append(svi.step())
            if step % 500 == 0:
                print(f"Step {step} : loss = {losses[-1]:.4f}")
        return model, guide, losses


def simulate_exponential_transitions(model, n_subjects=300, obs_times=None, rng=None, rates=None):
    if rng is None:
        rng = np.random.default_rng(42)
    if obs_times is None:
        obs_times = np.array([0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0])
    if rates is None:
        raise ValueError("rates must be provided for exponential simulation")
    
    Q = model.generator_matrix(rates)
    rows = []
    for i in range(n_subjects):
        state = 0
        rows.append({"id": i, "obs_time": obs_times[0], "state": state})
        for t in range(1, len(obs_times)):
            dt = obs_times[t] - obs_times[t - 1]
            P = torch.linalg.matrix_exp(Q * dt).numpy()
            probs = P[state]
            probs = np.clip(probs, 0, None) # ensure non-negative
            probs = probs / probs.sum()
            state = rng.choice(model.n_states, p=probs)
            rows.append({"id": i, "obs_time": obs_times[t], "state": state})
    return pd.DataFrame(rows)


def simulate_weibull_transitions(model, n_subjects=300, obs_times=None, rng=None, alpha=None, k=None):
    if rng is None:
        rng = np.random.default_rng(42)
    if obs_times is None:
        obs_times = np.array([0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0])
    if alpha is None or k is None:
        raise ValueError("alpha and k must be provided for Weibull simulation")
    
    rows = []
    for i in range(n_subjects):
        state = 0
        rows.append({"id": i, "obs_time": obs_times[0], "state": state})
        for t in range(1, len(obs_times)):
            dt = obs_times[t] - obs_times[t - 1]
            rates_t = np.exp(alpha) * k * (obs_times[t] + 1e-16)**(k - 1)
            Q_t = model.generator_matrix(torch.tensor(rates_t))
            P = torch.linalg.matrix_exp(Q_t * dt).numpy()
            probs = P[state]
            probs = np.clip(probs, 0, None)
            probs = probs / probs.sum()
            state = rng.choice(model.n_states, p=probs)
            rows.append({"id": i, "obs_time": obs_times[t], "state": state})
    return pd.DataFrame(rows)


def make_exponential_model(model, data):
    """
    create a Pyro model for the multistate model with exponential hazards
    """
    labels = [f"q_{i}{j}" for i, j in model.transitions]
    def model_fn():
        rates = torch.stack([
            pyro.sample(label, dist.Exponential(torch.tensor(1.0)))
            for label in labels
        ])
        pyro.factor("likelihood", log_likelihood_constantQ(model, data, rates))
    return model_fn


def make_weibull_model(model, data):
    """
    create a Pyro model for the multistate model with Weibull hazards
    """
    def model_fn():
        alpha = torch.stack([
            pyro.sample(f"alpha_{i}{j}",
                        dist.Normal(torch.tensor(-1.0), torch.tensor(1.0)))
            for i, j in model.transitions
        ])
        k = torch.stack([
            pyro.sample(f"k_{i}{j}",
                        dist.LogNormal(torch.tensor(0.5), torch.tensor(0.3)))
            for i, j in model.transitions
        ])

        Q_fn = weibull_Q_fn(model, alpha, k)
        ll = log_likelihood_time_varyingQ(model, data, Q_fn, dtype=alpha.dtype)
        pyro.factor("likelihood", ll)
    return model_fn


def weibull_Q_fn(model, alpha, k, eps=1e-3):
    def Q_fn(t):
        rates_t = torch.exp(alpha) * k * (t + eps)**(k - 1)
        return model.generator_matrix(rates_t)
    return Q_fn