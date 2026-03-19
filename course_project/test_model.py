import pytest
import torch

from multistate.model import MultistateModel


def test_multistate_model():
    # define simple model
    states = ["healthy", "illness", "death"]
    transitions = [(0, 1), (0, 2), (1, 2)]
    absorbing = [2]
    rates = torch.tensor([0.1, 0.05, 0.5])
    expected_Q = torch.tensor([[-0.15, 0.1, 0.05], [0.0, -0.5, 0.5], [0.0, 0.0, 0.0]], dtype=torch.float32)
    t = 1.0
    expected_P = torch.linalg.matrix_exp(expected_Q * t)

    model = MultistateModel(states, transitions, absorbing)

    # test properties
    assert model.n_states == len(states)
    assert model.n_transitions == len(transitions)

    # test get_state_index
    assert model.get_state_index("healthy") == 0
    assert model.get_state_index("illness") == 1
    assert model.get_state_index("death") == 2

    # test transition_index
    assert model.transition_index(0, 1) == 0
    assert model.transition_index(0, 2) == 1
    assert model.transition_index(1, 2) == 2

    # test generator_matrix
    Q = model.generator_matrix(rates)
    assert torch.allclose(Q, expected_Q)

    # test transition_probs
    P = model.transition_probs(rates, t)
    assert torch.allclose(P, expected_P)
