import pandas as pd
import numpy as np
from Akkumodell2.battery_simulator_start import BatterySimulator
from Akkumodell2.battery_pack_start import BatteryPack

import matplotlib.pyplot as plt

g = 9.81
rho = 1.225              # Luftdichte
A = 0.5625                  # Produkt Stirnfläche, cw-Wert
m = 80                  # Masse Fahrrad + Fahrer

r_inch = 27                 # Raddurchmesser in inch
r_m = r_inch * 0.0254        # Raddurchmesser in mm
m_konst = 1.5               # Motorkonstante Nm/A

df = pd.read_csv("final_project_input_data.csv", sep=";") # Einlesen der CSV-Datei
df["time"] = pd.to_datetime(df["time"])


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

# Strecke
df["ds"] = haversine(
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

Gesamtstrecke = df["ds"].sum()
Durchschnittsgeschwindigkeit = df["v"].mean()

# Ergebnisse speichern
#df.to_csv("GPS_Auswertung.csv", index=False)

print(f"\nGesamtdistanz: {Gesamtstrecke:.1f} m")
print(f"Durchschnittsgeschwindigkeit: {Durchschnittsgeschwindigkeit:.1f} m/s")


#berechnung der Leistung
df["P"] = df["F_Antrieb"] * df ["v"]

# berechnung Drehmoment am Motor in Nm
df["T_drehmoment"] = df["F_Antrieb"] * r_m 

# berechnung Motorstrom bei bekannter Motorkonstante
df["I_motor"] = df["T_drehmoment"] / m_konst

# Berechnung Maximalleistung
df["P_max"] = df["P"].max()

# Enwicklung des Ladezustandes des Akkus über die Fahrt
def simulation_ladezustand(df, battery : BatteryPack = BatteryPack(capacity_nom_Ah=10, initial_soc=0.7, Vmin=32.0, Vmax=42.0)):
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


# Ergebnisse speichern
df.to_csv("Output.csv", index=False)






# Für jede Spalte einen Graphen erstellen
for spalte in df.columns:
    if spalte == "time":
        continue  # Zeitspalte nicht gegen sich selbst plotten

    plt.figure(figsize=(10, 5))
    plt.plot(df["time"], df[spalte], linewidth=2)

    plt.title(f"{spalte} über der Zeit")
    plt.xlabel("Zeit [s]")
    plt.ylabel(spalte)
    plt.grid(True)

    plt.show()
