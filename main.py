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
import logging

import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from datetime import datetime

from LaTeX import create_latex_report
logging.basicConfig(format="%(asctime)s:%(levelname)s: %(message)s", level=logging.INFO, filename="Main.log", force=True)

def Kenngroessen(df):
    # Maximalleistung
    P_max = df["P"].max()
    # Gesamtstrecke
    Gesamtstrecke_Original = df["ds_orig"].sum() 
    Gesamtstrecke_Glatt = df["ds"].sum() 
    # Durchschnittsgeschwindigkeit
    Durchschnittsgeschwindigkeit = df["v"].mean()
    # Gesamtzeit
    Gesamtzeit = (df["time"].iloc[-1] - df["time"].iloc[0])
    # Höhenänderungen
    hoehenaenderung = df["ele"].diff()
    # Gesamter Anstieg und Abstieg
    anstieg = hoehenaenderung[hoehenaenderung > 0].sum()
    abstieg = -hoehenaenderung[hoehenaenderung < 0].sum()

    return {
        "P_max": P_max,
        "Gesamtstrecke_Original": Gesamtstrecke_Original,
        "Gesamtstrecke_Glatt": Gesamtstrecke_Glatt,
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

def PlotStreckeAufKarte(df : pd.DataFrame) -> None:
    """
    Die Originale und geplottete Strecke werden auf einer Folium-Karte geplotet
    """
    try:
        # Prüfen, ob die absolut notwendigen Spalten überhaupt im DataFrame existieren
        erforderliche_spalten = ["lat", "lon", "lat_glatt", "lon_glatt"]
        for spalte in erforderliche_spalten:
            if spalte not in df.columns:
                raise KeyError(f"Die erforderliche Spalte '{spalte}' fehlt im DataFrame.")
            
        # NaN-Werte aus den Koordinaten entfernen, da folium diese nicht verarbeiten kann
        df_map_glatt = df.dropna(subset=["lat_glatt", "lon_glatt"])
        df_map_orig = df.dropna(subset=["lat", "lon"])

        # Prüfen, ob DataFrame gefüllt ist mit Werten
        if df_map_glatt.empty or df_map_orig.empty:
            logging.warning("Karten-Plot abgebrochen: Keine gültigen GPS-Daten vorhanden.")
            print("Keine gültigen GPS-Daten zum Plotten der Karte vorhanden.")
            return

        # Startpunkt für die Zentrierung der Karte festlegen
        start_lat = df_map_orig["lat"].iloc[0]
        start_lon = df_map_orig["lon"].iloc[0]
        
        # Endpunkt für die Markierung
        end_lat = df_map_orig["lat"].iloc[-1]
        end_lon = df_map_orig["lon"].iloc[-1]

        # Karte initialisieren 
        karte = folium.Map(tiles="cartodb positron") # "cartodb positron" nutzen. Das blockiert Selenium nicht

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
        # Die gefahrene original Strecke als grüne Linie auf der Karte einzeichnen
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

        # Karte automatisch so zoomen, dass die gesamte Strecke exakt hineinpasst
        karte.fit_bounds(koordinaten_orig)

        # Karte als HTML-Datei speichern
        karte.save("strecke_karte_vergleich.html")
        print("Karte wurde als 'strecke_karte_vergleich.html' gespeichert.")
        logging.info("Karte wurde als 'strecke_karte_vergleich.html' gespeichert.")

        # Automatisch als PNG exportieren via Selenium
        print("Erstelle PNG-Abbildung (dies kann einen Moment dauern)...")
        
        # Konvertiert das Folium-Objekt direkt in ein PNG-Byte-Array und speichert es
        img_data = karte._to_png(delay=3)  # delay gibt der Karte Zeit zum Rendern
        with open("strecke_karte_abbildung.png", "wb") as f:
            f.write(img_data)
            
        print(f"Abbildung wurde erfolgreich als 'strecke_karte_abbildung.png' gespeichert.")
        logging.info(f"Abbildung wurde erfolgreich als 'strecke_karte_abbildung.png' gespeichert.")

    except KeyError as ke:
        logging.error(f"Strukturfehler im DataFrame bei der Kartenerstellung: {ke}")
    except Exception as e:
        # Fängt alle unerwarteten Fehler ab (z.B. Speicherfehler, Folium-interne Probleme)
        logging.error(f"Unerwarteter Fehler beim Erstellen der Streckenkarte: {e}", exc_info=True) # exc_info=True (bei unerwarteten Fehler wird Zeilennummer des Fehlers in Log geschrieben)

def hoehenprofil_steigung(df : pd.DataFrame)-> None:
    """
    Erstellt ein farbcodiertes Höhenprofil basierend auf der Steigung und speichert es als PNG.
    """
    try:
        # Prüfen, ob die absolut notwendigen Spalten überhaupt im DataFrame existieren
        erforderliche_spalten = ["s_orig", "ele_glatt", "phi_rad"]
        for spalte in erforderliche_spalten:
            if spalte not in df.columns:
                raise KeyError(f"Die erforderliche Spalte '{spalte}' fehlt im DataFrame.")
            
        # Prüfen, ob DataFrame gefüllt ist mit Werten
        if df.empty:
            logging.warning("Plotten des Höhenprofils abgebrochen: Keine gültigen Daten vorhanden.")
            print("Plotten des Höhenprofils abgebrochen: Keine gültigen Daten vorhanden.")
            return
        
        # Daten vorbereiten (X: Distanz in km, Y: geglättete Höhe in m)
        x = df["s_orig"] / 1000  # Umrechnung von Meter in Kilometer
        y = df["ele_glatt"]

        # Steigung in Prozent berechnen:
        steigung = np.tan(df["phi_rad"]) * 100

        # segmente für die LineCollection erstellen
        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        fig, ax = plt.subplots(figsize=(10, 5))

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

        plt.tight_layout() # Verhindert abgeschnittene Ränder im PNG
        plt.savefig("hoehenprofil_steigung.png")
        plt.close() # schließt das Fenster
        logging.info("Höhenprofil erfolgreich generiert und gespeichert.")
        print("Höhenprofil erfolgreich generiert und als `hoehenprofil_steigung.png` gespeichert.")

    except KeyError as ke:
        logging.error(f"Datenfehler in hoehenprofil_steigung: {ke}")
    except ValueError as ve:
        logging.error(f"Berechnungsfehler in hoehenprofil_steigung: {ve}. Überprüfe, ob Daten leere Werte (NaNs) enthalten.")
    except Exception as e:
        logging.error(f"Unerwarteter Fehler bei der Diagrammerstellung: {e}", exc_info=True)

def reverse_geocoding(df : pd.DataFrame) -> list[str]:
    """Ermitteln der durchfahrenen Orte und ausgabe als Liste von str"""
    # Prüfen, ob die absolut notwendigen Spalten überhaupt im DataFrame existieren
    erforderliche_spalten = ["s_orig", "lat", "lon", "ele"]
    for spalte in erforderliche_spalten:
        if spalte not in df.columns:
            raise KeyError(f"Die erforderliche Spalte '{spalte}' fehlt im DataFrame.")
            
    # Prüfen, ob DataFrame gefüllt ist mit Werten
    if df.empty:
        logging.warning("Reverse Geocoding abgebrochen: Keine gültigen GPS-Daten vorhanden.")
        print("Reverse Geocoding abgebrochen: Keine gültigen GPS-Daten vorhanden.")
        return

    liste_orte = [] 
    letzter_ort = None
    
    # Berechnung der Schrittweite. Dadurch wird ermitteln der Ort schneller
    # Wenn // <30 dann schrittweite größer => ungenauer. Wenn // >30 dann schrittweite kleiner => genauer
    schrittweite = max(1, len(df) // 30) # Schrittweite ca. 76
    
    print("Ermittle Orte entlang der Strecke (dies kann einen Moment dauern)...")
    logging.info(f"Starte Reverse Geocoding mit {len(df)} Zeilen. Schrittweite: {schrittweite}")
    # Verhindert, dass die erste Anfrage direkt nach den Karten-Plots blockiert wird
    time.sleep(2)
    # Ein eindeutiger user_agent ist für den Nominatim-Dienst zwingend erforderlich
    geolocator = Nominatim(user_agent="abschlussprojekt_ebike_tour_simulator")

    for idx in range(0, len(df), schrittweite):
        try:
            row = df.iloc[idx]
            # Überspringe Zeilen mit NaN-Werten
            if pd.isna(row["s_orig"]) or pd.isna(row["lat"]) or pd.isna(row["lon"]):
                logging.warning(f"Zeile {idx} wurde übersprungen, weil kein gültiger Wert (NaN) eingetragen ist.")
                continue
            # API abfragen
            ort = None
            ort_name = None
            try: # um API Fehler abzufangen
                location = geolocator.reverse((row["lat"], row["lon"]), timeout=10) # suchen der adresse und speichern als location objekt 
                if location: # true wenn location erkannt wird
                    address = location.raw.get("address", {}) # gibt adresse aus location objekt zurück
                    # Versuche den Stadtnamen oder das Dorf zu erkennen, erkennd kleinste urbane Einheit 
                    ort_name = address.get("village") or address.get("town") or address.get("city") or address.get("suburb")
                    # Falls kein spezifischer Ort gefunden wurde, nimm die formatierte Adresse
                    if ort_name:
                        ort = ort_name
                    else:
                        ort = location.address
                else:
                    ort = "Unbekannter Ort"
                    logging.info("Ort wurde nicht gefunden")
            except Exception as e:
                logging.warning(f"API-Fehler bei Zeile {idx}: {e}")
                ort = f"Fehler bei der Abfrage ({e})"

            # Warte 1 Sekunde, um den Fehler 429 (zu viele Anfragen) zu vermeiden
            time.sleep(1) # durch Warten dauert Funktion ca. 31 sek.
        
            # Speichern, wenn ein Ort gefunden wurde und er neu ist
            if ort != letzter_ort:
                liste_orte.append(ort)
                letzter_ort = ort_name

        except Exception as e:
            # Fängt unerwartete Fehler innerhalb der Schleife ab, damit das Skript nicht abstürzt
            logging.error(f"Unerwarteter Fehler bei der Verarbeitung von Index {idx}: {e}", exc_info=True) # exc_info=True (bei Fehler wird Zeilennummer des Fehlers in Log geschrieben)
            continue

    logging.info(f"Reverse Geocoding erfolgreich beendet")

    # Speichern der durchfahrenen Orte als .txt Datei
    try:
        datei_name = "durchfahrene_orte.txt"
        with open(datei_name, "w", encoding="utf-8") as f: # with .. as f Datei wird automatisch wieder gedchlossen; open(datei_name,..) ... öffnen der Datei; w ... write; encoding="utf-8" ... auch Umlaute können geschrieben werden
            for ort in liste_orte:
                f.write(f"{ort}\n") # \n ... Zeilenumbruch
        logging.info(f"Orte erfolgreich in {datei_name} exportiert.")
        print(f"Orte erfolgreich in '{datei_name}' gespeichert.")
    except Exception as e:
        logging.error(f"Fehler beim Schreiben der TXT-Datei: {e}")

    return liste_orte

def simulation(df, masse, A, r_inch):
    g = 9.81
    m = masse                       # Masse Fahrrad + Fahrer
    A = A                           # Produkt Stirnfläche, cw-Wert
    r_inch = r_inch                 # Raddurchmesser in inch
    r_m = r_inch * 0.0254           # Raddurchmesser in mm
    m_konst = 1.5                   # Motorkonstante Nm/A
    rho_0 = 1.225                   # Luftdichte auf Meereshöhe (ca. 1,225 kg/m³)
    M = 0.02896                     # Molare Masse der Luft (≈ 0,02896 kg/mol)
    g = 9.81                        # Erdbeschleunigung (≈ 9,81 m/s²)
    R = 8.314                       # Universelle Gaskonstante (\(8{,}314 \text{ J/(mol}\cdot\text{K)}\))
    T = 273.15                      # Absolute Temperatur in Kelvin (T in °C + 273,15)
    c_R = 0.003                     # Rollwiderstandsbeiwert Quelle: https://www.rhetos.de/html/lex/rollwiderstandskoeffizienten.htm

    df = glaette_gps(df)
    
    df["time"] = pd.to_datetime(df["time"])
    df["time_s"] = (df["time"] - df["time"].iloc[0]).dt.total_seconds()

    df["ds"] = haversine(
        df["lat_glatt"].shift(),
        df["lon_glatt"].shift(),
        df["lat_glatt"],
        df["lon_glatt"]
    )
    df["s"] = df["ds"].cumsum()                                                                     # zurückgelegte Strecke mit den geglätteten Werten

    df["dt"] = df["time_s"].diff()                                                                  # Zeitdifferenz
    df["ds_orig"] = haversine(
        df["lat"].shift(),
        df["lon"].shift(),
        df["lat"],
        df["lon"]
    )
    df["s_orig"] = df["ds_orig"].cumsum()                                                           # zurückgelegte Strecke mit original Werten 

    df["v"] = df["ds"] / df["dt"]                                                                   # Geschwindigkeit
    df.loc[df["v"] > 30, "v"] = np.nan                                                              # Geschwindigkeit > 30 m/s löschen
    df["v"] = df["v"].interpolate()                                                                 # fehlende Werte interpolieren
    df["v"] = (df["v"].rolling(window=25, center=True, min_periods=1).mean())                       # Glättung der Geschwindigkeit

    df["a"] = np.gradient(df["v"], df["time_s"])
    df.loc[df["a"] > 1, "a"] = np.nan                                                               # Beschleunigung > 2 m/s² löschen
    df.loc[df["a"] < -1, "a"] = np.nan                                                              # Beschleunigung < -2 m/s² löschen
    df["a"] = df["a"].interpolate()
    df["a"] = df["a"].rolling(window=25, center=True, min_periods=1).mean()                         # Glättung der Beschleunigung

    df["dh"] = df["ele_glatt"].diff()                                                               # Höhenänderung
    df["phi_rad"] = np.arctan2(df["dh"], df["ds"])                                                  # Steigungswinkel
    
    df.loc[df["phi_rad"] < -0.174533, "phi_rad"] = np.nan                                           # Winkel < -10° löschen
    df["phi_rad"] = df["phi_rad"].interpolate()                                                     # fehlende Werte interpolieren
    df["phi_rad"] = df["phi_rad"].rolling(window=25, center=True, min_periods=1).mean()             # Glättung des Steigungswinkels
    df["phi_grad"] = np.degrees(df["phi_rad"])                                                      # Steigungswinkel in Grad
    
    df["rho"] = luftdruck_berechnung(rho_0, M, g, R, T, df["ele_glatt"])                            # Luftdichte in Abhängigkeit der Höhe

    df["F_D"] = 0.5 * df["rho"] * A * df["v"]**2                                                    # Luftwiderstand
    df["F_H"] = (m * g) * np.sin(df["phi_rad"])                                                     # Hangkraft
    df["F_A"] = m * df["a"]                                                                         # Beschleunigungskraft
    df["F_R"] = c_R * m * g * np.cos(df["phi_rad"])                                                 # Rollwiderstand 

    df["F_Antrieb"] = df["F_D"] + df["F_H"] + df["F_A"]  + df["F_R"]                                # Gesamte Antriebskraft
    df["F_Antrieb"] = df["F_Antrieb"].rolling(window=25, center=True, min_periods=1).mean()         # Glättung der Antriebskraft
    
    df["P"] = df["F_Antrieb"] * df ["v"]                                                            # Berechnung der Leistung
    df["P"] = df["P"].rolling(window=25, center=True, min_periods=1).mean()                         # Glättung der Leistung
    
    df["T_drehmoment"] = df["F_Antrieb"] * (r_m/2)                                                  # Berechnung Drehmoment am Motor in Nm
    df["T_drehmoment"] = df["T_drehmoment"].rolling(window=25, center=True, min_periods=1).mean()   # Glättung des Drehmoments
    
    df["I_motor"] = df["T_drehmoment"] / m_konst                                                    # Berechnung Motorstrom bei bekannter Motorkonstante
    df["I_motor"] = df["I_motor"].rolling(window=25, center=True, min_periods=1).mean()             # Glättung des Motorstroms   

    #Simulation des Laddezustande der beiden Akkutypen
    b1 = lifepo(capacity_nom_cell_Ah=30.0, initial_soc=1.0)     # Ertellen einer Instanz des lifepo Akkus
    b2 = nmc(capacity_nom_cell_Ah=30.0, initial_soc=1.0)        # Erstellen einer Instanz des nmc Akkus
    simulatorb1 = BatterySimulator(b1)                          # Erstellen eine Instanz der Klasse BatterySimulator
    simulatorb2 = BatterySimulator(b2)                          # Erstellen eine Instanz der Klasse BatterySimulator

    soc_liste_lifepo = simulatorb1.simulation_ladezustand(df)   # Speichern der durch die Methode simulation_ladezustand zurück gegebenen Liste an Ladezuständen
    soc_liste_nmc = simulatorb2.simulation_ladezustand(df)      # Speichern der durch die Methode simulation_ladezustand zurück gegebenen Liste an Ladezuständen
    df["SOC_lifepo"] = soc_liste_lifepo                         # Hinzufügen einer neuen Spalte im Pandas-DataFrame für den SOC
    df["SOC_nmc"] = soc_liste_nmc                               # Hinzufügen einer neuen Spalte im Pandas-DataFrame für den SOC
    simulatorb1.plot_ladezustand("SOC_lifepo",df)               # ploten und als .png Speichern des Ladezustandes über die Zeit mit der plot_ladezustand Methode
    simulatorb2.plot_ladezustand("SOC_nmc",df)                  # ploten und als .png Speichern des Ladezustandes über die Zeit mit der plot_ladezustand Methode

    # Ergebnisse speichern
    return df

def Output(df):

    # Ergebnisse speichern
    df.to_csv("Output.csv", index=False)

    results = Kenngroessen(df)
    print(f"Gesamtstrecke mit originalen Daten: {results['Gesamtstrecke_Original']:.1f} m")
    print(f"Gesamtstrecke mit geglätteten Daten: {results['Gesamtstrecke_Glatt']:.1f} m")
    print(f"Durchschnittsgeschwindigkeit: {results['Durchschnittsgeschwindigkeit']:.1f} m/s")
    print(f"Maximalleistung: {results['P_max']:.1f} W")
    print(f"Gesamtzeit: {results['Gesamtzeit']}")
    print(f"Gesamter Anstieg: {results['Anstieg']:.1f} m")
    print(f"Gesamter Abstieg: {results['Abstieg']:.1f} m")

    # Ergebnisse speichern
    df.to_csv("Output.csv", index=False)

    for spalte in df.columns:
        if spalte in ["lat", "lon", "time", "ele", "ele_glatt", "ds", "dt", "dh","F_D", "F_H", "F_A", "F_R", "F_Antrieb", "temp", "phi_rad", "lat_glatt", "lon_glatt", "time_s","SOC_lifepo","SOC_nmc","SOC"]:
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
        elif spalte == "ele":
            plt.ylabel(f"{spalte} [m]")
            plt.title("Höhe über der Zeit")

        plt.grid(True)
        plt.savefig(f"{spalte}.png", dpi=300, bbox_inches="tight")
        plt.close()

    return results

def parameterstudie(
    df: pd.DataFrame,
    parameter,
    werte,
    kennwert = "P_max"
):
    logging.warning(f"Start der Parameterstudie")
    x = []
    y = []
    for wert in werte:
        parameter_dict = {
            "masse": 80,
            "A": 0.5625,
            "r_inch": 27
        }
        parameter_dict[parameter] = wert
        df = simulation(df.copy(), **parameter_dict)
        results = Kenngroessen(df)
        x.append(wert)
        y.append(results[kennwert])
    plt.figure(figsize=(8,5))
    plt.plot(
        x,
        y,
        marker="o",
        linewidth=2
    )

    plt.xlabel(parameter)
    plt.ylabel(kennwert)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(
        f"Parameterstudie_{parameter}_{kennwert}.png",
        dpi=300
    )
    logging.warning(f"Ende der Parameterstudie")

if __name__ == "__main__":
    try:
        df = pd.read_csv("final_project_input_data.csv", sep=";")
        results = {}
        df = simulation(df, masse=80, A=0.5625, r_inch=27)
        Output(df)

        #Ploten der Strecke auf einer Karte
        PlotStreckeAufKarte(df)
        
        # höhenprofil ploten
        hoehenprofil_steigung(df)

        #Reverse Geocoding ( Ermitten der orte entlang der Strecke)
        orte = reverse_geocoding(df)
        print(orte)   

        # Parameterstudien
        parameterstudie(df, parameter="masse", werte=np.arange(60,121,5))
        parameterstudie(df, parameter="A", werte=np.arange(0.5,5,0.5))
        parameterstudie(df, parameter="r_inch", werte=np.arange(20,31,1))

        #print(results)
        #results = Kenngroessen(df)
        #create_latex_report(results, filename="Auswertung", title="Auswertung der Fahrraddaten")
    except Exception as e:
        logging.error(f"Kritischer Fehler im Hauptprogramm: {e}", exc_info=True)
