# Bayesian Multistate Model for Time-to-Event Data Analysis

This project will implement Bayesian multistate models to estimate the transition rates among different disease states (e.g. healthy, illness, death).

Main example - illness-death model
- states: healthy, illness, death
- transitions: healthy -> illness with q01=0.30, healthy -> death with q02=0.10, illness -> death with q12=0.50
- absorbing state: death
- data are simulated via this model

Main dependencies: torch, pyro, arviz, numpy, pandas, matplotlib, scipy
