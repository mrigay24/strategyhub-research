/**
 * API Service for fetching real backtest data from the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface BacktestMetrics {
  total_return: number | null;
  cagr: number | null;
  volatility: number | null;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  max_drawdown: number | null;
  calmar_ratio: number | null;
  win_rate: number | null;
  profit_factor: number | null;
}

export interface EquityCurvePoint {
  date: string;
  equity: number;
  drawdown?: number;
}

export interface StrategyBacktest {
  id: number;
  name: string;
  strategy_type: string;
  description: string | null;
  symbol: string | null;
  run_id: number;
  start_date: string | null;
  end_date: string | null;
  initial_capital: number;
  final_capital: number | null;
  metrics: BacktestMetrics;
  equity_curve: EquityCurvePoint[];
}

export interface BenchmarkData {
  name: string;
  symbol: string;
  start_date: string | null;
  end_date: string | null;
  initial_capital: number;
  final_capital: number | null;
  metrics: {
    total_return: number | null;
    cagr: number | null;
    volatility: number | null;
    sharpe_ratio: number | null;
    max_drawdown: number | null;
  };
  equity_curve: EquityCurvePoint[];
}

export interface DashboardData {
  strategies: StrategyBacktest[];
  benchmark: BenchmarkData | null;
  total_strategies: number;
}

/**
 * Fetch dashboard data with all strategy backtests and benchmark
 */
export async function fetchDashboardData(): Promise<DashboardData> {
  const response = await fetch(`${API_BASE_URL}/backtests/dashboard`);

  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard data: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch a specific backtest run by ID
 */
export async function fetchBacktestById(runId: number) {
  const response = await fetch(`${API_BASE_URL}/backtests/${runId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch backtest: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch top performing strategies
 */
export async function fetchTopStrategies(metric: string = 'sharpe_ratio', limit: number = 10) {
  const response = await fetch(`${API_BASE_URL}/backtests/top?metric=${metric}&limit=${limit}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch top strategies: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Run a new backtest
 */
export async function runBacktest(params: {
  strategy_name: string;
  symbol?: string;
  params?: Record<string, unknown>;
  initial_capital?: number;
  commission_bps?: number;
  slippage_bps?: number;
}) {
  const response = await fetch(`${API_BASE_URL}/backtests/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error(`Failed to run backtest: ${response.statusText}`);
  }

  return response.json();
}

export interface RegimeResearch {
  bull_sharpe: number | null;
  bear_sharpe: number | null;
  high_vol_sharpe: number | null;
  sideways_sharpe: number | null;
  best_regime: string | null;
  worst_regime: string | null;
  overall_sharpe: number | null;
}

export interface MonteCarloResearch {
  sharpe: number | null;
  adjusted_sharpe: number | null;
  verdict: string | null;
  iid_p_value: number | null;
  iid_ci_lower: number | null;
  iid_ci_upper: number | null;
  block_p_value: number | null;
  sign_p_value: number | null;
  percentile_rank: number | null;
}

export interface WalkForwardResearch {
  is_sharpe: number | null;
  oos_sharpe: number | null;
  wfe: number | null;
  verdict: string | null;
  avg_oos_sharpe: number | null;
  avg_wfe: number | null;
  fold_oos_sharpes: number[];
  fold_labels: string[];
  n_folds: number | null;
}

export interface ScorecardResearch {
  tier: string | null;
  sharpe: number | null;
  cagr: number | null;
  max_drawdown: number | null;
  pct_positive_years: number | null;
  adj_sharpe: number | null;
}

export interface StrategyResearch {
  strategy_name: string;
  data_period: string | null;
  n_bootstrap: number | null;
  monte_carlo: MonteCarloResearch | null;
  walk_forward: WalkForwardResearch | null;
  regime: RegimeResearch | null;
  scorecard: ScorecardResearch | null;
}

export interface StrategyParameter {
  name: string;
  label: string;
  default: number;
  min: number;
  max: number;
  step: number;
  robustness: 'ROBUST' | 'FRAGILE';
  description: string;
}

/**
 * Fetch Phase 3 research results for a strategy
 */
export async function fetchResearchData(strategyName: string): Promise<StrategyResearch> {
  const response = await fetch(`${API_BASE_URL}/research/${strategyName}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch research data: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch tunable parameter definitions for a strategy
 */
export async function fetchStrategyParameters(strategyName: string): Promise<{ parameters: StrategyParameter[] }> {
  const response = await fetch(`${API_BASE_URL}/research/parameters/${strategyName}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch parameters: ${response.statusText}`);
  }
  return response.json();
}

export interface FactorAlpha {
  strategy_name: string;
  capm: {
    alpha_annual: number | null;
    beta: number | null;
    r_squared: number | null;
  };
  longshort: {
    cagr: number | null;
    volatility: number | null;
    sharpe_ratio: number | null;
    max_drawdown: number | null;
    market_correlation: number | null;
    equity_curve: { date: string; value: number }[];
  };
  longonly: { cagr: number | null; sharpe_ratio: number | null };
  benchmark: { cagr: number | null; sharpe_ratio: number | null };
}

export async function fetchFactorAlpha(strategyName: string): Promise<FactorAlpha> {
  const response = await fetch(`${API_BASE_URL}/research/alpha/${strategyName}`);
  if (!response.ok) throw new Error(`Failed to fetch factor alpha: ${response.statusText}`);
  return response.json();
}

export interface SensitivityData {
  strategy_name: string;
  defaults: Record<string, number>;
  sweep_1d: {
    param: string;
    values: { param_value: number; sharpe_ratio: number | null; is_default: boolean }[];
  }[];
  heatmap: {
    param_1: string | null;
    param_2: string | null;
    values_1: number[];
    values_2: number[];
    default_1: number | null;
    default_2: number | null;
    grid: { v1: number; v2: number; sharpe: number | null }[];
  };
  robustness: Record<string, {
    robustness: string;
    sharpe_min: number;
    sharpe_max: number;
    coefficient_of_variation: number;
  }>;
}

export async function fetchSensitivityData(strategyName: string): Promise<SensitivityData> {
  const response = await fetch(`${API_BASE_URL}/research/sensitivity/${strategyName}`);
  if (!response.ok) throw new Error(`Failed to fetch sensitivity data: ${response.statusText}`);
  return response.json();
}

export interface RollingMetrics {
  strategy_name: string;
  data_period: string | null;
  n_years: number;
  rank_stability: number | null;
  annual_sharpe: { year: number; strategy: number | null; benchmark: number | null }[];
  annual_cagr: { year: number; strategy: number | null; benchmark: number | null }[];
  annual_mdd: { year: number; strategy: number | null; benchmark: number | null }[];
}

export interface CorrelationData {
  strategies: string[];
  cells: { row: string; col: string; value: number | null }[];
  avg_correlation: number | null;
  diversification_ratio: number | null;
  data_period: string | null;
}

export async function fetchRollingMetrics(strategyName: string): Promise<RollingMetrics> {
  const response = await fetch(`${API_BASE_URL}/research/rolling/${strategyName}`);
  if (!response.ok) throw new Error(`Failed to fetch rolling metrics: ${response.statusText}`);
  return response.json();
}

export async function fetchCorrelationData(): Promise<CorrelationData> {
  const response = await fetch(`${API_BASE_URL}/research/correlation`);
  if (!response.ok) throw new Error(`Failed to fetch correlation data: ${response.statusText}`);
  return response.json();
}

// ── AI Strategy Builder ────────────────────────────────────────────────────

export interface AiBuilderFactor {
  id: string
  name: string
  weight: number
  role: string
}

export interface AiBuilderStrategySpec {
  matched_strategy: string
  strategy_display_name: string
  confidence: number
  factors: AiBuilderFactor[]
  hypothesis: string
  rebalancing: string
  universe: string
  key_risk: string
  analyst_note: string
}

export interface AiBuilderGate {
  gate: number
  name: string
  criterion: string
  value: string
  result: 'PASS' | 'FAIL' | 'CAVEAT'
  detail: string
}

export interface AiBuilderResponse {
  raw_response: string
  strategy_spec: AiBuilderStrategySpec | null
  validation_gates: AiBuilderGate[]
  n_passed: number
  n_failed: number
  n_caveat: number
  overall_verdict: string
  matched_strategy_info: { display?: string; family?: string; desc?: string }
}

export interface FactorInfo {
  id: string
  name: string
  category: string
  description: string
  academic_source: string
  signal: string
  typical_holding: string
  used_in: string[]
}

export async function fetchAiBuilderGenerate(
  messages: { role: string; content: string }[]
): Promise<AiBuilderResponse> {
  const response = await fetch(`${API_BASE_URL}/ai-builder/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(err.detail || `AI Builder error: ${response.statusText}`)
  }
  return response.json()
}

export interface CustomBacktest {
  sharpe_ratio: number | null
  cagr: number | null
  max_drawdown: number | null
  volatility: number | null
  total_return: number | null
  win_rate: number | null
  equity_curve: { date: string; value: number }[]
}

export interface AiBuilderGenerateAndBacktestResponse extends AiBuilderResponse {
  factor_code: string
  custom_backtest: CustomBacktest | null
  backtest_error: string | null
}

export async function fetchAiBuilderGenerateAndBacktest(
  messages: { role: string; content: string }[]
): Promise<AiBuilderGenerateAndBacktestResponse> {
  const response = await fetch(`${API_BASE_URL}/ai-builder/generate-and-backtest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(err.detail || `AI Builder error: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchFactorLibrary(): Promise<{ factors: FactorInfo[]; n_factors: number }> {
  const response = await fetch(`${API_BASE_URL}/ai-builder/factors`)
  if (!response.ok) throw new Error('Failed to fetch factor library')
  return response.json()
}

// ── Live Signals ─────────────────────────────────────────────────────────────

export interface LiveHolding {
  symbol: string;
  weight: number;
  rank: number;
}

export interface LiveSignals {
  strategy_name: string;
  generated_at: string | null;
  signal_date: string | null;
  n_holdings: number | null;
  holdings: LiveHolding[];
  data_source: string;
}

export async function fetchLiveSignals(strategyName: string): Promise<LiveSignals> {
  const res = await fetch(`${API_BASE_URL}/research/signals/${strategyName}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `Failed to fetch signals for ${strategyName}`)
  }
  return res.json()
}

/**
 * Fetch available strategies from the backend
 */
export async function fetchAvailableStrategies() {
  const response = await fetch(`${API_BASE_URL}/strategies/available`);

  if (!response.ok) {
    throw new Error(`Failed to fetch available strategies: ${response.statusText}`);
  }

  return response.json();
}
