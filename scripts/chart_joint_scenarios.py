#!/usr/bin/env python3
import argparse,json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--private-out',type=pathlib.Path,required=True);a=ap.parse_args();x=json.loads((a.private_out/'analysis.json').read_text())
plt.rcParams.update({'font.family':'Noto Sans CJK SC','axes.unicode_minus':False,'font.size':11})
fig,ax=plt.subplots(figsize=(10,4.8));fig.subplots_adjust(left=.10,right=.98,bottom=.22,top=.82)
ys=np.arange(2,5.51,.25)
for s,c in [(1.5,'#2b8cbe'),(2,'#0a695d'),(2.5,'#a66e22'),(3,'#956579')]:ax.plot(ys,ys+s,label=f'综合利差 {s:.1f} 个百分点',color=c,lw=2)
ax.axhspan(4,5,color='#e0f2e8',alpha=.8);ax.axvline(5.22,color='#a74737',ls='--');ax.text(5.17,4.1,'10月8日\n国债5.22%',ha='right',color='#a74737',fontsize=10)
ax.set(xlabel='假设10年国债收益率（%）',ylabel='机械相加的按揭利率（%）',xlim=(2,5.5),ylim=(3.5,8.7));ax.grid(alpha=.15);ax.legend(loc='upper left',fontsize=9,ncol=2);fig.text(.03,.94,'4字头是条件组合，不是到达日期',fontsize=16,weight='bold');fig.text(.03,.06,'绿色带：4% ≤ 按揭 < 5%。利差为假设；粗略分解不是定价模型，也不是个人贷款报价。',fontsize=10)
fig.savefig(a.private_out/'four_handle_conditions.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,4.8));fig.subplots_adjust(left=.1,right=.98,bottom=.23,top=.82)
rates=[z['rate_pct']for z in x['equal_payment_boundaries']]
for key,label,c in [('fixed_cash_equal_PI_price_index','固定首付现金40','#0a695d'),('fixed_fraction_equal_PI_price_index','固定首付比例40%','#a66e22')]:ax.plot(rates,[z[key]for z in x['equal_payment_boundaries']],'-o',label=label,color=c,lw=2)
ax.axhline(100,color='#777',ls='--',lw=1);ax.scatter([7.375],[100],c='#1f333b',s=40,zorder=5);ax.text(7.45,102,'初始7.375% / 价格100',fontsize=9);ax.set(xlabel='未来利率假设（%）',ylabel='保持相同月PI的房价指数',ylim=(85,140));ax.grid(alpha=.15);ax.legend(loc='upper right',fontsize=10);fig.text(.03,.94,'低利率可以被涨价抵消；首付约束决定幅度',fontsize=16,weight='bold');fig.text(.03,.07,'虚构初始房价100、首付40、30年摊还。仅PI，不含等待成本、税险、交易费或收入约束。',fontsize=10)
fig.savefig(a.private_out/'payment_boundaries.png',dpi=180);plt.close(fig)
