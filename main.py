import pandas as pd
import numpy as np

g = 9.81
rho = 1.225              # Luftdichte
cw = 0.9                 # Luftwiderstandsbeiwert Fahrer + Fahrrad
A = 0.5                  # Stirnfläche
m = 100                  # Masse Fahrrad + Fahrer

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

df["F_D"] = 0.5 * rho * cw * A * df["v"]**2 # Luftwiderstand
df["F_H"] = m * g * np.sin(df["phi"]) # Hangkraft
df["F_A"] = m * df["a"] # Beschleunigungskraft

df["F_Antrieb"] = df["F_D"] + df["F_H"] + df["F_A"] # Gesamte Antriebskraft

# Ergebnisse speichern
df.to_csv("GPS_Auswertung.csv", index=False)

# Ausgabe
print(df[[
    "time",
    "ds",
    "v",
    "a",
    "phi",
    "F_D",
    "F_H",
    "F_A",
    "F_Antrieb"
]].head())

print(f"\nGesamtdistanz: {df['ds'].iloc[-1]:.1f} m")