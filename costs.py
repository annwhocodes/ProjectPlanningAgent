import pandas as pd
from crew_definition import crew

# Calculate estimated costs
costs = 0.150 * (crew.usage_metrics.prompt_tokens + crew.usage_metrics.completion_tokens) / 1_000_000
print(f" Total estimated cost: ${costs:.4f}")

# Convert UsageMetrics instance to DataFrame
df_usage_metrics = pd.DataFrame([crew.usage_metrics.dict()])
print("\nUsage Metrics:")
print(df_usage_metrics)
