#!/usr/bin/env python3
import argparse,json,pathlib,datetime
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--analysis',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args();x=json.loads(a.analysis.read_text());a.out.mkdir(parents=True,exist_ok=True)
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
 colors=['#164e63','#be6c28','#6d6ca2'];fig,ax=plt.subplots(figsize=(10,4.6),layout='constrained')
 for key,label,col in zip(['MORTGAGE30US','GS10','FEDFUNDS'],['30-year mortgage (PMMS)','10-year Treasury','Effective federal funds'],colors):
  v=x['monthly'][key];dates=sorted(d for d in v if '2000-01'<=d<='2026-08');ax.plot([datetime.date.fromisoformat(d+'-01')for d in dates],[v[d]for d in dates],label=label,color=col,lw=1.5)
 ax.set_ylabel('Percent, monthly mean');ax.grid(alpha=.15);ax.legend(loc='upper right',ncol=1,frameon=False);ax.set_title('Policy cuts do not map one-for-one into mortgage rates',loc='left',fontweight='bold');fig.text(.025,.018,'Source: Federal Reserve / Freddie Mac via FRED. Frozen 12 Oct 2026; complete months through Aug 2026.',fontsize=8,color='#555');fig.get_layout_engine().set(rect=(0,.06,1,.95));fig.savefig(a.out/'rate_channels.png',dpi=180);plt.close(fig)
 fig,axs=plt.subplots(1,2,figsize=(10,4.8),layout='constrained')
 for ax,start,end,title in zip(axs,['2006-12','2021-12'],['2012-12','2023-12'],['2006–2012: rates down, prices down','2021–2023: rates up, prices up']):
  months=sorted(k for k in x['prices']['Irvine|four_bedroom']if start<=k<=end);r0=x['monthly']['MORTGAGE30US'][start];f=lambda r:(r/1200)/(1-(1+r/1200)**-360);q=[f(r0)/f(x['monthly']['MORTGAGE30US'][k])for k in months];p=x['prices']['Irvine|four_bedroom'];dates=[datetime.date.fromisoformat(k+'-01')for k in months]
  ax.plot(dates,[p[k]/p[start]*100 for k in months],label='Irvine 4-bed ZHVI',color=colors[0],lw=2);ax.plot(dates,[100*z for z in q],label='Equal PI: fixed down %',color=colors[1],lw=1.6);ax.plot(dates,[100*(.2+.8*z)for z in q],label='Equal PI: fixed down $ (20%)',color=colors[2],lw=1.4,ls='--');ax.set_title(title,loc='left',fontsize=11);ax.grid(alpha=.15);ax.set_ylabel('Start month = 100');ax.tick_params(axis='x',rotation=25)
 axs[0].legend(loc='upper left',fontsize=8,frameon=False);fig.text(.02,.96,'Payment capacity is not a price forecast',ha='left',fontweight='bold',fontsize=15);fig.text(.025,.018,'Sources: Zillow modeled, smoothed SA 4-bedroom index; Freddie Mac via FRED; own 30-year PI calculation.\nNo tax, insurance, HOA, income growth or quality-matched transactions. Frozen 12 Oct 2026.',fontsize=8,color='#555');fig.get_layout_engine().set(rect=(0,.10,1,.78));fig.savefig(a.out/'rate_price_counterexamples.png',dpi=180);plt.close(fig)
 print('2 charts saved')
if __name__=='__main__':main()
