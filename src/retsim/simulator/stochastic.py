import numpy as np
from scipy.linalg import cholesky


class CorrelatedReturnGenerator:
    """
    Generates correlated monthly asset returns using Cholesky decomposition of a covariance matrix.
    Includes automated Positive Semi-Definite (PSD) repair via eigenvalue clipping.
    """

    def __init__(self, expected_monthly_returns: np.ndarray, covariance_matrix: np.ndarray):
        self.mu = np.asarray(expected_monthly_returns, dtype=float)
        self.cov = np.asarray(covariance_matrix, dtype=float)

        if self.mu.ndim != 1:
            raise ValueError("expected_monthly_returns must be a 1D array.")
        if self.cov.ndim != 2 or self.cov.shape[0] != self.cov.shape[1]:
            raise ValueError("covariance_matrix must be a 2D square matrix.")
        if len(self.mu) != self.cov.shape[0]:
            raise ValueError("Dimension mismatch between returns and covariance matrix.")

        # Attempt Cholesky decomposition L L^T = Covariance
        try:
            self.L = cholesky(self.cov, lower=True)
        except np.linalg.LinAlgError:
            # Matrix is not Positive Semi-Definite (PSD); repair using eigenvalue clipping
            repaired_cov = self.repair_psd_matrix(self.cov)
            self.L = cholesky(repaired_cov, lower=True)

    @staticmethod
    def repair_psd_matrix(A: np.ndarray, min_eigenvalue: float = 1e-8) -> np.ndarray:
        """
        Projects a non-PSD symmetric matrix to the nearest PSD matrix via eigenvalue clipping.
        """
        sym_A = (A + A.T) / 2.0
        vals, vecs = np.linalg.eigh(sym_A)
        vals = np.maximum(vals, min_eigenvalue)
        repaired = vecs @ np.diag(vals) @ vecs.T
        return (repaired + repaired.T) / 2.0

    def sample_monthly_returns(self, num_months: int = 1) -> np.ndarray:
        """
        Returns (num_assets, num_months) array of correlated monthly return factors.
        """
        num_assets = len(self.mu)
        z = np.random.normal(0, 1, size=(num_assets, num_months))
        return self.mu[:, np.newaxis] + (self.L @ z)
