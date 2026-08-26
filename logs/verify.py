import json
m = json.load(open('logs/metrics.json'))
ts = m['time_series']
print(f'Time series points: {len(ts)}')
for t in ts[:8]:
    print(f"  {t['date']}  cumulative_rate={t['cumulative_rate']}%  daily_recovered={t['daily_recovered']:,.0f}")
if len(ts) > 8:
    print(f"  ... and {len(ts)-8} more")
