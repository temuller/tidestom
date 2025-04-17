import numpy as np
import pandas as pd
from astropy.time import Time
import plotly.graph_objects as go

def get_hovertemplates(df: pd.DataFrame, columns: list) -> str:
    """Creates the hover template to show information when hovering 
    over the data.

    Parameters
    ----------
    df: light-curves information.
    columns: columns used for displaying the information (e.g. mag, MJD).

    Returns
    -------
    hovertemplate: hover information.
    """
    df_columns = df.columns.to_list()
    hovertemplate = "".join(f"{col}: %{{customdata[{df_columns.index(col)}]}}<br>" 
                            for col in columns)
    return hovertemplate
    
def photometry_trace(df: pd.DataFrame, colour: str, phot_type: str='mag', name: str=None, hovertemplate: str=None) -> go.Scatter:
    """Creates a trace to display the light curve photometry.

    Parameters
    ----------
    df: light-curves information.
    colour: colour for plotting.
    phot_type: column to use in the y axis.
    name: name to identify the trace.
    hovertemplate: hover information to display.

    Returns
    -------
    trace: light-curve trace.
    """
    trace = go.Scatter(x=df['mjd'],
                       y=df[phot_type],
                       mode='markers',
                       name=name,
                       marker=dict(color=colour),
                       customdata=df,
                       hovertemplate=hovertemplate,
                       legendgroup=name,  # group markers and error bars together
                      ) 
    return trace
    
def error_trace(df: pd.DataFrame, colour: str, phot_type: str='mag', name: str=None) -> go.Scatter:
    """Creates a trace to display the light curve photometry uncertainty.

    Parameters
    ----------
    df: light-curves information.
    colour: colour for plotting.
    phot_type: column to use in the y axis.
    name: name to identify the trace.

    Returns
    -------
    trace: light-curve error trace.
    """
    trace = go.Scatter(x=df['mjd'],
                       y=df[phot_type],
                       mode='lines',
                       name=name,
                       line=dict(width=0),  # Invisible line for error bars
                       error_y=dict(type='data',
                                    symmetric=True,
                                    array=df[f'{phot_type}_err'],
                                    color=colour
                                   ),
                       showlegend=False,
                       legendgroup=name
                      )
    return trace

def upperlimit_trace(df: pd.DataFrame, colour: str, phot_type: str='mag', name: str=None, hovertemplate: str=None) -> go.Scatter:
    """Creates a trace to display the light curve photometry upper limits.

    Parameters
    ----------
    df: light-curves information.
    colour: colour for plotting.
    phot_type: column to use in the y axis.
    name: name to identify the trace.
    hovertemplate: hover information to display.

    Returns
    -------
    trace: light-curve upper-limits trace.
    """
    trace = go.Scatter(x=df['mjd'],
                       y=df[f"upper_{phot_type}"],
                       mode='markers',
                       name=name,
                       marker_symbol="triangle-down-open",
                       marker_size=12,
                       marker=dict(color=colour),
                       opacity=0.7,
                       customdata=df,
                       hovertemplate=hovertemplate,
                       showlegend=False,
                       legendgroup=name,
                      )
    return trace

def create_toggling_buttons(fig: go.Figure) -> list[dict, dict]:
    """Creates the buttons for toggling between magnitude and flux.

    Parameters
    ----------
    fig.: plotly figure.

    Returns
    -------
    buttons: magnitude/flux buttons.
    """
    mag_visibility = [False if "flux" in trace.name else True for trace in fig.data]
    flux_visibility = [False if "mag" in trace.name else True for trace in fig.data]
    
    buttons = [
        dict(
            label='Magnitude',
            method='update',
            args=[
                {'visible': mag_visibility},  # Show magnitude, hide flux
                {'yaxis': {'title': 'AB Magnitude', 'autorange': 'reversed'}},
            ]
        ),
        dict(
            label='Flux',
            method='update',
            args=[
                {'visible': flux_visibility},  # Show flux, hide magnitude
                {'yaxis': {'title': 'Flux (μJy)'}},
            ]
        )
    ]
    return buttons

def plot_lightcurves(photometry: pd.DataFrame) -> go.Figure:
    """Plots the light curves for a transient.

    Parameter
    ---------
    photometry: transient dataframe with photometry.

    Returns
    -------
    fig: plot figure.
    """
    colour_dict = {"ztf_g":"green", "ztf_r":"red", "ztf_i":"gold",
                   "gaia_G":"purple",
                   "atlas_c":"cyan", "atlas_o":"orange",
                   "neowise_W1":"navy", "neowise_W2":"darkred", 
                   "neowise_W3":"indigo", "neowise_W4":"darkslategrey",
                   "tess":"black",
                   "goto_L":"purple",
                   "ps1_g":"green", "ps1_r":"red", "ps1_i":"gold",
                   "clear(VegaMag)":"skyblue",
                  }

    # add columns
    zp = 23.9  # to get flux in micro jansky
    photometry["flux"] = 10 ** (-0.4 * (photometry.mag.values - zp))
    photometry["flux_err"] = np.abs(photometry.flux.values * 0.4 * np.log(10) * photometry.mag_err.values)
    photometry["upper_flux"] = 10 ** (-0.4 * (photometry.upper_mag.values - zp))
    photometry["iso"] = Time(photometry.mjd.values, format="mjd").iso
    photometry["date"] = photometry.iso.str.split().str[0]
    
    # update decimal precision
    for col in photometry.columns:
        if photometry[col].dtype == float:
            photometry[col] = photometry[col].apply(lambda x: np.round(x, 3))
    
    ########################
    # Initialize the figure
    fig = go.Figure()
    
    # Add traces for each filter
    for i, (filt, colour) in enumerate(colour_dict.items()):
        filt_df = photometry[photometry["filt"]==filt]
        # split detections and non-detections
        det_mask = ~filt_df.mag.isna()
        det_df = filt_df[det_mask]
        nondet_df = filt_df[~det_mask]
    
        # hover templates
        hovertemp_mag = get_hovertemplates(det_df, columns=["filt", "date", "mjd", "mag", "mag_err"])
        hovertemp_flux = get_hovertemplates(filt_df, columns=["filt", "date", "mjd", "flux", "flux_err"])
        hovertemp_uppermag = get_hovertemplates(nondet_df, columns=["filt", "date", "mjd", "upper_mag"])
        hovertemp_upperflux = get_hovertemplates(nondet_df, columns=["filt", "date", "mjd", "upper_flux"])
        
        # photometry
        mag_trace = photometry_trace(det_df, colour, phot_type='mag', name=f"{filt}_mag", hovertemplate=hovertemp_mag)  
        flux_trace = photometry_trace(det_df, colour, phot_type='flux', name=f"{filt}_flux", hovertemplate=hovertemp_flux)  
        # non detections 
        uppermag_trace = upperlimit_trace(nondet_df, colour, phot_type='mag', name=f"{filt}_mag", hovertemplate=hovertemp_uppermag)
        upperflux_trace = upperlimit_trace(nondet_df, colour, phot_type='flux', name=f"{filt}_flux", hovertemplate=hovertemp_upperflux)
    
        # error bars
        # "name" needs to match the photometry so their legends are connected
        magerr_trace = error_trace(det_df, colour, phot_type='mag', name=f"{filt}_mag")
        fluxerr_trace = error_trace(det_df, colour, phot_type='flux', name=f"{filt}_flux")
        
        fig.add_trace(mag_trace)
        fig.add_trace(magerr_trace)
        fig.add_trace(uppermag_trace)
        fig.add_trace(flux_trace)
        fig.add_trace(fluxerr_trace)
        fig.add_trace(upperflux_trace)  # no associated errors at the moment
     
    # assign initial visibility of the traces
    for trace in fig.data:
        if "flux" in trace.name:
            trace.visible = False
        else:
            trace.visible = True
            
    # discovery date
    #fig.add_vline(obj.discovery_time_mjd, line_width=2, line_dash="solid", line_color="black", 
    #                  annotation_text="disc.", annotation_position="bottom left")
    # spectra dates
    #for spec_mjd in obj.spec_df['mjd'].values:
    #    fig.add_vline(spec_mjd, line_width=2, line_dash="dot", line_color="black", 
    #                  annotation_text="s", annotation_position="top left")
        
    # Define buttons for toggling between magnitude and flux
    buttons = create_toggling_buttons(fig)
    
    # Update layout
    fig.update_layout(
        #title=f"{obj.name} Light Curves",
        xaxis_title="Modified Julian Date",
        yaxis_title="AB Magnitude",
        yaxis=dict(autorange='reversed',  # Inverted y-axis for magnitudes
                  ),  
        #legend_title="Filters",
        #template="plotly_white",
        xaxis_tickformat = '%d',
        width=700,
        height=500,
        font_family="P052",
        font_size=16,
    
        updatemenus=[
            dict(
                type='buttons',
                showactive=True,
                buttons=buttons,
                direction='left',
                x=0.15,
                y=1.15,
                xanchor='center',
                yanchor='top'
            )
        ],
    )
    
    return fig