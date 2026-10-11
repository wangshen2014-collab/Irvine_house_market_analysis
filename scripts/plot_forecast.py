"""Plot official county projections as versioned conditional scenarios."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

plt.rcParams['svg.fonttype'] = 'none'

ROOT = Path(__file__).resolve().parents[1]
with (ROOT/'data/clean/dof_oc_population_projection_v2026.csv').open() as f:
    dof = [r for r in csv.DictReader(f) if 2025 <= int(r['year']) <= 2050]
with (ROOT/'data/clean/scag_city_county_forecast_vintages.csv').open() as f:
    scag = [r for r in csv.DictReader(f) if r['geography']=='Orange County' and int(r['year']) >= 2025]
fig, ax = plt.subplots(figsize=(9, 4.7), dpi=160)
ax.plot([int(r['year']) for r in dof], [int(r['population_total']) for r in dof], color='#245878', linewidth=2.4, linestyle='--', label='DOF Baseline 2024 / Vintage Mar 2026')
ax.plot([int(r['year']) for r in scag], [int(r['population_supplement']) for r in scag], color='#c57437', linewidth=2.4, linestyle='--', marker='o', markersize=4, label='SCAG Connect SoCal 2024 / adopted Apr 2024')
ax.set_title('Orange County: official population projections diverge', loc='left', fontweight='bold', fontsize=13, pad=16)
ax.set_ylabel('Population (millions)')
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x/1e6:.2f}'))
ax.set_xticks([2025,2030,2035,2040,2045,2050])
ax.set_xlim(2024,2051)
ax.set_ylim(3100000,3500000)
ax.grid(axis='y', alpha=.2)
ax.spines[['top','right']].set_visible(False)
ax.legend(loc='upper left', frameon=False, fontsize=9)
ax.annotate('3,439,000', (2050,3439000), xytext=(-75,9), textcoords='offset points', color='#a35e2e')
ax.annotate('3,151,816', (2050,3151816), xytext=(-75,-18), textcoords='offset points', color='#245878')
fig.text(.1,.015,'Sources: California DOF P-2A; SCAG Table 12. Both July 1; SCAG rounded to 1,000.\nDashed lines show conditional projections, not a confidence interval. SCAG segments connect published 5-year points.',fontsize=8,color='#4d5966')
fig.tight_layout(rect=(0,.09,1,1))
(ROOT/'figures').mkdir(exist_ok=True)
fig.savefig(ROOT/'figures/orange_county_forecast.svg')
fig.savefig(ROOT/'figures/orange_county_forecast.png')
print('Saved forecast SVG and PNG')
