import torch
from dataclasses import dataclass, field
from typing import List, Tuple

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
            assert 0 <= i < n and 0 <= j < n and i != j, f"invalid transition ({i}, {j}) for {n} states"
        # validate absorbing states
        for s in self.absorbing:
            assert 0 <= s < n, f"invalid absorbing state index {s}"

    @property
    def n_states(self):
        return len(self.states)
    
    @property
    def n_transitions(self):
        return len(self.transitions)
    
    
    def get_state_index(self, state: str) -> int:
        """
        return the index of the state label in self.states
        """
        return self.states.index(state)
    

    def transition_index(self, i: int, j: int) -> int:
        """
        return the index of the transition (i,j) in self.transitions
        """
        return self.transitions.index((i, j))
    
    def generator_matrix(self, rates: torch.Tensor) -> torch.Tensor:
        """
        generate the generator matrix Q from the transition rates
        Q[i, j] = rates[k], which corresponds to self.transitions[k]
        """
        n = self.n_states
        Q = torch.zeros(n, n, dtype=torch.float32)
        for k, (i, j) in enumerate(self.transitions):
            Q[i, j] = rates[k]
        # set diagonal entries so that rows sum to zero
        Q -= torch.diag(Q.sum(dim=1))
        return Q


    def transition_probs(self, rates: torch.Tensor, t: float) -> torch.Tensor:
        """
        compute the transition probability matrix P(t) from the generator matrix Q and time t
            P(t) = expm(Q * t)
        """
        Q = self.generator_matrix(rates)
        return torch.linalg.matrix_exp(Q * t)
        pass


    def __repr__(self):
        return f"MultistateModel(states={self.states}, transitions={self.transitions}, absorbing={self.absorbing})"


if __name__ == "__main__":
    # illness-death model
    model = MultistateModel(
        states=["healthy", "illness", "death"],
        transitions=[(0, 1), (0, 2), (1, 2)],
        absorbing=[2],
    )
    print(model)
    print(model.get_state_index("illness"))
    print(model.generator_matrix(torch.tensor([0.1, 0.05, 0.2])))
    print(model.transition_probs(torch.tensor([0.1, 0.05, 0.2]), t=0.0))