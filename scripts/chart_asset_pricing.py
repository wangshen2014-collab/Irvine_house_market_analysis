#!/usr/bin/env python3
"""Private charts from frozen derived inputs. Source time series stay private."""
import argparse,json,pathlib,datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
def main():
 p=argparse.ArgumentParser();p.add_argument('--private-out',required=True,type=pathlib.Path);a=p.parse_args();x=json.loads((a.private_out/'analysis.json').read_text());plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
 fig,ax=plt.subplots(figsize=(9,4.4),layout='constrained')
 for name,color in [('Irvine','#243b53'),('Stonegate','#007f82'),('Orchard Hills','#bc633a'),('Portola Springs','#7a5195')]:
  s=next(s for s in x['series']if s['geography']==name and s['product']=='four_bedroom');v=s['values'];dates=sorted(k for k in v if k>='2024-01-01');ax.plot([datetime.date.fromisoformat(k)for k in dates],[100*v[k]/v[dates[0]]for k in dates],label=name,color=color,lw=2)
 ax.set(title='Four-bedroom ZHVI | Jan 2024 = 100',ylabel='Seasonally adjusted, smoothed model index');ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'));ax.grid(axis='y',alpha=.2);ax.legend(ncol=2,frameon=False,loc='upper left');fig.get_layout_engine().set(rect=(0,.07,1,.93));fig.text(.015,.01,'Source: Zillow Research, downloaded 2026-10-12; through Aug 2026. Orchard Hills is not Reserve.',fontsize=8);fig.savefig(a.private_out/'zhvi_chart.png',dpi=180);plt.close(fig)
 fig,axs=plt.subplots(2,1,figsize=(9,6),layout='constrained',sharex=True)
 c=[r for r in x['county']if '202401'<=r['month_date_yyyymm']<='202609'];dates=[datetime.datetime.strptime(r['month_date_yyyymm'],'%Y%m')for r in c]
 for key,label,color in [('active_listing_count','Active stock','#007f82'),('pending_listing_count','Pending stock','#bc633a')]:axs[0].plot(dates,[float(r[key])for r in c],label=label,lw=2,color=color)
 axs[0].set(title='Orange County | inventory and new supply',ylabel='Snapshot listings');axs[0].legend(frameon=False,ncol=2);axs[1].bar(dates,[float(r['new_listing_count'])for r in c],width=20,color='#577590',label='New listings per month');axs[1].set(ylabel='Monthly new listings');axs[1].legend(frameon=False);axs[1].xaxis.set_major_locator(mdates.MonthLocator(interval=6));axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
 for ax in axs:ax.grid(axis='y',alpha=.2)
 fig.get_layout_engine().set(rect=(0,.05,1,.95));fig.text(.015,.01,'Source: Realtor.com Economic Research; retrieved 2026-10-12. Pending stock is not new contract flow.',fontsize=8);fig.savefig(a.private_out/'county_chart.png',dpi=180);plt.close(fig)
 print('2 private figures saved')
if __name__=='__main__':main()
