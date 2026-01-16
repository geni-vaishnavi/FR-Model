import pandas as pd

# 1 SCORING RULES & WEIGHTS

WEIGHTS = {
    "Net Profit Margin": 0.15,
    "Sales Growth or Turnover Growth": 0.15,
    "Net CF from Operations/EBITDA": 0.15,
    "DSCR": 0.15,
    "Interest coverage ratio (ICR)": 0.10,
    "Current Ratio": 0.10,
    "Cash Conversion Cycle": 0.10,
    "Leverage (Debt / Tangible Net Worth)": 0.10
}

# Scoring Thresholds (Value >= Threshold -> Score)

RULES = {
    "Net Profit Margin": [
        (0.15, 600), (0.12, 500), (0.10, 400), (0.08, 300), (0.05, 200), (0.02, 100)
    ],
    "Sales Growth or Turnover Growth": [
        (0.25, 600), (0.19, 500), (0.17, 400), (0.15, 300), (0.12, 200), (0.05, 100)
    ],
    "Net CF from Operations/EBITDA": [
        (4.00, 600), (3.00, 500), (2.00, 400), (1.00, 300), (0.50, 200), (0.01, 100)
    ],
    "DSCR": [
        (2.50, 600), (2.25, 500), (2.00, 400), (1.75, 300), (1.50, 200), (1.25, 100)
    ],
    "Interest coverage ratio (ICR)": [
        (4.00, 600), (3.50, 500), (3.00, 400), (2.00, 300), (1.50, 200), (1.00, 100)
    ],
    "Current Ratio": [
        (2.70, 600), (2.30, 500), (1.80, 400), (1.50, 300), (1.25, 200), (1.00, 100)
    ]
}


# 2. CALCULATION ENGINE

class APARFinancialModel:
    def __init__(self, data_dict):
        self.data = data_dict
        
    def _calculate_single_year(self, year, prev_year_revenue=None):
        """Calculates raw ratios for one specific year using Excel names."""
        fin = self.data.get(year, {})
        if not fin: return {}

        # 1. Net Profit Margin
       
        npm = (fin['Net Profit'] / fin['Net Sales']) if fin.get('Net Sales') else 0.0

        # 2. Sales Growth
        
        growth = 0.0
        if prev_year_revenue and fin.get('Net Sales'):
            growth = (fin['Net Sales'] - prev_year_revenue) / prev_year_revenue

        # 3. Net CF / EBITDA
        
        cf_ebitda = (fin['Operating Cash flows'] / fin['EBITDA']) if fin.get('EBITDA') else 0.0

        # 4. DSCR
        
        dscr = (fin['EBITDA'] / fin['Debt Service']) if fin.get('Debt Service') else 0.0

        # 5. ICR
        
        icr = (fin['EBIT'] / fin['Interest Payments']) if fin.get('Interest Payments') else 0.0

        # 6. Current Ratio
        
        curr_ratio = (fin['Current Assets'] / fin['Current Liabilities']) if fin.get('Current Liabilities') else 0.0

        # 7. Cash Conversion Cycle
        # Excel Logic: Inventory Days + Receivable Days - Payable Days
        ccc = 0.0
        if fin.get('COGS') and fin.get('Net Sales'):
            inv_days = (fin['Inventory'] / fin['COGS']) * 365
            rec_days = (fin['Trade and other receivables'] / fin['Net Sales']) * 365
            
            pay_days = (fin['Trade Creditors'] / fin['COGS']) * 365
            ccc = inv_days + rec_days - pay_days

        # 8. Leverage (Total Liab / TNW)
        
        tnw = fin.get('Shareholders Equity', 0) - fin.get('Intangible assets', 0)
        leverage = (fin['Total Liabilities'] / tnw) if tnw else 0.0

        
        return {
            "Net Profit Margin": npm,
            "Sales Growth or Turnover Growth": growth,
            "Net CF from Operations/EBITDA": cf_ebitda,
            "DSCR": dscr,
            "Interest coverage ratio (ICR)": icr,
            "Current Ratio": curr_ratio,
            "Cash Conversion Cycle": ccc,
            "Leverage (Debt / Tangible Net Worth)": leverage
        }

    def get_weighted_ratios(self, eval_year, prev_year, hist_year_revenue):
        """Applies 70% Current / 30% Previous logic."""
        
        r_prev = self._calculate_single_year(prev_year, hist_year_revenue)
        
       
        prev_rev = self.data[prev_year]['Net Sales']
        r_curr = self._calculate_single_year(eval_year, prev_rev)

        final = {}
        for k in r_curr:
            # Rule: Leverage uses 100% Current Year
            if k == "Leverage (Debt / Tangible Net Worth)":
                final[k] = r_curr[k]
            # Rule: All others use 70/30 weighted average
            else:
                final[k] = (r_curr[k] * 0.70) + (r_prev[k] * 0.30)
        
        return final

def get_score(metric_name, value):
    """Determines score based on metric rules."""
    
    #  CCC (Lower is Better)
    if metric_name == "Cash Conversion Cycle":
        if value <= 30.01: return 600
        elif value <= 60.01: return 300
        return 0
        
    #  Leverage (Lower is Better)
    if metric_name == "Leverage (Debt / Tangible Net Worth)":
        if value <= 1.00: return 500
        elif value <= 1.70: return 400
        elif value <= 2.50: return 300
        elif value <= 3.00: return 200
        elif value <= 3.50: return 100
        return 0

    # Standard Case 
    rules = RULES.get(metric_name, [])
    for threshold, score in rules:
        if value >= threshold:
            return score
    return 0


# 3. INPUT DATA 


inputs = {
    "2022": { "Net Sales": 116218.0 }, 
    "2023": {
        "Net Sales": 117554.0, 
        "COGS": 93319.0, 
        "Net Profit": 8917.0,
        "EBITDA": 14567.0, 
        "EBIT": 14567.0, 
        "Operating Cash flows": 14900.0,
        "Debt Service": 70119.0, 
        "Interest Payments": 5317.0,
        "Current Assets": 111109.0, 
        "Current Liabilities": 105687.0,
        "Inventory": 7124.0, 
        "Trade and other receivables": 29104.0, 
        "Trade Creditors": 35297.0,
        "Total Liabilities": 112566.0, 
        "Shareholders Equity": 18867.0, 
        "Intangible assets": 25.0
    },
    "2024": {
        "Net Sales": 135572.0, 
        "COGS": 106486.0, 
        "Net Profit": 7526.0,
        "EBITDA": 17926.0, 
        "EBIT": 17926.0, 
        "Operating Cash flows": 18582.0,
        "Debt Service": 76210.0, 
        "Interest Payments": 9744.0,
        "Current Assets": 161490.0, 
        "Current Liabilities": 138351.0,
        "Inventory": 18289.0, 
        "Trade and other receivables": 19641.0, 
        "Trade Creditors": 60131.0,
        "Total Liabilities": 153607.0, 
        "Shareholders Equity": 26392.0, 
        "Intangible assets": 15.0
    }
}

# 4. EXECUTION

# Initialize
model = APARFinancialModel(inputs)


final_ratios = model.get_weighted_ratios("2024", "2023", inputs["2022"]["Net Sales"])

# Calculate Scores
total_score = 0.0
print(f"{'Financial Ratios':<40} | {'Value':<10} | {'Score':<8} | {'Weights':<8}")
print("-" * 75)

order = [
    "Net Profit Margin",
    "Sales Growth or Turnover Growth",
    "Net CF from Operations/EBITDA",
    "DSCR",
    "Interest coverage ratio (ICR)",
    "Current Ratio",
    "Cash Conversion Cycle",
    "Leverage (Debt / Tangible Net Worth)"
]

for name in order:
    val = final_ratios[name]
    score = get_score(name, val)
    weight = WEIGHTS[name]
    weighted_score = score * weight
    total_score += weighted_score
    
    
    if "Margin" in name or "Growth" in name:
        val_str = f"{val:.3f}" 
    else:
        val_str = f"{val:.3f}"

    print(f"{name:<40} | {val_str:<10} | {score:<8.2f} | {weight*100:.0f}%")

print("-" * 75)
print(f"{'Financial Risk Score':<63} | {total_score:.3f}")
