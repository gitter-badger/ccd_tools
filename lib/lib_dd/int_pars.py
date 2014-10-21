"""
Integrated parameters

pars: linear representation of parameters
"""
import os
import numpy as np
import scipy.signal as sp


def _rho0_linear(pars, tau, s):
    return pars[0]


def rho0(pars, tau, s):
    return np.log10(_rho0_linear(pars, tau, s))


def m_data(pars, tau, s):
    return np.log10(pars[1:])


def _m_tot_linear(pars, tau, s):
    m_tot_linear = np.nansum(pars[1:])
    return m_tot_linear


def m_tot(pars, tau, s):
    return np.log10(_m_tot_linear(pars, tau, s))


def _m_tot_n_linear(pars, tau, s):
    m_tot_n = _m_tot_linear(pars, tau, s) / _rho0_linear(pars, tau, s)
    return m_tot_n


def m_tot_n(pars, tau, s):
    m_tot_n = np.log10(_m_tot_n_linear(pars, tau, s))
    return m_tot_n


def tau_mean(pars, tau, s):
    # tau_mean in log10
    try:
        tau_mean = np.nansum(s * pars[1:]) / (_m_tot_linear(pars, tau, s))
        f_mean = 1 / (2 * np.pi * 10**tau_mean)
    except Exception:
        tau_mean = np.nan
        f_mean = np.nan
    return {'tau_mean': tau_mean, 'f_mean': f_mean}


def tau_arithmetic(pars, tau, s):
    try:
        tau_arithmetic = np.nansum(tau * pars[1:]) / (
            _m_tot_linear(pars, tau, s))
        f_arithmetic = 1 / (2 * np.pi * 10**tau_arithmetic)
    except Exception:
        tau_arithmetic = np.nan
        f_arithmetic = np.nan
    return {'tau_arithmetic': tau_arithmetic, 'f_arithmetic': f_arithmetic}


def tau_geometric(pars, tau, s):
    try:
        tau_geometric = np.prod(tau**pars[1:])**(
            1 / _m_tot_linear(pars, tau, s))
        np.nansum(tau * pars[1:]) / (_m_tot_linear(pars, tau, s))
        f_geometric = 1 / (2 * np.pi * 10**tau_geometric)
    except Exception:
        tau_geometric = np.nan
        f_geometric = np.nan
    return {'tau_geometric': tau_geometric, 'f_geometric': f_geometric}


def _cumulative_tau(pars, tau, s):
    g_tau = pars[1:] / _m_tot_linear(pars, tau, s)
    cums_gtau = np.cumsum(g_tau)

    # remove extra ranges
    # g_tau = g_tau[~np.isnan(g_tau)]
    # cums_gtau = np.repeat(np.nan, s.size)
    return cums_gtau


def _tau_x(x, pars, tau, s):
    """
    Compute the relaxation time corresponding to a certain percentage of the
    cumulative chargeabilities

    x: fraction between 0.0 - 1.0
    """
    try:
        cums_gtau = _cumulative_tau(pars, tau, s)

        # 0.5 ?
        index_median = np.argmin(np.abs(cums_gtau - x))
        if(np.isnan(index_median)):
            tau_x = np.nan
            f_x = np.nan
        else:
            tau_x = s[index_median]
            f_x = 1 / (2 * np.pi * 10**tau_x)
    except Exception:
        # cums_gtau = np.repeat(np.nan, s.size)
        tau_x = np.nan
        f_x = np.nan

    return tau_x, f_x


def tau_x(pars, tau, s):
    r"""
    Arbitrary cumultative :math:`\tau_x` values can be computed using the
    environment variable DD_TAU_X: The string separates the requested
    percentages as fractions with ';' characters.

    Example:

        DD_TAU_X="0.2;0.35;0.6"
    """
    if('DD_TAU_X' not in os.environ):
        return {}
    else:
        results = {}
        items = os.environ['DD_TAU_X'].split(';')
        for x in items:
            tau_x, f_x = _tau_x(float(x), pars, tau, s)
            results['tau_x_{0}'.format(float(x)*100)] = tau_x
            results['f_x_{0}'.format(float(x)*100)] = f_x
    return results


def tau_50(pars, tau, s):
    tau_50, f_50 = _tau_x(0.5, pars, tau, s)
    results = {'tau_50': tau_50, 'f_50': f_50}
    return results


def U_tau(pars, tau, s):
    """compute uniformity parameter similar to Nordsiek and Weller, 2008:
        :math:`U_{\tau} = \frac{\tau_{10}}{\tau_{60}}
    """
    tau_10, f_10 = _tau_x(0.1, pars, tau, s)
    tau_60, f_60 = _tau_x(0.6, pars, tau, s)
    u_tau = tau_10 / tau_60
    return u_tau


def tau_max(pars, tau, s):
    index_max = np.argmax(tau)
    if(index_max.size == 0):
        return {'tau_max': np.nan, 'f_max': np.nan}
    else:
        return {'tau_max': s[index_max],
                'f_max': 1 / (2 * np.pi * tau[index_max])}


def _get_peaks(pars, s):
    """
    Return the peaks in the relaxation time distribution.

    Parameters
    ----------
    pars: parameter values corresponding to the rel. times in s (+ rho0 on first
          index)
    s : log10 relaxation times

    Returns
    -------
    s_peaks : log10 rel. times corresponding to the peaks
    tau_peaks : linear representations of rel. times
    f_peaks : frequencies corresponding to the peak rel. times

    """
    # compute m-distribution maxima
    m_maxima = sp.argrelmax(pars[1:])[0]

    # reverse so the low-frequency peaks come first
    m_maxima = [x for x in reversed(m_maxima)]

    s_peaks = s[m_maxima]

    # not sure if this should not be left linear
    tau_peaks = 10 ** s_peaks
    f_peaks = 1 / (2 * np.pi * tau_peaks)

    return s_peaks, tau_peaks, f_peaks


def decade_loadings(pars, tau, s):
    r"""Compute the chargeability sum for each frequency decade.
    """
    f_tau = 1 / (2 * np.pi * tau)

    # get min/max of frequencies, rounded to lower/higher decade
    min_f = np.floor(np.log10(f_tau).min())
    max_f = np.ceil(np.log10(f_tau).max())

    # generate bins
    bins = np.logspace(min_f, max_f, (max_f - min_f) + 1)
    bin_indices = np.digitize(f_tau, bins)

    loadings_abs = []
    for i in set(bin_indices):
        indices = np.where(bin_indices == i)[0]
        loadings_abs.append(np.sum(pars[indices]))
    loadings = np.array(loadings_abs) / _m_tot_linear(pars, tau, s)
    results = {}
    results['decade_loadings'] = loadings
    results['decade_bins'] = bins
    return results


def tau_peaks(pars, tau, s):
    results = {}

    # tau peaks (we store in log10)
    try:
        s_peaks, tau_peaks, f_peaks = _get_peaks(pars, s)

        # save peaks and corresponding frequencies
        for nr in range(1, 3):
            key = '_peak{0}'.format(nr)
            if(len(tau_peaks) >= nr):
                results['tau' + key] = s_peaks[nr - 1]
                results['f' + key] = f_peaks[nr - 1]
            else:
                results['tau' + key] = np.nan
                results['f' + key] = np.nan

        # we also want to save all peaks in one file
        results['tau_peaks_all'] = s_peaks
        results['f_peaks_all'] = f_peaks
    except Exception:
        # print ('Error computing tau_peaks: ', e)
        for nr in range(1, 3):
            key = '_peak{0}'.format(nr)
            results['tau' + key] = np.nan
            results['f' + key] = np.nan
    return results