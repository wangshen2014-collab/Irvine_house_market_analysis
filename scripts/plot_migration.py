"""Plot observed county migration; does not produce a forecast."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((ROOT/'data/clean/county_components_2020_2025.csv').open()))
dof=sorted([r for r in rows if r['source_id']=='SRC-012' and r['geography']=='Orange County'],key=lambda r:r['estimate_year'])
census=sorted([r for r in rows if r['source_id']=='SRC-015' and r['geography']=='Orange County'],key=lambda r:r['estimate_year'])
assert len(dof)==len(census)==5
labels=[f"{int(r['estimate_year'])-1}-{str(r['estimate_year'])[-2:]}" for r in dof]
x=list(range(5))
plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(11.4,4.5),layout='constrained')
axes[0].bar([i-.17 for i in x],[int(r['net_domestic_migration'])/1000 for r in dof],.34,label='Domestic net',color='#ad5b4d')
axes[0].bar([i+.17 for i in x],[int(r['net_international_migration'])/1000 for r in dof],.34,label='International net',color='#4f8793')
axes[0].set_title('DOF: inflow and outflow channels',loc='left',weight='bold')
axes[1].plot(x,[int(r['net_migration'])/1000 for r in dof],marker='o',color='#285a69',label='DOF Feb 2026')
axes[1].plot(x,[int(r['net_migration'])/1000 for r in census],marker='s',linestyle='--',color='#996631',label='Census Vintage 2025')
axes[1].set_title('Total net migration: two vintages',loc='left',weight='bold')
for ax in axes:
 ax.set_xticks(x,labels);ax.axhline(0,color='#333',linewidth=.8);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
 ax.set_ylabel('Thousand people');ax.legend(frameon=False,loc='lower right',fontsize=9)
fig.suptitle('Orange County migration | July-to-June periods',fontsize=16,weight='bold')
fig.supxlabel('Sources: DOF E-2 (Feb 2026), Census county components (Mar 2026). Historical estimates; not home buyers.',fontsize=8)
(ROOT/'figures').mkdir(exist_ok=True)
fig.savefig(ROOT/'figures/orange_county_migration.svg')
fig.savefig(ROOT/'figures/orange_county_migration.png',dpi=160)
print('Saved observed migration chart in figures/')
