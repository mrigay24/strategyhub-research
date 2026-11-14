"""Paper 3 shared library: "Hold as much entropy as you have ignorance".

Everything is plain numpy / scipy (no sklearn, cvxpy or statsmodels), so the
estimators and tests are written out here and unit-tested in ep_tests.py.

Contents
  entropy ............ effective N (Shannon exp-entropy, Renyi-2 = 1/HHI)
  covariance ......... MLE / unbiased sample covariance, Ledoit-Wolf (2004 JMVA) shrinkage
  portfolio rules .... 1/N, sample mean-variance (DGU relative weights), minimum variance,
                       Kan-Zhou (2007) three-fund, Tu-Zhou (2011) combination,
                       DGNU (2009) 2-norm constrained min-variance, long-only QP
  entropy dial ....... Gibbs / maximum-entropy tilt w_i ∝ exp(beta z_i) (closed form) and a
                       general entropy-regularised mean-variance solver by mirror descent
                       (exponentiated gradient) with a KKT check
  theory ............. Kan-Zhou K-parameter shrinkage, the IC -> beta* -> N_eff* map
  inference .......... Sharpe, CEQ, turnover; Jobson-Korkie-Memmel; Ledoit-Wolf (2008)
                       studentized circular block bootstrap; Newey-West; Hansen (2005) SPA;
                       Bailey et al. (2017) PBO by CSCV
"""
from __future__ import annotations

import itertools
import math

import numpy as np
from scipy import optimize, special, stats

SEED = 20261113

# =============================================================================
# Entropy / effective number of holdings
# =============================================================================


def neff_shannon(w) -> float:
    """exp(Shannon entropy) of a long-only weight vector (normalised to sum 1)."""
    w = np.asarray(w, float)
    w = w[w > 0]
    w = w / w.sum()
    return float(np.exp(-(w * np.log(w)).sum()))


def neff_renyi2(w) -> float:
    """1 / sum(w^2) for weights normalised to sum 1 (= exp of Renyi-2 entropy).

    Defined for long-short weights too; for sum(w)=1, sum(w^2) = ||w - 1/N||^2 + 1/N,
    so this is a monotone transform of the distance from 1/N (the DGNU 2-norm)."""
    w = np.asarray(w, float)
    w = w / w.sum()
    return float(1.0 / (w ** 2).sum())


# =============================================================================
# Covariance estimators
# =============================================================================


def cov_mle(X: np.ndarray) -> np.ndarray:
    Xc = X - X.mean(0)
    return Xc.T @ Xc / X.shape[0]


def cov_unbiased(X: np.ndarray) -> np.ndarray:
    Xc = X - X.mean(0)
    return Xc.T @ Xc / (X.shape[0] - 1)


def lw_identity(X: np.ndarray):
    """Ledoit & Wolf (2004, J. Multivariate Analysis 88) shrinkage toward m*I.

    Norm: ||A||^2 = tr(A A')/N.  S = MLE covariance of demeaned data.
      m   = tr(S)/N
      d^2 = ||S - m I||^2
      b_bar^2 = (1/T^2) sum_t ||x_t x_t' - S||^2
      b^2 = min(b_bar^2, d^2);  shrinkage s = b^2/d^2
      Sigma* = s m I + (1 - s) S
    Returns (Sigma*, s)."""
    X = np.asarray(X, float)
    T, N = X.shape
    Xc = X - X.mean(0)
    S = Xc.T @ Xc / T
    m = np.trace(S) / N
    d2 = ((S - m * np.eye(N)) ** 2).sum() / N
    xx = (Xc ** 2).sum(1)
    xSx = np.einsum("ti,ij,tj->t", Xc, S, Xc, optimize=True)
    b2bar = (xx ** 2 - 2 * xSx + (S ** 2).sum()).sum() / N / T ** 2
    b2 = min(b2bar, d2)
    s = b2 / d2 if d2 > 0 else 1.0
    return s * m * np.eye(N) + (1 - s) * S, float(s)


# =============================================================================
# Classic portfolio rules (DGU 2009 conventions: weights in risky assets)
# =============================================================================


def w_ew(N: int) -> np.ndarray:
    return np.full(N, 1.0 / N)


def w_mv(mu: np.ndarray, S: np.ndarray) -> np.ndarray:
    """Sample mean-variance (tangency) as DGU relative weights x / |1'x|."""
    x = np.linalg.solve(S, mu)
    return x / abs(x.sum())


def w_gmv(S: np.ndarray) -> np.ndarray:
    x = np.linalg.solve(S, np.ones(S.shape[0]))
    return x / x.sum()


def _ibeta_unreg(x, a, b):
    """Unregularised incomplete beta B_x(a, b)."""
    return special.betainc(a, b, x) * special.beta(a, b)


def theta2_adjusted(theta2_hat: float, N: int, T: int) -> float:
    """Kan-Zhou (2007) adjusted estimator of the squared max Sharpe ratio theta^2.

    theta2_a = ((T-N-2) th - N)/T + 2 th^(N/2) (1+th)^(-(T-2)/2) / (T B_{th/(1+th)}(N/2, (T-N)/2))
    with th the sample estimate mu' S^-1 mu (S = MLE covariance)."""
    th = max(theta2_hat, 1e-300)
    corr = 2 * th ** (N / 2) * (1 + th) ** (-(T - 2) / 2) / (
        T * _ibeta_unreg(th / (1 + th), N / 2, (T - N) / 2))
    return ((T - N - 2) * th - N) / T + corr


def psi2_adjusted(psi2_hat: float, N: int, T: int) -> float:
    """Kan-Zhou (2007) adjusted estimator of psi^2 = theta^2 - theta_g^2."""
    p = max(psi2_hat, 1e-300)
    corr = 2 * p ** ((N - 1) / 2) * (1 + p) ** (-(T - 2) / 2) / (
        T * _ibeta_unreg(p / (1 + p), (N - 1) / 2, (T - N + 1) / 2))
    return ((T - N - 1) * p - (N - 1)) / T + corr


def w_kz3(mu: np.ndarray, S_mle: np.ndarray, T: int, gamma: float = 1.0, relative=True):
    """Kan-Zhou (2007) three-fund rule (DGU 'mv-min').

    w = c3/gamma [ eta Sinv mu + (1-eta) mu_g Sinv 1 ],  c3 = (T-N-1)(T-N-4)/(T(T-2)),
    eta = psi2_a / (psi2_a + N/T),  mu_g = mu'Sinv 1 / 1'Sinv 1."""
    N = len(mu)
    Sinv_mu = np.linalg.solve(S_mle, mu)
    Sinv_1 = np.linalg.solve(S_mle, np.ones(N))
    a = mu @ Sinv_mu
    b = Sinv_1.sum()
    mu_g = Sinv_mu.sum() / b
    psi2 = a - mu_g ** 2 * b
    psi2a = max(psi2_adjusted(psi2, N, T), 0.0)
    eta = psi2a / (psi2a + N / T)
    c3 = (T - N - 1) * (T - N - 4) / (T * (T - 2))
    x = c3 / gamma * (eta * Sinv_mu + (1 - eta) * mu_g * Sinv_1)
    return x / abs(x.sum()) if relative else x


def w_tz(mu: np.ndarray, S_mle: np.ndarray, T: int, gamma: float = 3.0, relative=True):
    """Tu-Zhou (2011) optimal combination of 1/N and the unbiased-covariance ML rule.

    w_hat = (1/gamma) Stilde^-1 mu with Stilde = T S_mle/(T-N-2);  w_e = 1/N.
    delta = pi1/(pi1+pi2),
      pi1 = w_e'S w_e - (2/gamma) w_e'mu + theta2_a/gamma^2
      pi2 = (c1-1) theta2_a/gamma^2 + c1 N/(T gamma^2),  c1 = (T-2)(T-N-2)/((T-N-1)(T-N-4))."""
    N = len(mu)
    St = T * S_mle / (T - N - 2)
    w_hat = np.linalg.solve(St, mu) / gamma
    we = np.full(N, 1.0 / N)
    th2 = mu @ np.linalg.solve(S_mle, mu)
    th2a = max(theta2_adjusted(th2, N, T), 0.0)
    c1 = (T - 2) * (T - N - 2) / ((T - N - 1) * (T - N - 4))
    pi1 = we @ S_mle @ we - 2 / gamma * we @ mu + th2a / gamma ** 2
    pi2 = (c1 - 1) * th2a / gamma ** 2 + c1 * N / (T * gamma ** 2)
    delta = pi1 / (pi1 + pi2) if (pi1 + pi2) > 0 else 0.0
    delta = min(max(delta, 0.0), 1.0)
    x = (1 - delta) * we + delta * w_hat
    return (x / abs(x.sum()) if relative else x), float(delta)


def w_gmv_ridge(S: np.ndarray, nu: float) -> np.ndarray:
    """min w'(S + nu I)w s.t. 1'w = 1 — the solution of the DGNU 2-norm constrained GMV."""
    return w_gmv(S + nu * np.eye(S.shape[0]))


def w_gmv_norm2_cv(X: np.ndarray, n_folds: int = 5, grid=None) -> np.ndarray:
    """DGNU (2009) 2-norm constrained min-variance, delta calibrated by cross-validation.

    The constraint ||w||^2 <= delta is equivalent to a ridge term nu*I (Lagrange multiplier).
    We pick nu on a grid (relative to the average variance) to minimise the out-of-fold
    portfolio variance over n_folds contiguous folds of the estimation window, then
    re-estimate on the whole window."""
    T, N = X.shape
    S = cov_mle(X)
    avgvar = np.trace(S) / N
    if grid is None:
        grid = np.r_[0.0, avgvar * np.logspace(-3, 1, 17)]
    folds = np.array_split(np.arange(T), n_folds)
    best, best_nu = np.inf, 0.0
    for nu in grid:
        oos = []
        for f in folds:
            tr = np.setdiff1d(np.arange(T), f)
            w = w_gmv_ridge(cov_mle(X[tr]), nu)
            oos.append(X[f] @ w)
        v = np.var(np.concatenate(oos))
        if v < best:
            best, best_nu = v, nu
    return w_gmv_ridge(S, best_nu)


# ---------------- long-only quadratic programme on the simplex ----------------


def proj_simplex(v: np.ndarray) -> np.ndarray:
    """Euclidean projection onto {w >= 0, sum w = 1} (Duchi et al. 2008)."""
    n = len(v)
    u = np.sort(v)[::-1]
    css = np.cumsum(u)
    rho = np.nonzero(u * np.arange(1, n + 1) > (css - 1))[0][-1]
    theta = (css[rho] - 1) / (rho + 1.0)
    return np.maximum(v - theta, 0.0)


def qp_simplex(Q: np.ndarray, c: np.ndarray, iters: int = 20000, tol: float = 1e-13):
    """minimise 0.5 w'Qw - c'w over the simplex by FISTA (accelerated projected gradient).
    Returns (w, kkt_residual)."""
    N = len(c)
    L = np.linalg.eigvalsh(Q)[-1]
    step = 1.0 / L
    w = np.full(N, 1.0 / N)
    y, t = w.copy(), 1.0
    for _ in range(iters):
        w_new = proj_simplex(y - step * (Q @ y - c))
        t_new = 0.5 * (1 + math.sqrt(1 + 4 * t * t))
        y = w_new + (t - 1) / t_new * (w_new - w)
        if np.abs(w_new - w).sum() < tol:
            w = w_new
            break
        w, t = w_new, t_new
    return w, kkt_simplex_qp(Q, c, w)


def kkt_simplex_qp(Q, c, w, active_tol=1e-9) -> float:
    """KKT residual for min 0.5w'Qw - c'w on the simplex: gradient g = Qw - c must equal a
    constant lambda on the support and be >= lambda off it."""
    g = Q @ w - c
    on = w > active_tol
    lam = g[on].mean()
    r_on = np.abs(g[on] - lam).max()
    r_off = max(0.0, (lam - g[~on]).max()) if (~on).any() else 0.0
    return float(max(r_on, r_off))


def w_gmv_longonly(S):
    return qp_simplex(S, np.zeros(S.shape[0]))[0]


def w_mv_longonly(mu, S, gamma):
    return qp_simplex(gamma * S, mu)[0]


# =============================================================================
# Entropy dial
# =============================================================================


def gibbs(z: np.ndarray, beta: float) -> np.ndarray:
    """Maximum-entropy (Gibbs) tilt: argmax_{w in simplex} beta z'w + H(w) = softmax(beta z).

    This is Jaynes's (1957) maximum-entropy distribution under a mean constraint on z;
    beta = 0 gives 1/N, beta -> inf puts everything on the top-z asset."""
    a = beta * np.asarray(z, float)
    a = a - a.max()
    w = np.exp(a)
    return w / w.sum()


def gibbs_beta_for_neff(z: np.ndarray, target_ratio: float, beta_max: float = 50.0) -> float:
    """beta >= 0 such that exp(H(gibbs(z, beta))) = target_ratio * N (bisection; N_eff is
    strictly decreasing in beta for non-constant z)."""
    N = len(z)
    if target_ratio >= 1.0:
        return 0.0
    target = target_ratio * N
    lo, hi = 0.0, beta_max
    if neff_shannon(gibbs(z, hi)) > target:
        return hi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if neff_shannon(gibbs(z, mid)) > target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def entropy_mv(mu, S, gamma, tau, iters=200000, tol=1e-13, w0=None):
    """argmax_{w in simplex} w'mu - (gamma/2) w'S w + tau H(w), by mirror descent
    (exponentiated gradient).  Update in log space:
        log w <- (1 - eta tau) log w + eta (mu - gamma S w) + const.
    With S = 0 the fixed point is the Gibbs tilt softmax(mu/tau).
    Returns (w, kkt_residual, iterations).  KKT (interior, since tau > 0):
        mu_i - gamma (S w)_i - tau (log w_i + 1) = nu for every i."""
    mu = np.asarray(mu, float)
    N = len(mu)
    S = np.zeros((N, N)) if S is None else np.asarray(S, float)
    w = np.full(N, 1.0 / N) if w0 is None else np.asarray(w0, float).copy()
    L = gamma * np.abs(S).max() if S.any() else 0.0  # relative smoothness w.r.t. entropy
    eta = 1.0 / (tau + L)
    logw = np.log(w)
    for k in range(iters):
        g_smooth = mu - gamma * S @ w
        logw_new = (1 - eta * tau) * logw + eta * g_smooth
        logw_new -= logw_new.max()
        w_new = np.exp(logw_new)
        w_new /= w_new.sum()
        logw_new = np.log(w_new)
        if np.abs(w_new - w).sum() < tol:
            w, logw = w_new, logw_new
            break
        w, logw = w_new, logw_new
    g = mu - gamma * S @ w - tau * (np.log(w) + 1)
    kkt = float(np.abs(g - g.mean()).max())
    return w, kkt, k + 1


def normal_scores(x: np.ndarray) -> np.ndarray:
    """Cross-sectional rank -> standard normal scores (ties averaged)."""
    r = stats.rankdata(x)
    return stats.norm.ppf((r - 0.5) / len(x))


# =============================================================================
# Theory: information-matched shrinkage and the predicted effective N
# =============================================================================


def kz_scale(theta2: float, K: int, T: int) -> float:
    """Kan-Zhou optimal scaling of a K-parameter plug-in rule:
    c* = (T-K-1)(T-K-4)/(T(T-2)) * theta2/(theta2 + K/T)."""
    if T <= K + 4:
        return 0.0
    return (T - K - 1) * (T - K - 4) / (T * (T - 2)) * theta2 / (theta2 + K / T)


def info_share_from_t(t_hat: float) -> float:
    """Estimated knowledge share c = max(0, 1 - 1/t^2) (positive-part James-Stein form of
    theta2/(theta2 + 1/T) with the unbiased estimate theta2 - 1/T); 0 if t <= 1."""
    if not np.isfinite(t_hat) or t_hat <= 1.0:
        return 0.0
    return 1.0 - 1.0 / t_hat ** 2


def gibbs_moments(z: np.ndarray, beta: float):
    """(m, q) for the Gibbs tilt: m = sum w z (signal exposure), q = sum w^2 - 1/N."""
    w = gibbs(z, beta)
    return float(w @ z), float((w ** 2).sum() - 1.0 / len(z))


def theory_beta(z, mu_f, var_rho_D2, cov_ef, D2, gamma, beta_max=6.0):
    """beta* maximising  U(beta) = m mu_f - gamma m cov_ef - (gamma/2)[m^2 var_rho_D2 + D2 q]
    over beta >= 0, where (m, q) = gibbs_moments(z, beta).  mu_f is the (shrunk) expected
    return of the unit signal tilt, var_rho_D2 its factor variance net of idiosyncratic
    noise, cov_ef its covariance with the 1/N portfolio, D2 the cross-sectional variance of
    returns (idiosyncratic scale).  Returns (beta*, U(beta*))."""
    if mu_f - gamma * cov_ef <= 0:
        return 0.0, 0.0

    def negU(b):
        m, q = gibbs_moments(z, b)
        return -(m * mu_f - gamma * m * cov_ef - 0.5 * gamma * (m * m * var_rho_D2 + D2 * q))

    res = optimize.minimize_scalar(negU, bounds=(0.0, beta_max), method="bounded",
                                   options={"xatol": 1e-6})
    b = float(res.x)
    return (b, float(-res.fun)) if -res.fun > 0 else (0.0, 0.0)


def predicted_neff_ratio_closed(ic, N, T, gamma_D, sigma2_rho=0.0, sigma2_ic=None):
    """Closed-form-ish prediction N_eff*/N for normal scores and large N.

    knowledge share c = T ic^2 / (T ic^2 + s2), s2 = var(IC) (default: Grinold breadth 1/N
    plus sigma2_rho); beta solves  c ic = gamma_D beta (sigma2_rho + exp(beta^2)/N);
    N_eff/N = exp(-beta^2/2)."""
    if sigma2_ic is None:
        sigma2_ic = sigma2_rho + 1.0 / N
    if ic <= 0:
        return 1.0, 0.0, 0.0
    c = T * ic ** 2 / (T * ic ** 2 + sigma2_ic)
    f = lambda b: gamma_D * b * (sigma2_rho + np.exp(b * b) / N) - c * ic
    b = optimize.brentq(f, 0.0, 10.0)
    return float(np.exp(-b * b / 2)), float(c), float(b)


# =============================================================================
# Performance measures
# =============================================================================


def sharpe(r) -> float:
    r = np.asarray(r, float)
    return float(r.mean() / r.std(ddof=1))


def ceq(r, gamma) -> float:
    r = np.asarray(r, float)
    return float(r.mean() - 0.5 * gamma * r.var(ddof=1))


def turnover_series(W: np.ndarray, R: np.ndarray) -> np.ndarray:
    """W: (T, N) target weights set at the start of each month; R: (T, N) total returns in
    that month.  Turnover in month t = sum |W_t - W_{t-1}^+| with W_{t-1}^+ the drifted
    weights; the first month counts the build from cash (sum |W_0|)."""
    T = W.shape[0]
    to = np.zeros(T)
    prev = None
    for t in range(T):
        if prev is None:
            to[t] = np.abs(W[t]).sum()
        else:
            to[t] = np.abs(W[t] - prev).sum()
        g = W[t] * (1 + np.nan_to_num(R[t]))
        s = g.sum()
        prev = g / s if abs(s) > 1e-12 else W[t]
    return to


# =============================================================================
# Inference
# =============================================================================


def jkm_test(r1, r2):
    """Jobson-Korkie (1981) test of equal Sharpe ratios with Memmel's (2003) correction.
    Returns (z, two-sided p).  theta = [2 - 2 rho + 0.5 (s1^2 + s2^2 - 2 s1 s2 rho^2)] / T."""
    r1, r2 = np.asarray(r1, float), np.asarray(r2, float)
    T = len(r1)
    s1, s2 = sharpe(r1), sharpe(r2)
    rho = np.corrcoef(r1, r2)[0, 1]
    th = (2 - 2 * rho + 0.5 * (s1 ** 2 + s2 ** 2 - 2 * s1 * s2 * rho ** 2)) / T
    z = (s1 - s2) / math.sqrt(th) if th > 0 else 0.0
    return float(z), float(2 * stats.norm.sf(abs(z)))


def _sr_diff_and_grad(x):
    """x: (T, 2).  Delta = mu1/sd1 - mu2/sd2 from u = (mu1, mu2, g1, g2) (uncentred 2nd
    moments) and the gradient of f(u) (Ledoit-Wolf 2008, eq. for Delta)."""
    mu = x.mean(0)
    g = (x ** 2).mean(0)
    v = g - mu ** 2
    d = mu[0] / math.sqrt(v[0]) - mu[1] / math.sqrt(v[1])
    grad = np.array([
        g[0] / v[0] ** 1.5,
        -g[1] / v[1] ** 1.5,
        -0.5 * mu[0] / v[0] ** 1.5,
        0.5 * mu[1] / v[1] ** 1.5,
    ])
    return d, grad


def _block_psi(y: np.ndarray, b: int) -> np.ndarray:
    """Block-based (Gotze-Kunsch) estimate of the long-run covariance of y (T, k), using
    non-overlapping blocks of length b."""
    T = y.shape[0]
    l = T // b
    yc = y[: l * b] - y[: l * b].mean(0)
    sums = yc.reshape(l, b, -1).sum(1) / math.sqrt(b)
    return sums.T @ sums / l


def _hac_psi(y: np.ndarray, lags: int | None = None) -> np.ndarray:
    """Newey-West (Bartlett) long-run covariance of y (T, k)."""
    T = y.shape[0]
    if lags is None:
        lags = int(math.floor(4 * (T / 100) ** (2 / 9)))
    yc = y - y.mean(0)
    S = yc.T @ yc / T
    for j in range(1, lags + 1):
        G = yc[j:].T @ yc[:-j] / T
        S += (1 - j / (lags + 1)) * (G + G.T)
    return S


def lw_sharpe_test(r1, r2, b: int = 5, M: int = 4999, seed: int = SEED):
    """Ledoit & Wolf (2008) studentized circular block bootstrap test of H0: SR1 = SR2.

    Original statistic studentized with a Newey-West HAC standard error; bootstrap
    statistics studentized with the block-based (Gotze-Kunsch) standard error, as in LW's
    Algorithm 3.1.  Returns (delta, se, two-sided p)."""
    x = np.column_stack([r1, r2]).astype(float)
    T = x.shape[0]
    d, grad = _sr_diff_and_grad(x)
    y = np.column_stack([x, x ** 2])
    se = math.sqrt(grad @ _hac_psi(y) @ grad / T)
    rng = np.random.default_rng(seed)
    l = int(math.ceil(T / b))
    xx = np.vstack([x, x[:b]])  # circular wrap
    count = 0
    for _ in range(M):
        starts = rng.integers(0, T, size=l)
        idx = (starts[:, None] + np.arange(b)[None, :]).ravel()[:T] % T
        xs = xx[idx]
        ds, gs = _sr_diff_and_grad(xs)
        ys = np.column_stack([xs, xs ** 2])
        ses = math.sqrt(max(gs @ _block_psi(ys, b) @ gs / T, 1e-300))
        if se > 0 and abs(ds - d) / ses >= abs(d) / se:
            count += 1
    return float(d), float(se), float((count + 1) / (M + 1))


def newey_west_ols(y, X, lags: int | None = None):
    """OLS with Newey-West standard errors.  X should include a constant column.
    Returns (beta, se)."""
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    T = len(y)
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    e = y - X @ beta
    if lags is None:
        lags = int(math.floor(4 * (T / 100) ** (2 / 9)))
    Xe = X * e[:, None]
    S = Xe.T @ Xe
    for j in range(1, lags + 1):
        G = Xe[j:].T @ Xe[:-j]
        S += (1 - j / (lags + 1)) * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    return beta, np.sqrt(np.diag(V))


def stationary_bootstrap_indices(T, mean_block, rng):
    """Politis-Romano stationary bootstrap index vector of length T."""
    p = 1.0 / mean_block
    idx = np.empty(T, dtype=int)
    idx[0] = rng.integers(T)
    for t in range(1, T):
        idx[t] = rng.integers(T) if rng.random() < p else (idx[t - 1] + 1) % T
    return idx


def spa_test(d: np.ndarray, B: int = 4999, mean_block: float = 6.0, seed: int = SEED):
    """Hansen (2005) test for superior predictive ability.

    d: (T, K) performance differentials of K models over the benchmark (positive = model
    better).  H0: no model beats the benchmark (max_k E[d_k] <= 0).
    Returns dict with statistic and consistent / lower / upper p-values."""
    d = np.asarray(d, float)
    T, K = d.shape
    dbar = d.mean(0)
    rng = np.random.default_rng(seed)
    idxs = [stationary_bootstrap_indices(T, mean_block, rng) for _ in range(B)]
    boot_means = np.array([d[i].mean(0) for i in idxs])  # (B, K)
    omega = np.sqrt(T * ((boot_means - dbar) ** 2).mean(0))
    omega = np.where(omega > 0, omega, np.inf)
    stat = max(0.0, float((math.sqrt(T) * dbar / omega).max()))
    thresh = -math.sqrt(2 * math.log(math.log(T)))
    out = {"stat": stat}
    for name, mu in {
        "lower": np.maximum(dbar, 0.0),
        "consistent": np.where(math.sqrt(T) * dbar / omega >= thresh, dbar, 0.0),
        "upper": dbar,
    }.items():
        z = math.sqrt(T) * (boot_means - dbar + mu) / omega
        tb = np.maximum(z.max(1), 0.0)
        out["p_" + name] = float((tb >= stat).mean())
    return out


def pbo_cscv(R: np.ndarray, S: int = 16, metric=sharpe):
    """Probability of backtest overfitting by combinatorially symmetric cross-validation
    (Bailey, Borwein, Lopez de Prado & Zhu 2017).  R: (T, K) returns of K variants.
    Splits the T rows into S contiguous blocks; for every half/half combination picks the
    in-sample best variant and records the logit of its out-of-sample relative rank.
    Returns (pbo, logits)."""
    R = np.asarray(R, float)
    T, K = R.shape
    blocks = np.array_split(np.arange(T), S)
    logits = []
    for comb in itertools.combinations(range(S), S // 2):
        is_idx = np.concatenate([blocks[i] for i in comb])
        oos_idx = np.concatenate([blocks[i] for i in range(S) if i not in comb])
        is_perf = np.array([metric(R[is_idx, k]) for k in range(K)])
        oos_perf = np.array([metric(R[oos_idx, k]) for k in range(K)])
        best = int(np.argmax(is_perf))
        rank = stats.rankdata(oos_perf)[best] / (K + 1)  # relative rank in (0, 1)
        logits.append(math.log(rank / (1 - rank)))
    logits = np.array(logits)
    return float((logits <= 0).mean()), logits
