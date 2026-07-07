import pandas as pd
import numpy as np
import folium
from battery_simulator_start import BatterySimulator
from battery_pack_start import BatteryPack
from Akku import lifepo
from Akku import nmc
import matplotlib.collections as mcollections
from geopy.geocoders import Nominatim
import time

import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from datetime import datetime

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

    d = R * c
    return d

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

def glaette_gps(df):
    df = df.copy()
    df["lat_glatt"] = df["lat"].rolling(window=10, min_periods=1).mean()
    df["lon_glatt"] = df["lon"].rolling(window=10, min_periods=1).mean()
    df["ele_glatt"] = df["ele"].rolling(window=10, min_periods=1).mean()
    return df

def luftdruck_berechnung(rho_0, M, g, R, temp, h):

    T = temp + 273.15  # Umrechnung von °C in Kelvin
    rho = rho_0 * np.exp((-M * g * h) / (R * T))
    return rho

def reverse_geocode(lat, lon):
    """Wandelt Breitengrad und Längengrad in eine lesbare Adresse um."""
    try:
        # Ein eindeutiger user_agent ist für den Nominatim-Dienst zwingend erforderlich
        geolocator = Nominatim(user_agent="abschlussprojekt_ebike_tour_simulator")
        location = geolocator.reverse((lat, lon), timeout=10)
        if location: # true wenn location erkannt wird
            address = location.raw.get("address", {})
            # Versuche den Stadtnamen oder das Dorf zu erkennen, erkennd kleinste urbane Einheit 
            ort = address.get("village") or address.get("town") or address.get("city") or address.get("suburb")
            # Falls kein spezifischer Ort gefunden wurde, nimm die formatierte Adresse
            return ort if ort else location.address
        return "Unbekannter Ort"
    except Exception as e:
        return f"Fehler bei der Abfrage ({e})"

if __name__ == "__main__":
    g = 9.81
    #rho = 1.225                # Luftdichte
    A = 0.5625                  # Produkt Stirnfläche, cw-Wert
    m = 80                      # Masse Fahrrad + Fahrer
    r_inch = 27                 # Raddurchmesser in inch
    r_m = r_inch * 0.0254       # Raddurchmesser in mm
    m_konst = 1.5               # Motorkonstante Nm/A
    rho_0 = 1.225               # Luftdichte auf Meereshöhe (ca. 1,225 kg/m³)
    M = 0.02896                 # Molare Masse der Luft (≈ 0,02896 kg/mol)
    g = 9.81                    # Erdbeschleunigung (≈ 9,81 m/s²)
    R = 8.314                   # Universelle Gaskonstante (\(8{,}314 \text{ J/(mol}\cdot\text{K)}\))
    T = 273.15                  # Absolute Temperatur in Kelvin (T in °C + 273,15)




    df = pd.read_csv("final_project_input_data.csv", sep=";") # Einlesen der CSV-Datei
    df = glaette_gps(df)



    df["time"] = pd.to_datetime(df["time"])
    df["time_s"] = (df["time"] - df["time"].iloc[0]).dt.total_seconds()


    df["ds"] = haversine(
        df["lat_glatt"].shift(),
        df["lon_glatt"].shift(),
        df["lat_glatt"],
        df["lon_glatt"]
    )

    df["ds_orig"] = haversine(
        df["lat"].shift(),
        df["lon"].shift(),
        df["lat"],
        df["lon"]
    )
    df["s_orig"] = df["ds_orig"].cumsum()     # zurückgelegte Strecke 

    df["dt"] = df["time_s"].diff()  # Zeitdifferenz
    #df = df[df["dt"] >= 1].copy()   # Zeilen mit dt < 1 Sekunde entfernen

    df["s"] = df["ds"].cumsum()     # zurückgelegte Strecke

    df["v"] = df["ds"] / df["dt"] # Geschwindigkeit
    df.loc[df["v"] > 30, "v"] = np.nan # Geschwindigkeit > 30 m/s löschen
    df["v"] = df["v"].interpolate() # fehlende Werte interpolieren
    df["v"] = (df["v"].rolling(window=25, center=True, min_periods=1).mean()) # Glättung der Geschwindigkeit

    df["a"] = np.gradient(df["v"], df["time_s"])
    df.loc[df["a"] > 1, "a"] = np.nan # Beschleunigung > 2 m/s² löschen
    df.loc[df["a"] < -1, "a"] = np.nan # Beschleunigung < -2 m/s² löschen
    df["a"] = df["a"].interpolate()
    df["a"] = df["a"].rolling(window=25, center=True, min_periods=1).mean() # Glättung der Beschleunigung


    df["dh"] = df["ele_glatt"].diff()                                                               # Höhenänderung
    df["phi_rad"] = np.arctan2(df["dh"], df["ds"])                                                  # Steigungswinkel
    
    df.loc[df["phi_rad"] < -0.174533, "phi_rad"] = np.nan                                           # Winkel < -10° löschen
    df["phi_rad"] = df["phi_rad"].interpolate()                                                     # fehlende Werte interpolieren
    df["phi_rad"] = df["phi_rad"].rolling(window=25, center=True, min_periods=1).mean()             # Glättung des Steigungswinkels
    df["phi_grad"] = np.degrees(df["phi_rad"])                                                      # Steigungswinkel in Grad
    
    df["rho"] = luftdruck_berechnung(rho_0, M, g, R, T, df["ele_glatt"])                                     # Luftdichte in Abhängigkeit der Höhe

    df["F_D"] = 0.5 * df["rho"] * A * df["v"]**2                                                          # Luftwiderstand
    df["F_H"] = (m * g) * np.sin(df["phi_rad"])                                                     # Hangkraft
    
    df["F_A"] = m * df["a"]                                                                         # Beschleunigungskraft
    
    df["F_Antrieb"] = df["F_D"] + df["F_H"] + df["F_A"]                                             # Gesamte Antriebskraft
    df["F_Antrieb"] = df["F_Antrieb"].rolling(window=25, center=True, min_periods=1).mean()         # Glättung der Antriebskraft
    
    df["P"] = df["F_Antrieb"] * df ["v"]                                                            # Berechnung der Leistung
    df["P"] = df["P"].rolling(window=25, center=True, min_periods=1).mean()                         # Glättung der Leistung
    
    df["T_drehmoment"] = df["F_Antrieb"] * (r_m/2)                                                  # Berechnung Drehmoment am Motor in Nm
    df["T_drehmoment"] = df["T_drehmoment"].rolling(window=25, center=True, min_periods=1).mean()   # Glättung des Drehmoments
    
    df["I_motor"] = df["T_drehmoment"] / m_konst                                                    # Berechnung Motorstrom bei bekannter Motorkonstante
    df["I_motor"] = df["I_motor"].rolling(window=25, center=True, min_periods=1).mean()             # Glättung des Motorstroms   




    b1 = lifepo(capacity_nom_cell_Ah=20.0, initial_soc=1.0)
    b2 = nmc(capacity_nom_cell_Ah=20.0, initial_soc=1.0)
    simulatorb1 = BatterySimulator(b1)
    simulatorb2 = BatterySimulator(b2)

    soc_liste = simulatorb1.simulation_ladezustand(df)
    df["SOC"] = soc_liste
    simulatorb1.plot_ladezustand(df)


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
        if spalte in ["lat", "lon", "time", "ele", "ele_glatt", "ds", "dt", "dh","F_D", "F_H", "F_A", "F_Antrieb", "temp", "phi_rad", "lat_glatt", "lon_glatt", "time_s"]:
            continue

        plt.figure(figsize=(10, 5))
        plt.plot(df["time_s"], df[spalte], linewidth=2)

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
            plt.ylabel(f"{spalte} [m]")
            plt.title("Höhe über der Zeit")

        plt.grid(True)
        plt.savefig(f"{spalte}.png", dpi=300, bbox_inches="tight")
        plt.close()


    #Ploten der Strecke auf einer Karte
    # NaN-Werte aus den geglätteten Koordinaten entfernen, da folium diese nicht verarbeiten kann
    df_map = df.dropna(subset=["lat_glatt", "lon_glatt"])

    if not df_map.empty:
        # Startpunkt für die Zentrierung der Karte festlegen
        start_lat = df_map["lat_glatt"].iloc[0]
        start_lon = df_map["lon_glatt"].iloc[0]
        
        # Endpunkt für die Markierung
        end_lat = df_map["lat_glatt"].iloc[-1]
        end_lon = df_map["lon_glatt"].iloc[-1]

        # Karte initialisieren (OpenStreetMap als Standard)
        karte = folium.Map(location=[start_lat, start_lon], zoom_start=14)

        # Koordinaten-Paare für die Linie (PolyLine) vorbereiten
        koordinaten = list(zip(df_map["lat_glatt"], df_map["lon_glatt"]))

        # Die gefahrene Strecke als rote Linie auf der Karte einzeichnen
        folium.PolyLine(
            locations=koordinaten, 
            color="red", 
            weight=4, 
            opacity=0.8,
            tooltip="Gefahrene Strecke"
        ).add_to(karte)

        # Start- und Zielmarker hinzufügen
        folium.Marker(
            [start_lat, start_lon], 
            popup="Start", 
            icon=folium.Icon(color="green", icon="play")
        ).add_to(karte)
        
        folium.Marker(
            [end_lat, end_lon], 
            popup="Ziel", 
            icon=folium.Icon(color="red", icon="stop")
        ).add_to(karte)

        # Karte als HTML-Datei speichern
        karte.save("strecken_karte.html")
        print("Interaktive Karte wurde als 'strecken_karte.html' gespeichert.")
    else:
        print("Keine gültigen GPS-Daten zum Plotten der Karte vorhanden.")





    #Ploten der Strecke auf einer Karte
    # NaN-Werte aus den geglätteten Koordinaten entfernen, da folium diese nicht verarbeiten kann
    df_map_glatt = df.dropna(subset=["lat_glatt", "lon_glatt"])
    df_map_orig = df.dropna(subset=["lat", "lon"])

    if not df_map.empty:
        # Startpunkt für die Zentrierung der Karte festlegen
        start_lat = df_map_orig["lat"].iloc[0]
        start_lon = df_map_orig["lon"].iloc[0]
        
        # Endpunkt für die Markierung
        end_lat = df_map_orig["lat"].iloc[-1]
        end_lon = df_map_orig["lon"].iloc[-1]

        # Karte initialisieren (OpenStreetMap als Standard)
        karte = folium.Map(location=[start_lat, start_lon], zoom_start=14)

        # Koordinaten-Paare für die Linie (PolyLine) vorbereiten
        koordinaten_glatt = list(zip(df_map_glatt["lat_glatt"], df_map_glatt["lon_glatt"]))
        koordinaten_orig = list(zip(df_map_orig["lat"], df_map_orig["lon"]))
        # Die gefahrene geglättete Strecke als rote Linie auf der Karte einzeichnen
        folium.PolyLine(
            locations=koordinaten_glatt, 
            color="red", 
            weight=4, 
            opacity=0.8,
            tooltip="Gefahrene Strecke"
        ).add_to(karte)
        # Die gefahrene original Strecke als grün Linie auf der Karte einzeichnen
        folium.PolyLine(
            locations=koordinaten_orig, 
            color="green", 
            weight=4, 
            opacity=0.8,
            tooltip="Gefahrene Strecke"
        ).add_to(karte)

        # Start- und Zielmarker hinzufügen
        folium.Marker(
            [start_lat, start_lon], 
            popup="Start", 
            icon=folium.Icon(color="green", icon="play")
        ).add_to(karte)
        
        folium.Marker(
            [end_lat, end_lon], 
            popup="Ziel", 
            icon=folium.Icon(color="red", icon="stop")
        ).add_to(karte)

        # Karte als HTML-Datei speichern
        karte.save("strecke_karte_vergleich.html")
        print("Interaktive Karte wurde als 'strecke_karte_vergleich.html' gespeichert.")
    else:
        print("Keine gültigen GPS-Daten zum Plotten der Karte vorhanden.")

    # höhenprofil ploten
    # Daten vorbereiten (X: Distanz in km, Y: geglättete Höhe in m)
    x = df["s_orig"] / 1000  # Umrechnung von Meter in Kilometer
    y = df["ele_glatt"]

    # Steigung in Prozent berechnen:
    steigung = np.tan(df["phi_rad"]) * 100

    # segmente für die LineCollection erstellen
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    fig, ax = plt.subplots()

    # Farbkarte definieren (Coolwarm wechselt von Blau zu Weiß zu Rot)
    cmap = plt.get_cmap('coolwarm')
    norm = plt.Normalize(vmin=-15, vmax=15)  # -15% bis +15%

    # LineCollection erstellen und hinzufügen
    lc = mcollections.LineCollection(segments, cmap=cmap, norm=norm, linewidths=3.5)
    lc.set_array(steigung)
    line = ax.add_collection(lc)

    # Achsen-Limits
    ax.set_xlim(0, 95)
    ax.set_ylim(450, 900)

    # Achsen-Ticks definieren
    ax.set_xticks(np.arange(0, 96, 5))
    ax.set_yticks(np.arange(500, 801, 100))

    ax.set_xlabel("Distanz / km")
    ax.set_ylabel("Höhe / m")

    # Ticks größer und sauberer darstellen
    ax.tick_params(axis='both', which='major')

    # Colorbar (Farbskala) hinzufügen
    cbar = fig.colorbar(line, ax=ax)
    cbar.set_label("Steigung / %")
    cbar.set_ticks([-10, 0, 10])
 
    
    plt.savefig("hoehenprofil_steigung.png")


    #Reverse Geocoding ( Ermitten der orte entlang der Strecke)
    orte_marken = [] # Liste aus Tupeln: (Distanz_in_km, "Ortsname", Hoehe)
    letzter_ort = None
    
    # Prüfen den Datensatz in Schritten von z.B. 200 Zeilen (Intervall je nach Datendichte anpassen)
    schrittweite = max(1, len(df) // 30) # Ergibt ca. 30 Checkpoints über die Fahrt
    
    print("Ermittle Orte entlang der Strecke...")
    for idx in range(0, len(df), schrittweite):
        row = df.iloc[idx]

        # Überspringe Zeilen mit NaN-Werten
        if pd.isna(row["s_orig"]) or pd.isna(row["lat_glatt"]) or pd.isna(row["lon_glatt"]):
            continue

        aktuelle_distanz_km = row["s_orig"] / 1000
        
        # API abfragen
        ort = reverse_geocode(row["lat_glatt"], row["lon_glatt"])
        
        # Warte 1 Sekunde, um den Fehler 429 (zu viele Anfragen) zu vermeiden
        time.sleep(1)

        # Speichern, wenn ein Ort gefunden wurde und er neu ist
        if ort and ort != letzter_ort:
            orte_marken.append(ort)
            letzter_ort = ort

    print(orte_marken)
  