"""Descriptive paired scenarios; observation-level inference is exploratory."""
import math
import numpy as np
import pandas as pd
from scipy import stats


def _json_safe(value):
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, np.integer):
        return int(value)
    return value


def paired(ref, adj):
    a=np.asarray(ref,dtype=float);b=np.asarray(adj,dtype=float)
    if a.shape!=b.shape: raise ValueError('Paired samples must have matching shapes')
    finite=np.isfinite(a)&np.isfinite(b);a=a[finite];b=b[finite];d=b-a;n=len(d)
    result={'n':n,'mean_ref':float(a.mean()) if n else None,
            'mean_adjusted':float(b.mean()) if n else None,
            'mean_difference':float(d.mean()) if n else None,
            'sd_difference':float(d.std(ddof=1)) if n>=2 else None,
            't':None,'df':n-1 if n>=2 else None,'p_t':None,
            'wilcoxon_W':None,'p_wilcoxon':None,'cohen_dz':None,
            'inference_status':'unavailable_insufficient_pairs' if n<2 else 'available'}
    if n>=2:
        sd=float(d.std(ddof=1))
        if sd>0:
            t=stats.ttest_rel(b,a)
            result.update(t=float(t.statistic),p_t=float(t.pvalue),cohen_dz=float(d.mean()/sd))
        else:
            result['inference_status']='unavailable_zero_difference_variance'
        if np.any(d!=0):
            w=stats.wilcoxon(d,method='approx',correction=False)
            result.update(wilcoxon_W=float(w.statistic),p_wilcoxon=float(w.pvalue))
    return _json_safe(result)


def summarize(df):
    # Missing scenario columns are missing observations, never zero adjustments.
    df=df.copy()
    columns=['company','year','model_input_status','missing_input_reason','igpm_status',
             'net_income','ebt','income_tax_signed','ppe_depreciation','ppe_gross_depreciable',
             'incc_ebt_adjusted_proxy','incc_net_income_after_assumed_tax_shield_proxy']
    for label in ('incc','igpm'):
        columns += [label+'_factor',label+'_depreciation_adjusted_proxy',
                    label+'_net_income_adjusted_proxy',label+'_delta_depreciation',
                    label+'_tax_difference_counterfactual_34pct']
    for column in columns:
        if column not in df: df[column]=np.nan
    primary=df[df.model_input_status=='documented_accounting_proxy_calculable'].copy()
    companies=[]
    for c,g in df.groupby('company',sort=False):
        r=primary[primary.company==c]
        v={'company':c,'n_adjusted':len(r),'n_income_official':int(g.net_income.notna().sum()),'included_years':[int(x) for x in r.year]}
        if len(r):
            for k in ('ppe_depreciation','incc_depreciation_adjusted_proxy','net_income','incc_net_income_adjusted_proxy'):
                v[k+'_mean']=float(r[k].mean())
            v['erosion_ratio_means_pct']=100*(v['net_income_mean']-v['incc_net_income_adjusted_proxy_mean'])/v['net_income_mean'] if v['net_income_mean']>0 else None
            pos=r[r.incc_ebt_adjusted_proxy>0]
            v['n_adjusted_ebt_positive']=len(pos)
            v['tax_expense_adjusted_ebt_ratio_pct']=float(-pos.income_tax_signed.sum()/pos.incc_ebt_adjusted_proxy.sum()*100) if len(pos) else None
        companies.append(v)
    tests={}
    for label in ('incc','igpm'):
        tests[label+'_depreciation']=paired(primary.ppe_depreciation,primary[label+'_depreciation_adjusted_proxy'])
        tests[label+'_net_income']=paired(primary.net_income,primary[label+'_net_income_adjusted_proxy'])
    tests['incc_ebt']=paired(primary.ebt,primary.incc_ebt_adjusted_proxy)
    gross=primary[primary.ppe_gross_depreciable.notna()]
    tests['gross_depreciable']=paired(gross.ppe_gross_depreciable,gross.ppe_gross_depreciable*gross.incc_factor)
    matched=primary[(primary.ebt>0)&(primary.incc_ebt_adjusted_proxy>0)&primary.income_tax_signed.notna()]
    a=(-matched.income_tax_signed/matched.ebt*100).to_numpy()
    b=(-matched.income_tax_signed/matched.incc_ebt_adjusted_proxy*100).to_numpy();d=b-a
    tests['tax_rate_signed_matched_positive']=paired(a,b)
    n=len(d);valid_variance=n>=2 and float(d.std(ddof=1))>0
    h2={'hypothesis':'Within company-year adjusted effective tax ratio exceeds observed ratio; fixed disclosed signed provision. No comparison against nominal34%.',
        'n':n,'firms':{c:int((matched.company==c).sum()) for c in sorted(matched.company.unique())},
        'inference_status':'available' if valid_variance else 'unavailable_insufficient_pairs' if n<2 else 'unavailable_zero_difference_variance',
        'reference_mean_pct':float(a.mean()) if n else None,'adjusted_mean_pct':float(b.mean()) if n else None,
        'mean_difference_pp':float(d.mean()) if n else None,
        'median_reference_pct':float(np.median(a)) if n else None,'median_adjusted_pct':float(np.median(b)) if n else None,
        'median_paired_difference_pp':float(np.median(d)) if n else None,
        'sd_paired_difference_pp':float(d.std(ddof=1)) if n>=2 else None,
        'positive_difference_count':int((d>0).sum()),'negative_difference_count':int((d<0).sum()),'zero_difference_count':int((d==0).sum()),
        'negative_tax_expense_count':int((matched.income_tax_signed>0).sum()),
        't_statistic':None,'paired_t_two_sided_p':None,'paired_t_greater_p':None,
        'observation_level_t95ci_mean_difference_pp':[None,None],
        'wilcoxon_two_sided_p':None,'wilcoxon_greater_p':None,'wilcoxon_W_twosided':None,
        'limits':'Exploratory observation-level tests, no firm/time clustering or causal legal inference. Tax benefits retained. Both EBT denominators positive. Fixed provision creates denominator mechanism, not cash-tax evidence.'}
    if valid_variance:
        ci=stats.t.interval(.95,n-1,loc=d.mean(),scale=d.std(ddof=1)/n**.5)
        h2.update(t_statistic=float(stats.ttest_rel(b,a).statistic),
                  paired_t_two_sided_p=float(stats.ttest_rel(b,a).pvalue),
                  paired_t_greater_p=float(stats.ttest_rel(b,a,alternative='greater').pvalue),
                  observation_level_t95ci_mean_difference_pp=[float(x) for x in ci])
    if n>=2 and np.any(d!=0):
        h2.update(wilcoxon_two_sided_p=float(stats.wilcoxon(d,method='approx').pvalue),
                  wilcoxon_greater_p=float(stats.wilcoxon(d,method='approx',alternative='greater').pvalue),
                  wilcoxon_W_twosided=float(stats.wilcoxon(d,method='approx').statistic))
    ll=float(primary.net_income.mean());adjusted=float(primary.incc_net_income_adjusted_proxy.mean())
    pos=primary[primary.incc_ebt_adjusted_proxy>0]
    means={'net_income_official':ll,'incc_net_income_adjusted_proxy':adjusted,
           'ppe_depreciation':float(primary.ppe_depreciation.mean()),
           'incc_depreciation_adjusted_proxy':float(primary.incc_depreciation_adjusted_proxy.mean()),
           'incc_difference':ll-adjusted,'erosion_ratio_means_pct':(ll-adjusted)/ll*100 if ll!=0 else None,
           'tax_actual_cont_rate_mean_pct':float(a.mean()) if n else None,
           'tax_actual_adjusted_rate_mean_pct':float(b.mean()) if n else None,
           'tax_matched_positive_n':n,'adjusted_ebt_positive_n':len(pos),
           'tax_ratio_sums_positive_adjusted_pct':float(-pos.income_tax_signed.sum()/pos.incc_ebt_adjusted_proxy.sum()*100) if len(pos) else None,
           'incc_net_income_after_assumed_tax_shield_proxy':float(primary.incc_net_income_after_assumed_tax_shield_proxy.mean())}
    years=[]
    for y,r in primary.groupby('year'):
        v={'year':int(y),'n_adjusted':len(r),'incc_factor_mean_pct':float((r.incc_factor.mean()-1)*100),'igpm_factor_mean_pct':float((r.igpm_factor.mean()-1)*100)}
        for label in ('incc','igpm'):
            v[label+'_delta_depreciation_sum']=float(r[label+'_delta_depreciation'].sum(min_count=1))
            v[label+'_tax_counterfactual_34pct_sum']=v[label+'_delta_depreciation_sum']*.34
        years.append(v)
    summary={'status':'Official unbalanced comparable accounting-proxy panel; no missing observation imputed',
        'inference_status':'available' if len(primary)>=2 else 'unavailable_insufficient_observations',
        'unit':'BRL millions','target_n':len(df),'income_n':int(df.net_income.notna().sum()),'adjusted_n':len(primary),
        'igpm_separately_calculable_n':int((df.igpm_status=='calculable').sum()),
        'companies':companies,'years':years,'tests':tests,'means':means,
        'totals':{s:{'delta_depreciation':float(primary[s+'_delta_depreciation'].sum(min_count=1)),
                     'tax_counterfactual_assumed34pct':float(primary[s+'_tax_difference_counterfactual_34pct'].sum(min_count=1))} for s in ('incc','igpm')},
        'gaps':[{'company':r.company,'year':int(r.year),'reason':r.missing_input_reason} for _,r in df[df.model_input_status!='documented_accounting_proxy_calculable'].iterrows()],
        'limits':'Amounts BRL millions; accounting stock/charge is not physical age. Comparative notes and issuer scopes documented. H1 is a scenario, not identified causal effect. H2 uses observed paired signed ETR, no nominal34% benchmark.34% only optional counterfactual tax shield. H3 theoretical; DFC/DMPL distributions alone do not establish physical capital erosion or forced financing. No full80 aggregate extrapolation.'}
    return _json_safe(summary),_json_safe(h2)
