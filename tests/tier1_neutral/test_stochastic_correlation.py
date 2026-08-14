import numpy as np
import pytest
from retsim.simulator.stochastic import CorrelatedReturnGenerator


def test_correlated_return_generator_sampling():
    mu = np.array([0.006, 0.003])  # Monthly returns (~7.4% and ~3.7% annualized)
    cov = np.array([
        [0.0025, 0.0010],
        [0.0010, 0.0009]
    ])

    gen = CorrelatedReturnGenerator(mu, cov)
    samples = gen.sample_monthly_returns(num_months=120)

    assert samples.shape == (2, 120)
    # Check sample means approximate target means
    sample_mu = np.mean(samples, axis=1)
    assert np.allclose(sample_mu, mu, atol=0.015)


def test_non_psd_repair():
    # Construct a non-positive-definite symmetric matrix
    bad_cov = np.array([
        [1.0, 0.9, 0.9],
        [0.9, 1.0, -0.9],
        [0.9, -0.9, 1.0]
    ])
    mu = np.array([0.01, 0.01, 0.01])

    # Should not throw LinAlgError because repair_psd_matrix fixes it
    gen = CorrelatedReturnGenerator(mu, bad_cov)
    samples = gen.sample_monthly_returns(num_months=12)
    assert samples.shape == (3, 12)
