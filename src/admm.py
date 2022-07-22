from dataclasses import dataclass, field

import numpy as np
import numpy.linalg as la

from src.proximal_operators import proximal_update_admm


@dataclass
class CPDADMM:
    """
    Solves ADMM sub-problem for a given mode.
    This class stores the initial and current (final) states of the factor
      matrices and the dual variables for each ADMM sub-problem.
    """

    # fixed for each object
    tensor_mode: int
    constraint: str
    hyperparams: dict
    tol_error: float
    n_iters: int = -1

    # initial state of updated parameters
    factor_mat_0: np.ndarray[tuple[int, int], np.float64] = field(init=False)
    dual_var_0: np.ndarray[tuple[int, int], np.float64] = field(init=False)

    # current state of updated parameters
    factor: np.ndarray[tuple[int, int], np.float64] = field(init=False)
    dual_var: np.ndarray[tuple[int, int], np.float64] = field(init=False)

    def __call__(
        self,
        tensor_unfolding: np.ndarray[tuple[int, int], np.float64],
        kr_product: np.ndarray[tuple[int, int], np.float64],
        factor: np.ndarray[tuple[int, int], np.float64],
        dual_var: np.ndarray[tuple[int, int], np.float64],
        bsum: float = 0,
    ) -> tuple[
        np.ndarray[tuple[int, int], np.float64],
        np.ndarray[tuple[int, int], np.float64],
    ]:
        """
        Solves the ADMM sub-problem for a given mode.
        """
        self.factor_mat_0 = factor
        self.dual_var_0 = dual_var

        rank = factor.shape[1]
        kr_hadamard = kr_product.T @ kr_product
        rho = np.trace(kr_hadamard) / rank
        L = kr_hadamard + (rho + bsum) * np.eye(rank)
        F = kr_product.T @ tensor_unfolding
        factor_conv = factor

        itr = 0
        while True:
            factor_t = (
                la.inv(L)
                @ (F + rho * (factor + dual_var).T + bsum * factor_conv.T)
            ).T

            factor_0 = factor
            factor = proximal_update_admm(
                factor=factor_t,
                dual_var=dual_var,
                rho=rho,
                constraint=self.constraint,
                hyperparams=self.hyperparams,
            )

            dual_var = dual_var + factor - factor_t

            prim_res = la.norm(factor - factor_t) / la.norm(factor)
            dual_res = la.norm(factor - factor_0) / la.norm(dual_var)

            itr += 1

            stop_criter1 = prim_res < self.tol_error
            stop_criter2 = dual_res < self.tol_error
            stop_criter3 = itr >= self.n_iters
            if (stop_criter1 and stop_criter2) or stop_criter3:
                break

        return factor, dual_var
