## Execution Framework

The portfolio is implemented through a weekly monitoring + quarterly rebalancing cycle that balances signal responsiveness with transaction cost discipline. This approach ensures the strategy remains adaptive to new information without excessive turnover.

### Rebalancing Schedule & Logic

Weekly Review (Every Sunday):
1. Ingest last 255 trading days of price/volume data
2. Run gradient descent optimization → new target weights  
3. Compute drift: `max(|target_i - current_i|)` for each ETF
4. Action: Log results, no automatic trading

Quarterly Rebalance (1st Monday of Jan/Apr/Jul/Oct):
1. Review latest target weights from weekly computation
2. Execute if: Any single ETF drift >= 15% OR total TC < **25bps AUM**
3. Manual approval required before orders

Immediate Risk-Off Override (Anytime):
- Optimizer outputs stress_score > 0.8 → equal weights
- VIX > 35 OR avg corr > 0.75 → 50% cash
- Execute same day, document rationale

### Order Execution Protocol

Timing: Monday 9:30-11:00 CET (primary liquidity window)

Order Types:
Liquid ETFs (CSPX, Gold): Market orders
Illiquid ETFs (INR, CNYA): Limit orders at mid ±5bps
Bonds: Market order (liquid enough)

### Transaction Cost Management

Live TC Formula: TC = max(€3.50, 0.00065 × trade_value) + 2 × ETF_half_spread
Threshold: Skip if TC > 0.25% AUM

Expected Frequency: 2-4 rebalances per year
Annual TC Drag: 15-25bps