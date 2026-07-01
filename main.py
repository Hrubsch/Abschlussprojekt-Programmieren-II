import pandas as pd
import numpy as np
from Akkumodell2.battery_simulator_start import BatterySimulator
from Akkumodell2.battery_pack_start import BatteryPack
from Akkumodell2.Akku import lifepo
from Akkumodell2.Akku import nmc


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


# Enwicklung des Ladezustandes des Akkus über die Fahrt
#def simulation_ladezustand(df, battery : BatteryPack = BatteryPack(capacity_nom_Ah=10, initial_soc=0.7, Vmin=32.0, Vmax=42.0)):
    """Simulation des Ladezustands des Akkus über die Fahrt"""
    simulator = BatterySimulator(battery)

    df_bereinigt = df.dropna(subset=["dt"]) #ohne erste Zeile, weil keine Werte

    #current_list = df_bereinigt["I_motor"].to_list()
    #duration_list = df_bereinigt["dt"].to_list()

    soc_liste = []
    soc_liste.append(battery.soc * 100)
    for i,j in df_bereinigt.iterrows():
        dt = j["dt"]
        I_motor = j["I_motor"]
    battery.apply_current(I_motor, dt)
    soc_liste.append(battery.soc * 100) #hinzufügen von soc in %
    df["SOC"] = soc_liste
    return df["SOC"]





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
        df["lat"].shift(),
        df["lon"].shift(),
        df["lat"],
        df["lon"]

)
    

    df["dt"] = df["time"].diff().dt.total_seconds() # Zeitdifferenz
    df["v"] = df["ds"] / df["dt"] # Geschwindigkeit
    df["a"] = (df["v"].shift(-1) - df["v"].shift(1)) / (df["time"].shift(-1) - df["time"].shift(1)).dt.total_seconds() # Beschleunigung
    df["dh"] = df["ele"].diff() # Höhenänderung
    df["phi_rad"] = np.arctan2(df["dh"], df["ds"]) # Steigungswinkel
    df["phi_grad"] = np.degrees(df["phi_rad"]) # Steigungswinkel in Grad
    df["F_D"] = 0.5 * rho * A * df["v"]**2 # Luftwiderstand
    df["F_H"] = m * g * np.sin(df["phi_rad"]) # Hangkraft
    df["F_A"] = m * df["a"] # Beschleunigungskraft
    df["F_Antrieb"] = df["F_D"] + df["F_H"] + df["F_A"] # Gesamte Antriebskraft
    df["P"] = (df["F_Antrieb"] * df ["v"]) / df["dt"]#berechnung der Leistung
    df["T_drehmoment"] = df["F_Antrieb"] * r_m # berechnung Drehmoment am Motor in Nm
    df["I_motor"] = df["T_drehmoment"] / m_konst # berechnung Motorstrom bei bekannter Motorkonstante




# Ergebnisse speichern
    df.to_csv("Output.csv", index=False)



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
    if spalte in ["lat", "lon", "time", "ds", "dt", "F_D", "F_H", "F_A", "F_Antrieb", "dh", "temp", "phi_rad"]:
        continue

    plt.figure(figsize=(10, 5))
    plt.plot(df["time"], df[spalte], linewidth=2)

    plt.title(f"{spalte} über der Zeit")
    plt.xlabel("Zeit [s]")
    if spalte == "v":
        plt.ylabel(f"{spalte} [m/s]")
    elif spalte == "a":
        plt.ylabel(f"{spalte} [m/s²]")
    elif spalte == "P":
        plt.ylabel(f"{spalte} [W]")
    elif spalte == "phi_grad":
        plt.ylabel(f"{spalte} [°]")
    elif spalte == "T_drehmoment":
        plt.ylabel(f"{spalte} [Nm]")
    elif spalte == "I_motor":
        plt.ylabel(f"{spalte} [A]")
    elif spalte == "SOC":
        plt.ylabel(f"{spalte} [%]")
    elif spalte == "ele":
        plt.title(f"Höhenprofil über der Zeit")
        plt.ylabel(f"{spalte} [m]")

    plt.show()


    b1 = lifepo(capacity_nom_cell_Ah=10.0, initial_soc=1.0)
    b2 = nmc(capacity_nom_cell_Ah=10.0, initial_soc=1.0)
    simulatorb1 = BatterySimulator(b1)
    simulatorb2 = BatterySimulator(b2)

    simulatorb1.simulation_ladezustand(df)
    simulatorb1.plot_ladezustand(df)

    plt.grid(True)
    plt.savefig(f"{spalte}.png", dpi=300, bbox_inches="tight")
    plt.close()
