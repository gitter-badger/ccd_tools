from NDimInv.plot_helper import *
import numpy as np
import sip_formats.convert as sip_convert


class plot_iteration():
    """
    This class defines an override function for the default plot function of
    the Iteration class. The new plot function is aware of the Debye
    Decomposition approach and will plot more information (i.e. the RTD)
    """
    def plot(self, it, filename):
        try:
            self._plot(it, filename)
        except Exception, e:
            print('Exception in plot routine', e)

    def _plot(self, it, filename):
        """
        rre  rmim
        m
        """
        # nr of parameters (nr of tau values + 1 for rho0)
        step_size = it.Model.M_base_dims[0][1]
        m_indices = range(0, it.m.size, step_size)

        d = it.Data.Df
        response = it.Model.f(it.m)
        nr_f = len(it.Data.obj.frequencies)
        nr_spectra = response.size / 2 / nr_f

        # split data
        slices = []
        resp = []
        for i in range(0, d.size, nr_f):
            slices.append(d[i:i + nr_f])
            resp.append(response[i:i + nr_f])

        space_top = 1.2
        size_x = 12
        size_y = 2 * nr_spectra + space_top  # + 2 inches for title and legend

        fig, axes = plt.subplots(nr_spectra, 5, figsize=(size_x, size_y))
        top_margin = (size_y - space_top) / float(size_y)
        axes = np.atleast_2d(axes)

        frequencies = it.Data.obj.frequencies

        # loop over spectra
        for nr, i in enumerate(range(0, nr_spectra * 2, 2)):
            # part 1
            ax = axes[nr, 0]
            ax.semilogx(frequencies, slices[i], '.',
                        markeredgewidth=3.0)
            ax.semilogx(frequencies, resp[i], '-', c='r',
                        alpha=0.7)
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel(r"$\rho'~(\Omega m)$")

            # part 2
            ax = axes[nr, 1]
            ax.semilogx(frequencies, slices[i + 1], '.-',
                        markeredgewidth=3.0, label='data')
            ax.semilogx(frequencies, resp[i + 1], '-', c='r',
                        alpha=0.7, label='fit')
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel(r"$-\rho''~(\Omega m)$")

            # mark relaxation time parameters
            # mark tau_peak
            for index in range(1, 3):
                fpeak = it.stat_pars['f_peak{0}'.format(index)][nr]
                if(not np.isnan(fpeak)):
                    ax.axvline(x=fpeak, color='k', label=r'$\tau_{peak}$')

            ax.axvline(x=it.stat_pars['f_50'][nr], color='g',
                       label=r'$\tau_{50}$')
            ax.axvline(x=it.stat_pars['f_mean'][nr], color='c',
                       label=r'$\tau_{mean}$')

            # legend is created from first plot
            if(nr == 0):
                ax.legend(loc="upper center", ncol=5,
                          # bbox_to_anchor=(0, 0, 1, 0.95),
                          bbox_to_anchor=(0, 0, 1, 1),
                          bbox_transform=fig.transFigure)
                leg = ax.get_legend()
                ltext = leg.get_texts()
                plt.setp(ltext, fontsize='6')

            # rmag
            ax = axes[nr, 2]
            subdata = np.vstack(slices[i: i + 2]).flatten()
            rmag_rpha = sip_convert.convert(it.Model.obj.data_format,
                                            'rmag_rpha', subdata)
            rmag, rpha = sip_convert.split_data(rmag_rpha)

            ax.semilogx(it.Data.obj.frequencies, rmag.flatten(), '.')
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel(r'$|\rho|~(\Omega m)$')

            # rpha
            ax = axes[nr, 3]
            ax.semilogx(it.Data.obj.frequencies, -rpha.flatten(), '.')
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel(r'$-\phi~(mrad)$')

            # RTD (m distribution)
            ax = axes[nr, 4]
            title_string = ''
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
            # ax.set_title('lams: {0}'.format(it.lams))
            m_distribution = it.m[m_indices[nr]: m_indices[nr] + step_size][1:]
            ax.semilogx(it.Model.obj.tau, m_distribution, '.-')
            ax.xaxis.set_major_locator(mpl.ticker.LogLocator(5))
            ax.set_xlabel(r'$\tau$')
            ax.set_ylabel(r'$m(\tau)$')
            tau_min = np.min(it.Model.obj.tau)
            tau_max = np.max(it.Model.obj.tau)
            ax.set_xlim((tau_min, tau_max))
            # reverse tau direction for simple comparison to frequencies
            ax.invert_xaxis()
            # mark limits of data frequencies, converted into the tau space
            d_fmin = np.min(it.Data.obj.frequencies)
            d_fmax = np.max(it.Data.obj.frequencies)
            t_fmin = 1 / (2 * np.pi * d_fmin)
            t_fmax = 1 / (2 * np.pi * d_fmax)
            ax.axvline(t_fmin, c='y', alpha=0.7)
            ax.axvline(t_fmax, c='y', alpha=0.7)
            ax.axvspan(tau_min, t_fmax, hatch='/', color='gray', alpha=0.5)
            ax.axvspan(t_fmin, tau_max, hatch='/', color='gray', alpha=0.5)

            # mark relaxation time paramters
            for index in range(1, 3):
                tpeak = it.stat_pars['tau_peak{0}'.format(index)][nr]
                if(not np.isnan(tpeak)):
                    ax.axvline(x=10**tpeak, color='k', label=r'$\tau_{peak}$')

        for ax in axes.flatten():
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontsize(7)

        fig.suptitle('Debye Decomposition, iteration {0}'.format(it.nr))
        fig.tight_layout()
        fig.subplots_adjust(top=top_margin)
        fig.savefig(filename, dpi=150)
        fig.clf()
        del(fig)

        # import pdb
        # pdb.set_trace()
        # # debug plot: cumsgtau
        # filename += '_cumgtau.png'
        # fig, ax = plt.subplots(1, 1)
        # s_f = 1 / (2 * np.pi * 10 ** it.Model.obj.s_crop)
        # ax.semilogx(s_f, it.stat_pars['cums_gtau'][0], '.-')
        # ax.axhline(y=0.5)
        # ax.axvline(it.stat_pars['f_50'], color='r')
        # ax.set_ylabel('Cumulative m-sum')
        # ax.set_xlabel('Frequency')
        # fig.savefig(filename, dpi=150)