import matplotlib.pyplot as plt


def plot_current_profile(current_profile: list[float], duration_profile: list[float]):
    """Plots the current over time profile starting from t=0s. The current is assumed to be piecewise constant over the given duration intervals.

    Parameters
    ----------
    current_profile : list[float]
        List of current values in Amperes (A) for each interval.
    duration_profile : list[float]
        List of duration values in seconds (s) for each interval. Must have the same length as current_profile.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The matplotlib figure object containing the plot of current over time.
    """

    assert len(current_profile) == len(duration_profile), "Current and duration profiles must have the same length."

    t_plot, I_plot = [], []
    t_total = 0.0
    for I, d in zip(current_profile, duration_profile):
        t_plot += [t_total, t_total + d]
        I_plot += [I, I]
        t_total += d

    fig, ax = plt.subplots()
    ax.plot(t_plot, I_plot)
    ax.set_xlabel("Time $t$ / s")
    ax.set_ylabel("Current $I$ / A")
    ax.set_yticks(range(-2, 12, 1))
    ax.set_xticks(range(0, int(t_total) + 1, 60))
    ax.grid(True)
    fig.show()

    return fig

def plot_voltage_profile(voltage_profile: list[float], duration_profile: list[float]):
    """Plots the voltage over time profile starting from t=0s. 
    The voltage_profile must start with the initial voltage at t=0s, and the subsequent voltage values correspond to the voltage after applying the current for the respective duration intervals.
    The voltage is assumed to be piecewise constant over the given duration intervals.

    Parameters
    ----------
    voltage_profile : list[float]
        List of voltage values in Volts (V) for each interval. Plus the initial voltage at t=0s.
    duration_profile : list[float]
        List of duration values in seconds (s) for each interval. Must have the same length as voltage_profile.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The matplotlib figure object containing the plot of voltage over time.
    """

    assert len(voltage_profile) - 1 == len(duration_profile), "Voltage profile must be longer by 1 than duration profile and to account for the starting voltage at t=0s."

    t_plot, U_plot = [], []

    t_plot.append(0.0)
    U_plot.append(voltage_profile[0])

    t_total = 0.0
    for U, d in zip(voltage_profile[1:], duration_profile):
        t_plot += [t_total, t_total + d]
        U_plot += [U, U]
        t_total += d

    fig, ax = plt.subplots()
    ax.plot(t_plot, U_plot)
    ax.set_xlabel("Time $t$ / s")
    ax.set_ylabel("Voltage $U$ / V")
    ax.grid(True)
    fig.show()

    return fig

def plot_voltage_and_current_profile(voltage_profile: list[float], current_profile: list[float], duration_profile: list[float]):
    """Plots the voltage and current over time profiles starting from t=0s. 
    The voltage_profile must start with the initial voltage at t=0s, and the subsequent voltage values correspond to the voltage after applying the current for the respective duration intervals.
    The voltage and current are assumed to be piecewise constant over the given duration intervals.

    Parameters
    ----------
    voltage_profile : list[float]
        List of voltage values in Volts (V) for each interval. Plus the initial voltage at t=0s.
    current_profile : list[float]
        List of current values in Amperes (A) for each interval.
    duration_profile : list[float]
        List of duration values in seconds (s) for each interval. Must have the same length as voltage_profile and current_profile.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The matplotlib figure object containing the plot of voltage and current over time.
    """

    assert len(voltage_profile) - 1 == len(current_profile) == len(duration_profile), "Current and duration profiles must have the same length, and voltage profile must be longer by 1 to account for the starting voltage at t=0s."

    t_plot, U_plot, I_plot = [], [], []

    t_plot.append(0.0)
    U_plot.append(voltage_profile[0])

    t_total = 0.0
    for U, I, d in zip(voltage_profile[1:], current_profile, duration_profile):
        t_plot += [t_total, t_total + d]
        U_plot += [U, U]
        I_plot += [I, I]

        t_total += d

    fig, axV = plt.subplots(figsize=(9, 4.5))
    axI = axV.twinx()

    axV.plot(t_plot[0:], U_plot, "b-", label="Voltage U / V")
    axI.plot(t_plot[1:], I_plot, "r--", label="Current I / A")
    axV.set_xlabel("Time $t$ / s")
    axV.set_ylabel("Voltage $U$ / V", color="b")
    axI.set_ylabel("Current $I$ / A", color="r")
    axV.grid(True)
    
    fig.legend(loc="upper right", bbox_to_anchor=(0.85, 0.85))
    fig.show()

    return fig