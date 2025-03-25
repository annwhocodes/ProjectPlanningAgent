import pandas as pd
from crew_definition import crew

costs = 0.150 * (crew.usage_metrics.prompt_tokens + crew.usage_metrics.completion_tokens) / 1_000_000
print(f" Total estimated cost: ${costs:.4f}")

df_usage_metrics = pd.DataFrame([crew.usage_metrics.dict()])
print("\nUsage Metrics:")
print(df_usage_metrics)
