# StrategyHub Research - System Architecture

**Last Updated:** January 27, 2026  
**Version:** 1.0 (Early Research Phase)

---

## 1. Executive Summary

StrategyHub Research is a **data-driven trading strategy research platform** currently in its initial research and development phase. The system focuses on backtesting and analyzing trading strategies using historical S&P 500 stock price data.

### Current Status
- **Phase:** Research & Data Pipeline Development
- **Primary Focus:** Data ingestion, cleaning, and metrics calculation
- **Architecture Type:** Modular Python-based research pipeline
- **Deployment:** Local development environment

---

## 2. System Overview

### 2.1 Project Structure

```
strategyhub-research/
├── src/                    # Source code
│   ├── ingest/            # Data acquisition modules
│   ├── clean/             # Data cleaning and preprocessing
│   ├── metrics/           # Performance metrics calculation
│   ├── strategies/        # Trading strategy implementations
│   ├── portfolio/         # Portfolio management logic
│   └── utils/             # Shared utilities
├── data_raw/              # Raw downloaded datasets
├── data_processed/        # Cleaned and transformed data
├── notebooks/             # Jupyter notebooks for research
└── docs/                  # Documentation
```

### 2.2 Technology Stack

#### Backend / Data Processing
- **Language:** Python 3.9+
- **Data Manipulation:** Pandas (assumed for financial data)
- **Data Source:** Kaggle (S&P 500 Stock Prices 2014-2017)
- **Data Download:** kagglehub library

#### Development Tools
- **Package Manager:** pip
- **Version Control:** Git (assumed)
- **CLI Tool:** Gemini CLI (for AI-assisted development)

---

## 3. Architectural Components

### 3.1 Data Layer

#### 3.1.1 Data Sources
- **Primary Dataset:** Kaggle S&P 500 Stock Prices (2014-2017)
  - **Slug:** `gauravmehta13/sp-500-stock-prices`
  - **Coverage:** Historical stock prices
  - **Known Limitations:**
    - No adjusted prices (dividends/splits ignored)
    - Survivorship bias present
    - Short historical period (3 years)

#### 3.1.2 Data Pipeline

**Stage 1: Ingestion** (`src/ingest/`)
- **Module:** `download_sp500.py`
- **Function:** Downloads raw data from Kaggle to `data_raw/sp500_stock_prices/`
- **Process:**
  1. Uses KaggleHub to download dataset to cache
  2. Copies files to project's `data_raw` directory
  3. Preserves original file metadata

**Stage 2: Cleaning** (`src/clean/`)
- **Module:** `clean_prices.py` (placeholder - not yet implemented)
- **Planned Functions:**
  - Handle missing values
  - Validate data integrity
  - Remove duplicates
  - Standardize date formats
  - Filter out invalid records

**Stage 3: Transformation** (`data_processed/`)
- **Purpose:** Store cleaned, analysis-ready datasets
- **Status:** Currently empty (awaiting implementation)

#### 3.1.3 Data Schema

**Return Definition:** Close-to-close returns
```
ret[t] = close[t] / close[t-1] - 1
```

**Expected Data Fields:**
- `date`: Trading date
- `symbol`: Stock ticker symbol
- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price
- `close`: Closing price (unadjusted)
- `volume`: Trading volume

---

### 3.2 Analytics Layer

#### 3.2.1 Metrics Module (`src/metrics/`)
- **Module:** `returns.py` (placeholder - not yet implemented)
- **Planned Metrics:**
  - Daily returns
  - Cumulative returns
  - Sharpe ratio
  - Maximum drawdown
  - Win rate
  - Risk-adjusted returns

#### 3.2.2 Strategy Module (`src/strategies/`)
- **Status:** Directory created, no implementations yet
- **Planned Strategies:**
  - Moving average crossover
  - Mean reversion
  - Momentum strategies
  - Technical indicator-based strategies

#### 3.2.3 Portfolio Module (`src/portfolio/`)
- **Status:** Directory created, no implementations yet
- **Planned Features:**
  - Position sizing algorithms
  - Portfolio rebalancing logic
  - Risk management rules
  - Capital allocation strategies

---

### 3.3 Application Layer

#### 3.3.1 Research Notebooks (`notebooks/`)
- **Status:** Empty directory
- **Planned Usage:**
  - Exploratory data analysis (EDA)
  - Strategy prototyping
  - Visualization of results
  - Interactive backtesting

#### 3.3.2 Utility Functions (`src/utils/`)
- **Status:** Directory created
- **Planned Utilities:**
  - Date/time helpers
  - Financial calculations
  - Data validation functions
  - Logging and error handling

---

## 4. Frontend Architecture

### 4.1 Current State
**Status:** ❌ Not Yet Implemented

### 4.2 Planned Frontend (Future Phases)

#### Technology Stack Options:
1. **Option A: Dashboard (Streamlit/Dash)**
   - Quick prototyping
   - Interactive charts and controls
   - Python-native integration

2. **Option B: Full Web Application**
   - **Frontend:** React/Next.js or Vue.js
   - **API:** FastAPI or Flask REST API
   - **Authentication:** JWT-based auth
   - **Charting:** Plotly, Chart.js, or TradingView widgets

#### Planned Features:
- 📊 Interactive strategy backtesting interface
- 📈 Real-time performance metrics dashboard
- 🔍 Stock screener and filter tools
- 📁 Strategy comparison and ranking
- 📤 Export results (CSV, PDF reports)
- 🔐 User authentication and saved strategies

---

## 5. Database Architecture

### 5.1 Current State
**Status:** ❌ No Database (File-based storage)

**Current Approach:**
- Raw data: CSV files in `data_raw/`
- Processed data: Planned for `data_processed/`
- No persistent database layer yet

### 5.2 Planned Database (Future Phases)

#### Option A: Time-Series Database (Recommended for Financial Data)
- **Technology:** InfluxDB, TimescaleDB, or QuestDB
- **Benefits:**
  - Optimized for time-series queries
  - Efficient data compression
  - Fast aggregation and downsampling
  - Built-in retention policies

#### Option B: Relational Database
- **Technology:** PostgreSQL
- **Schema Design:**

```sql
-- Stocks table
CREATE TABLE stocks (
    symbol VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(255),
    sector VARCHAR(100),
    industry VARCHAR(100)
);

-- Price data table
CREATE TABLE price_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) REFERENCES stocks(symbol),
    date DATE NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    UNIQUE(symbol, date)
);

-- Strategies table
CREATE TABLE strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    description TEXT,
    parameters JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Backtest results table
CREATE TABLE backtest_results (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    run_date TIMESTAMP DEFAULT NOW(),
    start_date DATE,
    end_date DATE,
    total_return DECIMAL(10,4),
    sharpe_ratio DECIMAL(10,4),
    max_drawdown DECIMAL(10,4),
    win_rate DECIMAL(5,2),
    metadata JSONB
);

-- Portfolio positions table
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    backtest_id INTEGER REFERENCES backtest_results(id),
    symbol VARCHAR(10),
    entry_date DATE,
    exit_date DATE,
    quantity INTEGER,
    entry_price DECIMAL(12,4),
    exit_price DECIMAL(12,4),
    pnl DECIMAL(12,4)
);
```

#### Option C: Hybrid Approach
- **PostgreSQL:** User data, strategies, metadata
- **Parquet Files:** Historical price data (columnar storage)
- **Redis:** Caching layer for frequent queries

---

## 6. API Architecture (Future Phase)

### 6.1 Planned REST API Endpoints

**Base URL:** `http://localhost:8000/api/v1`

#### Data Endpoints
```
GET    /stocks              # List all stocks
GET    /stocks/{symbol}     # Get stock details
GET    /prices/{symbol}     # Get price history
POST   /prices/bulk         # Upload bulk price data
```

#### Strategy Endpoints
```
GET    /strategies          # List all strategies
POST   /strategies          # Create new strategy
GET    /strategies/{id}     # Get strategy details
PUT    /strategies/{id}     # Update strategy
DELETE /strategies/{id}     # Delete strategy
```

#### Backtest Endpoints
```
POST   /backtest/run        # Run backtest
GET    /backtest/{id}       # Get backtest results
GET    /backtest/compare    # Compare multiple backtests
```

#### Metrics Endpoints
```
GET    /metrics/returns/{symbol}     # Calculate returns
GET    /metrics/sharpe/{strategy_id} # Sharpe ratio
GET    /metrics/summary/{backtest_id}# Performance summary
```

---

## 7. Data Flow Architecture

### 7.1 Current Data Flow (Research Phase)

```
┌─────────────────┐
│  Kaggle API     │
│  (Data Source)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  download_sp500.py      │
│  (Ingestion Module)     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  data_raw/              │
│  (Raw CSV Files)        │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  clean_prices.py        │
│  (Cleaning Module)      │ ⬅️ NOT YET IMPLEMENTED
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  data_processed/        │
│  (Clean Data)           │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Jupyter Notebooks      │
│  (Analysis)             │
└─────────────────────────┘
```

### 7.2 Planned Production Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Market    │────▶│   Ingestion │────▶│   Database  │
│   Data APIs │     │   Service   │     │  (TimeSeries)│
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┘
                    │
      ┌─────────────▼──────────┬──────────────┬─────────────┐
      │                        │              │             │
┌─────▼─────┐  ┌──────▼──────┐ │ ┌────▼────┐  │  ┌─────▼────┐
│ Strategy  │  │  Portfolio  │ │ │ Metrics │  │  │  API     │
│ Engine    │  │  Manager    │ │ │ Service │  │  │  Layer   │
└─────┬─────┘  └──────┬──────┘ │ └────┬────┘  │  └─────┬────┘
      │               │        │      │       │        │
      └───────────────┴────────┴──────┴───────┴────────┘
                                │
                         ┌──────▼──────┐
                         │  Frontend   │
                         │  Dashboard  │
                         └─────────────┘
```

---

## 8. Deployment Architecture

### 8.1 Current Deployment
- **Environment:** Local development machine (macOS)
- **Execution:** Manual script execution via Python
- **Dependencies:** User-managed via pip

### 8.2 Planned Deployment Options

#### Option A: Docker Containerized
```yaml
services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://...
    depends_on: [db, redis]
  
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
  
  db:
    image: timescale/timescaledb:latest
    volumes: ["./data:/var/lib/postgresql/data"]
  
  redis:
    image: redis:alpine
  
  celery-worker:
    build: ./backend
    command: celery -A app worker
```

#### Option B: Cloud Deployment
- **Platform:** AWS, Google Cloud, or Azure
- **API:** AWS Lambda / Google Cloud Run (serverless)
- **Database:** RDS PostgreSQL / Cloud SQL
- **Frontend:** Vercel / Netlify / S3 + CloudFront
- **Data Storage:** S3 / Google Cloud Storage

---

## 9. Security Architecture (Planned)

### 9.1 Authentication & Authorization
- **Method:** JWT tokens
- **User Roles:**
  - Admin: Full system access
  - Analyst: Strategy creation and backtesting
  - Viewer: Read-only access to results

### 9.2 Data Security
- **Encryption at Rest:** Database encryption
- **Encryption in Transit:** HTTPS/TLS for all API calls
- **API Keys:** Secure storage in environment variables
- **Secrets Management:** AWS Secrets Manager / Google Secret Manager

### 9.3 API Security
- Rate limiting
- CORS configuration
- Input validation and sanitization
- SQL injection prevention (parameterized queries)

---

## 10. Performance & Scalability

### 10.1 Current Performance Characteristics
- **Data Volume:** ~3 years of S&P 500 data (~500 stocks)
- **Processing:** Single-threaded Python scripts
- **Bottleneck:** File I/O for CSV reading

### 10.2 Planned Optimizations

#### Data Processing
- **Parallel Processing:** Use `multiprocessing` or `Dask` for large datasets
- **Vectorization:** Leverage NumPy/Pandas vectorized operations
- **Caching:** Cache frequently accessed datasets

#### Database Optimization
- Indexed queries on date and symbol columns
- Partitioning by date ranges
- Materialized views for common aggregations

#### Backend Scalability
- Horizontal scaling with load balancers
- Async API endpoints (FastAPI with async/await)
- Background task processing with Celery

---

## 11. Monitoring & Observability (Planned)

### 11.1 Logging
- **Framework:** Python `logging` module
- **Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Storage:** Centralized logging (ELK stack or Cloud Logging)

### 11.2 Metrics
- API response times
- Backtest execution duration
- Database query performance
- Error rates and types

### 11.3 Alerting
- Failed backtest runs
- Data ingestion failures
- API downtime
- Abnormal error rates

---

## 12. Development Workflow

### 12.1 Current Workflow
1. Manual data download via `download_sp500.py`
2. Data exploration in Jupyter notebooks
3. Strategy prototyping
4. Performance evaluation

### 12.2 Planned CI/CD Pipeline

```
┌──────────────┐
│  Git Push    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  GitHub      │
│  Actions     │
└──────┬───────┘
       │
       ├─────▶ Run Tests (pytest)
       ├─────▶ Lint Code (flake8/black)
       ├─────▶ Security Scan
       │
       ▼
┌──────────────┐
│  Build       │
│  Docker Image│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Deploy to   │
│  Staging     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Manual      │
│  Approval    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Deploy to   │
│  Production  │
└──────────────┘
```

---

## 13. Risks & Limitations

### 13.1 Current Limitations
- ❌ No real-time data (historical only)
- ❌ Short historical period (2014-2017)
- ❌ Survivorship bias in dataset
- ❌ No corporate action adjustments
- ❌ No transaction costs modeled
- ❌ No slippage considerations
- ❌ Single asset class (US equities only)

### 13.2 Technical Debt
- Clean and metrics modules are empty placeholders
- No automated testing
- No error handling or logging
- Hard-coded paths in download script
- No configuration management

---

## 14. Future Roadmap

### Phase 1: Core Research Platform (Current)
- ✅ Data ingestion from Kaggle
- ⏳ Data cleaning pipeline
- ⏳ Metrics calculation module
- ⏳ Basic strategy implementations
- ⏳ Jupyter notebook analysis

### Phase 2: Enhanced Analytics
- Real-time data integration
- Advanced strategy library
- Portfolio optimization
- Risk analytics
- Monte Carlo simulations

### Phase 3: Web Application
- REST API development
- React/Next.js frontend
- User authentication
- Strategy builder UI
- Interactive dashboards

### Phase 4: Production Platform
- Cloud deployment
- Scheduled backtests
- Email alerts
- Performance tracking
- Multi-user support

### Phase 5: Advanced Features
- Machine learning integration
- Automated strategy discovery
- Live trading paper accounts
- Social features (strategy sharing)
- Mobile application

---

## 15. Appendix

### 15.1 Key Files Reference

| File Path | Purpose | Status |
|-----------|---------|--------|
| `src/ingest/download_sp500.py` | Download data from Kaggle | ✅ Implemented |
| `src/clean/clean_prices.py` | Clean and validate data | ❌ Empty |
| `src/metrics/returns.py` | Calculate returns and metrics | ❌ Empty |
| `src/strategies/` | Trading strategy implementations | ❌ Empty |
| `src/portfolio/` | Portfolio management logic | ❌ Empty |
| `src/utils/` | Shared utility functions | ❌ Empty |
| `data_raw/` | Raw downloaded data | 📁 Directory only |
| `data_processed/` | Cleaned data | 📁 Empty |
| `notebooks/` | Jupyter notebooks | 📁 Empty |
| `docs/assumptions_week1.md` | Initial assumptions doc | ✅ Exists |

### 15.2 Dependencies

**Currently Installed:**
- `kagglehub` - Kaggle dataset downloads
- `shutil` - File operations (stdlib)
- `pathlib` - Path handling (stdlib)

**Likely Needed Soon:**
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `matplotlib` / `seaborn` - Visualization
- `jupyter` - Interactive notebooks
- `pytest` - Testing framework

### 15.3 Environment Setup

**Python Version:** 3.9.6  
**Package Manager:** pip (v21.2.4 - upgrade recommended)  
**Operating System:** macOS  

**Gemini CLI Path:**
```bash
/Users/mrigaypathak/Library/Python/3.9/bin/gemini-cli
```
⚠️ **Note:** This path is not currently on system PATH

---

## 16. Contact & Maintenance

**Project Owner:** Mrigay Pathak  
**Project Type:** Trading Strategy Research Platform  
**Repository:** `/Users/mrigaypathak/Desktop/trading app/strategyhub-research/`  
**Documentation:** `docs/` directory  

---

**Document Version History:**
- v1.0 (Jan 27, 2026): Initial architecture documentation
