import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def Kenngroessen(df):
    # Maximalleistung
    P_max = df["P"].max()

    # Gesamtstrecke
    Gesamtstrecke = df["ds"].sum()

    # Durchschnittsgeschwindigkeit
    Durchschnittsgeschwindigkeit = df["v"].mean()

    # Gesamtzeit
    Gesamtzeit = df["time"].iloc[-1] - df["time"].iloc[0]

    # Höhenänderungen
    hoehenaenderung = df["ele"].diff()

    # Gesamter Anstieg und Abstieg
    anstieg = hoehenaenderung[hoehenaenderung > 0].sum()
    abstieg = -hoehenaenderung[hoehenaenderung < 0].sum()

    return {
        "P_max": P_max,
        "Gesamtstrecke": Gesamtstrecke,
        "Durchschnittsgeschwindigkeit": Durchschnittsgeschwindigkeit,
        "Gesamtzeit": Gesamtzeit,
        "Anstieg": anstieg,
        "Abstieg": abstieg
    }

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    c = 2*np.arctan2(np.sqrt(a), np.sqrt(1-a))

    return R*c








if __name__ == "__main__":
    g = 9.81
    rho = 1.225              # Luftdichte
    A = 0.5625                  # Produkt Stirnfläche, cw-Wert
    m = 80                  # Masse Fahrrad + Fahrer
    r_inch = 27                 # Raddurchmesser in inch
    r_m = r_inch * 0.0254        # Raddurchmesser in mm
    m_konst = 1.5               # Motorkonstante Nm/A

    df = pd.read_csv("final_project_input_data.csv", sep=";") # Einlesen der CSV-Datei
    df["time"] = pd.to_datetime(df["time"])

    df["ds"] = haversine(# Strecke
        df["lat"],
        df["lon"],
        df["lat"].shift(),
        df["lon"].shift()
)
    df["dt"] = df["time"].diff().dt.total_seconds() # Zeitdifferenz
    df["v"] = df["ds"] / df["dt"] # Geschwindigkeit
    df["a"] = df["v"].diff() / df["dt"] # Beschleunigung
    df["dh"] = df["ele"].diff() # Höhenänderung
    df["phi"] = np.arctan2(df["dh"], df["ds"]) # Steigungswinkel
    df["F_D"] = 0.5 * rho * A * df["v"]**2 # Luftwiderstand
    df["F_H"] = m * g * np.sin(df["phi"]) # Hangkraft
    df["F_A"] = m * df["a"] # Beschleunigungskraft
    df["F_Antrieb"] = df["F_D"] + df["F_H"] + df["F_A"] # Gesamte Antriebskraft
    df["P"] = (df["F_Antrieb"] * df ["v"]) / df["dt"]#berechnung der Leistung
    df["T_drehmoment"] = df["F_Antrieb"] * r_m # berechnung Drehmoment am Motor in Nm
    df["I_motor"] = df["T_drehmoment"] / m_konst # berechnung Motorstrom bei bekannter Motorkonstante



    results = Kenngroessen(df)
    print(f"\nGesamtdistanz: {results['Gesamtstrecke']:.1f} m")
    print(f"Durchschnittsgeschwindigkeit: {results['Durchschnittsgeschwindigkeit']:.1f} m/s")
    print(f"Maximalleistung: {results['P_max']:.1f} W")
    print(f"Gesamtzeit: {results['Gesamtzeit']}")
    print(f"Gesamter Anstieg: {results['Anstieg']:.1f} m")
    print(f"Gesamter Abstieg: {results['Abstieg']:.1f} m")

    # Ergebnisse speichern
    df.to_csv("Output.csv", index=False)

for spalte in df.columns:
    if spalte in ["lat", "lon", "ele", "time", "ds", "dt", "phi", "F_D", "F_H", "F_A", "F_Antrieb", "dh"]:
        continue

    plt.figure(figsize=(10, 5))
    plt.plot(df["time"], df[spalte], linewidth=2)

    plt.title(f"{spalte} über der Zeit")
    plt.xlabel("Zeit [s]")
    plt.ylabel(spalte)
    plt.grid(True)

    plt.savefig(f"{spalte}.png", dpi=300, bbox_inches="tight")
    plt.close()