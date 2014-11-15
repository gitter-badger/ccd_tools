from NDimInv.plot_helper import *
import numpy as np
import sip_formats.convert as sip_convert


class plot_iteration():
    """
    This class defines an override function for the default plot function of
    the Iteration class. The new plot function is aware of the Debye
    Decomposition approach and will plot more information (i.e. the RTD)
    """
    def plot(self, it, filename, keep_plot=False):
        try:
            self._plot(it, filename, keep_plot)
        except Exception, e:
            print('Exception in plot routine', e)

    class figure_environment(object):
        def __init__(self, it, filename, keep_plot, nr_spectra):
            self.nr_spectra = nr_spectra
            self.filename = filename
            self.it = it
            self.keep_plot = keep_plot

        def __enter__(self):
            space_top = 1.2
            size_x = 12
            size_y = 2 * self.nr_spectra + space_top

            fig, axes = plt.subplots(self.nr_spectra, 5,
                                     figsize=(size_x, size_y))
            self.top_margin = (size_y - space_top) / float(size_y)
            axes = np.atleast_2d(axes)
            self.fig = fig
            self.axes = axes
            return fig, axes

        def __exit__(self, type, value, traceback):
            ax = self.axes[0, 0]
            title = 'Debye Decomposition, iteration {0}'.format(self.it.nr)
            ax.annotate(title, xy=(0.0, 1.00), xytext=(15, -30),
                        textcoords='offset points', xycoords='figure fraction')
            self.fig.tight_layout()
            self.fig.subplots_adjust(top=self.top_margin)
            self.fig.savefig(self.filename, dpi=150)
            if not self.keep_plot:
                # clean up
                self.fig.clf()
                plt.close(self.fig)
                del(self.fig)

    def _plot(self, it, filename, keep_plot):
        """Reimplementation of plot routines
        """
        # import pdb; pdb.set_trace()
        D = it.Data.D
        F = it.Model.F(it.m)
        M = it.Model.convert_to_M(it.m)
        nr_spectra = max(1, len(it.Data.extra_dims))

        with self.figure_environment(it, filename, keep_plot, nr_spectra) as\
                (fig, axes):
            # iterate over spectra
            for nr, (d, m) in enumerate(it.Model.DM_iterator()):
                self._plot_rre_rim(nr, axes[nr, 0:2], D[d], F[d], it)
                self._plot_rmag_rpha(nr, axes[nr, 2:4], D[d], F[d], it)
                self._plot_rtd(nr, axes[nr, 4], M[m], it)

    def _plot_rtd(self, nr,  ax, m, it):
        ax.semilogx(it.Data.obj.tau, m[1:], '.-', color='k')
        ax.set_xlim(it.Data.obj.tau.min(), it.Data.obj.tau.max())
        ax.xaxis.set_major_locator(mpl.ticker.LogLocator(numticks=5))
        ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(5))
        self._mark_tau_parameters_tau(nr, ax, it)
        ax.invert_xaxis()
        # mark limits of data frequencies, converted into the tau space
        tau_min = np.min(it.Model.obj.tau)
        tau_max = np.max(it.Model.obj.tau)
        d_fmin = np.min(it.Data.obj.frequencies)
        d_fmax = np.max(it.Data.obj.frequencies)
        t_fmin = 1 / (2 * np.pi * d_fmin)
        t_fmax = 1 / (2 * np.pi * d_fmax)
        ax.axvline(t_fmin, c='y', alpha=0.7)
        ax.axvline(t_fmax, c='y', alpha=0.7)
        ax.axvspan(tau_min, t_fmax, hatch='/', color='gray', alpha=0.5)
        ax.axvspan(t_fmin, tau_max, hatch='/', color='gray', alpha=0.5,
                   label='area outside data range')

        ax.set_xlabel(r'$\tau~[s]$')
        ax.set_ylabel(r'$log_{10}(m)$')

        # print lambda value in title
        title_string = r'$\lambda:$ '
        for lam in it.lams:
            if(type(lam) == list):
                lam = lam[0]
            if(isinstance(lam, float) or isinstance(lam, int)):
                title_string += '{0} '.format(lam)
            else:
                # individual lambdas
                title_string += '{0} '.format(
                    lam[m_indices[nr],  m_indices[nr]])
        ax.set_title(title_string)

    def _plot_rmag_rpha(self, nr, axes, orig_data, fit_data, it):
        rmag_rpha_orig = sip_convert.convert(it.Data.obj.data_format,
                                             'rmag_rpha',
                                             orig_data)

        rmag_rpha_fit = sip_convert.convert(it.Data.obj.data_format,
                                            'rmag_rpha',
                                            fit_data)

        frequencies = it.Data.obj.frequencies

        ax = axes[0]
        ax.semilogx(frequencies, rmag_rpha_orig[:, 0], '.', color='k')
        ax.semilogx(frequencies, rmag_rpha_fit[:, 0], '-', color='k')
        ax.set_xlabel('frequency [Hz]')
        ax.set_ylabel(r'$|\rho|~[\Omega m]$')
        ax.xaxis.set_major_locator(mpl.ticker.LogLocator(numticks=4))
        ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(5))

        ax = axes[1]
        ax.semilogx(frequencies, -rmag_rpha_orig[:, 1], '.', color='k')
        ax.semilogx(frequencies, -rmag_rpha_fit[:, 1], '-', color='k')
        ax.set_xlabel('frequency [Hz]')
        ax.set_ylabel(r'$-\phi~[mrad]$')
        ax.xaxis.set_major_locator(mpl.ticker.LogLocator(numticks=4))
        ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(5))
        self._mark_tau_parameters_f(nr, ax, it)

    def _plot_rre_rim(self, nr, axes, orig_data, fit_data, it):
        rre_rim_orig = sip_convert.convert(it.Data.obj.data_format,
                                           'rre_rim',
                                           orig_data)

        rre_rim_fit = sip_convert.convert(it.Data.obj.data_format,
                                          'rre_rim',
                                          fit_data)
        frequencies = it.Data.obj.frequencies
        ax = axes[0]
        ax.semilogx(frequencies, rre_rim_orig[:, 0], '.', color='k')
        ax.semilogx(frequencies, rre_rim_fit[:, 0], '-', color='k')
        ax.set_xlabel('frequency [Hz]')
        ax.set_ylabel(r"$-\rho'~[\Omega m]$")
        ax.xaxis.set_major_locator(mpl.ticker.LogLocator(numticks=4))

        ax = axes[1]
        ax.semilogx(frequencies, -rre_rim_orig[:, 1], '.', color='k',
                    label='data')
        ax.semilogx(frequencies, -rre_rim_fit[:, 1], '-', color='k',
                    label='fit')
        ax.set_xlabel('frequency [Hz]')
        ax.set_ylabel(r"$-\rho''~[\Omega m]$")
        ax.xaxis.set_major_locator(mpl.ticker.LogLocator(numticks=4))

        self._mark_tau_parameters_f(nr, ax, it)

        # legend is created from first plot
        if nr == 0:
            ax.legend(loc="upper center", ncol=5,
                      bbox_to_anchor=(0, 0, 1, 1),
                      bbox_transform=ax.get_figure().transFigure)
            leg = ax.get_legend()
            ltext = leg.get_texts()
            plt.setp(ltext, fontsize='6')

    def _mark_tau_parameters_tau(self, nr, ax, it):
        # mark relaxation time parameters
        # mark tau_peak
        for index in range(1, 3):
            try:
                tpeak = it.stat_pars['tau_peak{0}'.format(index)][nr]
                if(not np.isnan(tpeak)):
                    ax.axvline(x=10**tpeak, color='k', label=r'$\tau_{peak}^' +
                               '{0}'.format(index) + '$',
                               linestyle='dashed')
            except:
                pass

        try:
            ax.axvline(x=10**it.stat_pars['tau_50'][nr], color='g',
                       label=r'$\tau_{50}$')
        except:
            pass

        try:
            ax.axvline(x=10**it.stat_pars['tau_mean'][nr], color='c',
                       label=r'$\tau_{mean}$')
        except:
            pass

    def _mark_tau_parameters_f(self, nr, ax, it):
        # mark relaxation time parameters
        # mark tau_peak
        for index in range(1, 3):
            try:
                fpeak = it.stat_pars['f_peak{0}'.format(index)][nr]
                if(not np.isnan(fpeak)):
                    ax.axvline(x=fpeak, color='k', label=r'$\tau_{peak}^' +
                               '{0}'.format(index) + '$',
                               linestyle='dashed')
            except:
                pass

        try:
            ax.axvline(x=it.stat_pars['f_50'][nr], color='g',
                       label=r'$\tau_{50}$')
        except:
            pass

        try:
            ax.axvline(x=it.stat_pars['f_mean'][nr], color='c',
                       label=r'$\tau_{mean}$')
        except:
            pass
