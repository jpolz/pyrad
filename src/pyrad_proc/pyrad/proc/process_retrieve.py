"""
pyrad.proc.process_retrieve
===========================

Functions for retrieving new moments and products

.. autosummary::
    :toctree: generated/

    process_signal_power
    process_snr
    process_l
    process_cdr
    process_rainrate

"""

from copy import deepcopy
from warnings import warn

import numpy as np

import pyart

from ..io.io_aux import get_datatype_fields, get_fieldname_pyart


def process_signal_power(procstatus, dscfg, radar=None):
    """
    Computes the signal power in dBm

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing

    dscfg : dictionary of dictionaries
        data set configuration. Accepted Configuration Keywords::

        datatype : list of string. Dataset keyword
            The input data types
        mflossv : float. Global keyword
            The matching filter losses of the vertical channel. Used if input
            is vertical reflectivity
        radconstv : float. Global keyword
            The vertical channel radar constant. Used if input is vertical
            reflectivity
        mflossh : float. Global keyword
            The matching filter losses of the vertical channel. Used if input
            is horizontal reflectivity
        radconsth : float. Global keyword
            The horizontal channel radar constant. Used if input is horizontal
            reflectivity
        attg : float. Dataset keyword
            The gas attenuation

    radar : Radar
        Optional. Radar object

    Returns
    -------
    new_dataset : Radar
        radar object

    """

    if procstatus != 1:
        return None

    for datatypedescr in dscfg['datatype']:
        datagroup, datatype, dataset, product = get_datatype_fields(
            datatypedescr)
        if datatype == 'dBZ':
            refl_field = 'reflectivity'
        if datatype == 'dBuZ':
            refl_field = 'unfiltered_reflectivity'
        if datatype == 'dBZc':
            refl_field = 'corrected_reflectivity'
        if datatype == 'dBuZc':
            refl_field = 'corrected_unfiltered_reflectivity'
        if datatype == 'dBZv':
            refl_field = 'reflectivity_vv'
        if datatype == 'dBuZv':
            refl_field = 'unfiltered_reflectivity_vv'
        if datatype == 'dBuZvc':
            refl_field = 'corrected_unfiltered_reflectivity_vv'

    if refl_field not in radar.fields:
        warn('Unable to obtain signal power. Missing field '+refl_field)
        return None

    if refl_field.endswith('_vv'):
        pwr_field = 'signal_power_vv'

        lmf = None
        if 'mflossv' in dscfg:
            lmf = dscfg['mflossv']

        radconst = None
        if 'radconstv' in dscfg:
            radconst = dscfg['radconstv']
    else:
        pwr_field = 'signal_power_hh'

        lmf = None
        if 'mflossh' in dscfg:
            lmf = dscfg['mflossh']

        radconst = None
        if 'radconsth' in dscfg:
            radconst = dscfg['radconsth']

    attg = None
    if 'attg' in dscfg:
        attg = dscfg['attg']

    s_pwr = pyart.retrieve.compute_signal_power(
        radar, lmf=lmf, attg=attg, radconst=radconst, refl_field=refl_field,
        pwr_field=pwr_field)

    # prepare for exit
    new_dataset = deepcopy(radar)
    new_dataset.fields = dict()
    new_dataset.add_field(pwr_field, s_pwr)

    return new_dataset


def process_snr(procstatus, dscfg, radar=None):
    """
    Computes SNR

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing

    dscfg : dictionary of dictionaries
        data set configuration. Accepted Configuration Keywords::

        datatype : string. Dataset keyword
            The input data type
        output_type : string. Dataset keyword
            The output data type. Either SNRh or SNRv

    radar : Radar
        Optional. Radar object

    Returns
    -------
    new_dataset : Radar
        radar object

    """

    if procstatus != 1:
        return None

    for datatypedescr in dscfg['datatype']:
        datagroup, datatype, dataset, product = get_datatype_fields(
            datatypedescr)
        if datatype == 'dBZ':
            refl = 'reflectivity'
        if datatype == 'dBuZ':
            refl = 'unfiltered_reflectivity'
        if datatype == 'dBZv':
            refl = 'reflectivity_vv'
        if datatype == 'dBuZv':
            refl = 'unfiltered_reflectivity_vv'
        if datatype == 'Nh':
            noise = 'noisedBZ_hh'
        if datatype == 'Nv':
            noise = 'noisedBZ_vv'

    if (refl not in radar.fields) or (noise not in radar.fields):
        warn('Unable to compute SNR. Missing data')
        return None

    if 'output_type' in dscfg:
        if dscfg['output_type'] == 'SNRh':
            snr_field = 'signal_to_noise_ratio_hh'
        elif dscfg['output_type'] == 'SNRv':
            snr_field = 'signal_to_noise_ratio_vv'
    else:
        snr_field = 'signal_to_noise_ratio_hh'

    snr = pyart.retrieve.compute_snr(
        radar, refl_field=refl, noise_field=noise,
        snr_field=snr_field)

    # prepare for exit
    new_dataset = deepcopy(radar)
    new_dataset.fields = dict()
    new_dataset.add_field(snr_field, snr)

    return new_dataset


def process_l(procstatus, dscfg, radar=None):
    """
    Computes L parameter

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing

    dscfg : dictionary of dictionaries
        data set configuration. Accepted Configuration Keywords::

        datatype : string. Dataset keyword
            The input data type

    radar : Radar
        Optional. Radar object

    Returns
    -------
    new_dataset : Radar
        radar object

    """

    if procstatus != 1:
        return None

    datagroup, datatype, dataset, product = get_datatype_fields(
        dscfg['datatype'])
    rhohv = get_fieldname_pyart(datatype)

    if rhohv not in radar.fields:
        print('Unable to compute L. Missing RhoHV field')
        return None

    l = pyart.retrieve.compute_l(
        radar, rhohv_field=rhohv,
        l_field='logarithmic_cross_correlation_ratio')

    # prepare for exit
    new_dataset = deepcopy(radar)
    new_dataset.fields = dict()
    new_dataset.add_field('logarithmic_cross_correlation_ratio', l)

    return new_dataset


def process_cdr(procstatus, dscfg, radar=None):
    """
    Computes Circular Depolarization Ratio

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing

    dscfg : dictionary of dictionaries
        data set configuration. Accepted Configuration Keywords::

        datatype : string. Dataset keyword
            The input data type

    radar : Radar
        Optional. Radar object

    Returns
    -------
    new_dataset : Radar
        radar object

    """

    if procstatus != 1:
        return None

    for datatypedescr in dscfg['datatype']:
        datagroup, datatype, dataset, product = get_datatype_fields(
            datatypedescr)
        if datatype == 'RhoHV':
            rhohv = 'cross_correlation_ratio'
        if datatype == 'uRhoHV':
            rhohv = 'uncorrected_cross_correlation_ratio'
        if datatype == 'RhoHVu':
            rhohv = 'unfiltered_cross_correlation_ratio'
        if datatype == 'ZDR':
            zdr = 'differential_reflectivity'
        if datatype == 'ZDRc':
            zdr = 'corrected_differential_reflectivity'

    if ((rhohv not in radar.fields) or
            (zdr not in radar.fields)):
        warn('Unable to compute CDR field. Missing data')
        return None

    cdr = pyart.retrieve.compute_cdr(
        radar, rhohv_field=rhohv, zdr_field=zdr,
        cdr_field='circular_depolarization_ratio')

    # prepare for exit
    new_dataset = deepcopy(radar)
    new_dataset.fields = dict()
    new_dataset.add_field('circular_depolarization_ratio', cdr)

    return new_dataset


def process_rainrate(procstatus, dscfg, radar=None):
    """
    Estimates rainfall rate from polarimetric moments

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing

    dscfg : dictionary of dictionaries
        data set configuration. Accepted Configuration Keywords::

        datatype : string. Dataset keyword
            The input data type
        RR_METHOD : string. Dataset keyword
            The rainfall rate estimation method. One of the following:
            Z, ZPoly, KDP, A, ZKDP, ZA, hydro

    radar : Radar
        Optional. Radar object

    Returns
    -------
    radar : Radar
        radar object

    """
    if procstatus != 1:
        return None

    if dscfg['RR_METHOD'] == 'Z':
        datagroup, datatype, dataset, product = get_datatype_fields(
            dscfg['datatype'][0])
        refl_field = get_fieldname_pyart(datatype)

        if refl_field not in radar.fields:
            warn('Unable to compute rainfall rate. Missing data')
            return None

        rain = pyart.retrieve.est_rain_rate_z(
            radar, alpha=0.0376, beta=0.6112, refl_field=refl_field,
            rr_field=None)

    elif dscfg['RR_METHOD'] == 'ZPoly':
        datagroup, datatype, dataset, product = get_datatype_fields(
            dscfg['datatype'][0])
        refl_field = get_fieldname_pyart(datatype)

        if refl_field not in radar.fields:
            warn('Unable to compute rainfall rate. Missing data')
            return None

        rain = pyart.retrieve.est_rain_rate_zpoly(
            radar, refl_field=refl_field, rr_field=None)

    elif dscfg['RR_METHOD'] == 'KDP':
        datagroup, datatype, dataset, product = get_datatype_fields(
            dscfg['datatype'][0])
        kdp_field = get_fieldname_pyart(datatype)

        if kdp_field not in radar.fields:
            warn('Unable to compute rainfall rate. Missing data')
            return None

        rain = pyart.retrieve.est_rain_rate_kdp(
            radar, alpha=None, beta=None, kdp_field=kdp_field, rr_field=None)

    elif dscfg['RR_METHOD'] == 'A':
        datagroup, datatype, dataset, product = get_datatype_fields(
            dscfg['datatype'][0])
        a_field = get_fieldname_pyart(datatype)

        if a_field not in radar.fields:
            warn('Unable to compute rainfall rate. Missing data')
            return None

        rain = pyart.retrieve.est_rain_rate_a(
            radar, alpha=None, beta=None, a_field=a_field, rr_field=None)

    elif dscfg['RR_METHOD'] == 'ZKDP':
        for datatypedescr in dscfg['datatype']:
            datagroup, datatype, dataset, product = get_datatype_fields(
                datatypedescr)
            if datatype == 'dBZc':
                refl_field = 'corrected_reflectivity'
            if datatype == 'KDPc':
                kdp_field = 'corrected_specific_differential_phase'
            if datatype == 'dBZ':
                refl_field = 'reflectivity'
            if datatype == 'KDP':
                kdp_field = 'specific_differential_phase'

        if ((refl_field not in radar.fields) or
                (kdp_field not in radar.fields)):
            warn('Unable to compute rainfall rate. Missing data')
            return None

        rain = pyart.retrieve.est_rain_rate_zkdp(
            radar, alphaz=0.0376, betaz=0.6112, alphakdp=None, betakdp=None,
            refl_field=refl_field, kdp_field=kdp_field, rr_field=None,
            master_field=refl_field, thresh=10., thresh_max=True)

    elif dscfg['RR_METHOD'] == 'ZA':
        for datatypedescr in dscfg['datatype']:
            datagroup, datatype, dataset, product = get_datatype_fields(
                datatypedescr)
            if datatype == 'dBZc':
                refl_field = 'corrected_reflectivity'
            if datatype == 'Ahc':
                a_field = 'corrected_specific_attenuation'
            if datatype == 'dBZ':
                refl_field = 'reflectivity'
            if datatype == 'Ah':
                a_field = 'specific_attenuation'

        if ((refl_field not in radar.fields) or
                (a_field not in radar.fields)):
            warn('Unable to compute rainfall rate. Missing data')
            return None

        rain = pyart.retrieve.est_rain_rate_za(
            radar, alphaz=0.0376, betaz=0.6112, alphaa=None, betaa=None,
            refl_field=refl_field, a_field=a_field, rr_field=None,
            master_field=refl_field, thresh=0.04, thresh_max=False)

    elif dscfg['RR_METHOD'] == 'hydro':
        for datatypedescr in dscfg['datatype']:
            datagroup, datatype, dataset, product = get_datatype_fields(
                datatypedescr)
            if datatype == 'dBZc':
                refl_field = 'corrected_reflectivity'
            if datatype == 'Ahc':
                a_field = 'corrected_specific_attenuation'
            if datatype == 'hydro':
                hydro_field = 'radar_echo_classification'
            if datatype == 'dBZ':
                refl_field = 'reflectivity'
            if datatype == 'Ah':
                a_field = 'specific_attenuation'

        if ((refl_field not in radar.fields) or
                (a_field not in radar.fields) or
                (hydro_field not in radar.fields)):
            warn('Unable to compute rainfall rate. Missing data')
            return None

        rain = pyart.retrieve.est_rain_rate_hydro(
            radar, alphazr=0.0376, betazr=0.6112, alphazs=0.1, betazs=0.5,
            alphaa=None, betaa=None, mp_factor=0.6, refl_field=refl_field,
            a_field=a_field, hydro_field=hydro_field, rr_field=None,
            master_field=refl_field, thresh=0.04, thresh_max=False)

    # prepare for exit
    new_dataset = deepcopy(radar)
    new_dataset.fields = dict()
    new_dataset.add_field('radar_estimated_rain_rate', rain)

    return new_dataset