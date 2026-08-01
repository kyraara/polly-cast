import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller, acf, pacf

class EDAService:
    @staticmethod
    def get_statistik_deskriptif(series):
        if series.empty:
            return {}
        desc = series.describe()
        return {
            'count': int(desc['count']),
            'mean': float(desc['mean']),
            'std': float(desc['std']),
            'min': float(desc['min']),
            'q1': float(desc['25%']),
            'median': float(desc['50%']),
            'q3': float(desc['75%']),
            'max': float(desc['max']),
            'skewness': float(series.skew()) if not pd.isna(series.skew()) else 0.0,
            'kurtosis': float(series.kurtosis()) if not pd.isna(series.kurtosis()) else 0.0
        }

    @staticmethod
    def get_decomposition(series, period=12):
        if series.empty:
            return {'trend': [], 'seasonal': [], 'residual': [], 'observed': [], 'labels': []}

        # Ensure index is DatetimeIndex
        if not isinstance(series.index, pd.DatetimeIndex):
            series.index = pd.to_datetime(series.index)
        
        # Resample to Month Start to ensure frequency
        series_freq = series.resample('MS').first()
        
        try:
            decomposition = seasonal_decompose(series_freq, model='additive', period=period)
            
            trend = [float(x) if not pd.isna(x) else None for x in decomposition.trend]
            seasonal = [float(x) if not pd.isna(x) else None for x in decomposition.seasonal]
            resid = [float(x) if not pd.isna(x) else None for x in decomposition.resid]
            observed = [float(x) if not pd.isna(x) else None for x in decomposition.observed]
            
            return {
                'trend': trend,
                'seasonal': seasonal,
                'residual': resid,
                'observed': observed,
                'labels': [x.strftime('%Y-%m') for x in series_freq.index]
            }
        except Exception as e:
            return {
                'trend': [None] * len(series_freq),
                'seasonal': [None] * len(series_freq),
                'residual': [None] * len(series_freq),
                'observed': [float(x) for x in series_freq.values],
                'labels': [x.strftime('%Y-%m') for x in series_freq.index],
                'error': str(e)
            }

    @staticmethod
    def get_boxplot_data(series):
        if series.empty:
            return {'min': 0, 'q1': 0, 'median': 0, 'q3': 0, 'max': 0, 'outliers': []}
            
        q1 = float(np.percentile(series, 25))
        median = float(np.percentile(series, 50))
        q3 = float(np.percentile(series, 75))
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = series[(series < lower_bound) | (series > upper_bound)].tolist()
        
        filtered_series = series[(series >= lower_bound) & (series <= upper_bound)]
        min_val = float(filtered_series.min()) if not filtered_series.empty else float(series.min())
        max_val = float(filtered_series.max()) if not filtered_series.empty else float(series.max())
        
        return {
            'min': min_val,
            'q1': q1,
            'median': median,
            'q3': q3,
            'max': max_val,
            'outliers': [float(x) for x in outliers]
        }

    @staticmethod
    def detect_seasonal_type(series, period=12):
        if series.empty:
            return 'add'
            
        try:
            # Ensure frequency is set
            series_freq = series.resample('MS').first()
            decomposition = seasonal_decompose(series_freq, model='additive', period=period)
            
            # Compute amplitude of seasonal component
            seasonal = decomposition.seasonal.dropna()
            if seasonal.empty:
                return 'add'
                
            amplitude = seasonal.max() - seasonal.min()
            
            # Simple heuristic based on Standard Deviation relative to Mean (Coefficient of Variation)
            cv = float(np.std(series) / np.mean(series))
            if cv < 0.15:
                return 'add'
            else:
                return 'mul'
        except:
            return 'add'

    @staticmethod
    def uji_stasioner(series):
        if series.empty:
            return {
                'adf_statistic': None,
                'p_value': None,
                'critical_values': {},
                'is_stationary': None,
                'conclusion': 'Data kosong, tidak dapat melakukan uji stasioner.'
            }
        try:
            series_clean = series.dropna()
            result = adfuller(series_clean, autolag='AIC')
            adf_stat = float(result[0])
            p_val = float(result[1])
            crit_vals = {k: float(v) for k, v in result[4].items()}
            is_stationary = p_val < 0.05
            conclusion = (
                f"Data {'sudah stasioner' if is_stationary else 'belum stasioner'} "
                f"(ADF = {adf_stat:.4f}, p-value = {p_val:.4f}). "
                f"Nilai kritis: 1% = {crit_vals.get('1%', 0):.4f}, "
                f"5% = {crit_vals.get('5%', 0):.4f}, "
                f"10% = {crit_vals.get('10%', 0):.4f}."
            )
            return {
                'adf_statistic': adf_stat,
                'p_value': p_val,
                'critical_values': crit_vals,
                'is_stationary': is_stationary,
                'conclusion': conclusion
            }
        except Exception as e:
            return {
                'adf_statistic': None,
                'p_value': None,
                'critical_values': {},
                'is_stationary': None,
                'conclusion': f"Gagal melakukan uji stasioner: {str(e)}"
            }

    @staticmethod
    def acf_pacf_data(series, nlags=24):
        if series.empty:
            return {'acf_values': [], 'pacf_values': [], 'nlags': 0}
        try:
            series_clean = series.dropna()
            max_lags = min(nlags, len(series_clean) // 2 - 1)
            if max_lags < 1:
                return {'acf_values': [], 'pacf_values': [], 'nlags': 0}
            acf_vals = acf(series_clean, nlags=max_lags).tolist()
            pacf_vals = pacf(series_clean, nlags=max_lags, method='ywm').tolist()
            return {
                'acf_values': acf_vals,
                'pacf_values': pacf_vals,
                'nlags': max_lags
            }
        except Exception as e:
            return {
                'acf_values': [],
                'pacf_values': [],
                'nlags': 0,
                'error': str(e)
            }
