import logging
import pandas as pd
from battery_pack_start import BatteryPack
import matplotlib.pyplot as plt
from plotting_utils import (
    plot_current_profile,
    plot_voltage_profile,
    plot_voltage_and_current_profile,
)

# Holt den Logger für dieses spezifische Modul
logger = logging.getLogger(__name__)
#logging.basicConfig(format="%(asctime)s:%(levelname)s: %(message)s", level=logging.INFO, filename="Batterysimulator.log")
class BatterySimulator:
    """Simple simulator for a battery pack. The simulator applies a current profile to the battery pack and records the voltage profile."""

    def __init__(self, battery_pack: BatteryPack) -> None:
        self.voltage_profile = []
        self.soc_liste = []
        self.battery_pack = battery_pack
        logging.info("BatterySimulator erfolgreich initialisiert.")

    def simulate(self, current_profile: list[float], duration_profile: list[float]) -> None:
        self.voltage_profile = []
        self.voltage_profile.append(self.battery_pack.voltage()) 
        
        for i, j in zip(current_profile, duration_profile):
            try: 
                self.battery_pack.apply_current(i,j)
                v = self.battery_pack.voltage(i)
                self.voltage_profile.append(v)
            except Exception as e:
                logging.error(f"Fehler während der Standardsimulation: {e}")                

    
    # Enwicklung des Ladezustandes des Akkus über die Fahrt
    def simulation_ladezustand(self, df : pd.DataFrame )-> list[float]:
        """Simulation des Ladezustands des Akkus über die Fahrt"""

        self.soc_liste = []
        logging.info("Starte Simulation des Ladezustands")

        # Prüfen, ob die benötigten Spalten existieren
        required_columns = ["dt", "I_motor"]
        for col in required_columns:
            if col not in df.columns:
                logging.error(f"Spalte '{col}' fehlt im DataFrame! Simulation abgebrochen.")
                raise KeyError(f"Fehler: DataFrame benötigt die Spalte '{col}'")

        for i,j in df.iterrows():
            try:
                dt = j["dt"]
                I_motor = j["I_motor"]

                # Verhindern von negativen zeitschritten
                if dt < 0:
                    logging.warning(f"[Zeile {i}] Negativer Zeitschritt dt={dt} erkannt. Überspringe Schritt.")
                    # Letzten SOC-Wert beibehalten, falls vorhanden, sonst aktuellen
                    self.soc_liste.append(self.battery_pack.soc)
                    continue
                
                self.battery_pack.apply_current(I_motor, dt)

                self.soc_liste.append(self.battery_pack.soc ) 

            except (ValueError, TypeError) as e:
                logging.error(f"[Zeile {i}] Ungültiger Datentyp in den Daten: {e}. Zeile übersprungen.")
                # Letzten SOC-Wert halten, damit die Listenlänge konsistent bleibt
                if self.soc_liste: # if ist True, wenn Liste mindestens ein Element enthält und false, wenn Liste leer ist
                # Wenn die Liste nicht leer ist, nimm das letzte Element
                    fallback_soc = self.soc_liste[-1]
                else:
                # Wenn die Liste noch leer ist, nimm den aktuellen SOC der Batterie
                    fallback_soc = self.battery_pack.soc
                self.soc_liste.append(fallback_soc)
            except Exception as e:
                logging.error(f"[Zeile {i}] Unerwarteter Fehler: {e}")
                raise e
            
        logging.info(f"Simulation beendet. {len(self.soc_liste)} Werte verarbeitet.")    
        return self.soc_liste

    def plot_ladezustand(self, spalten_name,df):
        """ploten des Ladezustandes"""

        fig, ax = plt.subplots()
        ax.plot(df["time_s"],df[spalten_name] * 100,label = "SOC(%)")
        ax.set_xlabel("t / s")
        ax.set_ylabel("SOC / %")
        ax.set_title("Ladezustand des Akkus über die Zeit")
        ax.grid()
        ax.legend(loc="upper right")
        plt.savefig(f"{spalten_name}.png")
        plt.close(fig)
        logging.info(f"Plot des Ladezustands wurde erfolgreich als '{spalten_name}.png' gespeichert.") 
        print(f"Plot des Ladezustands wurde erfolgreich als '{spalten_name}.png' gespeichert.") 


if __name__ == "__main__":
    print("Start der Testläufe")


    # Normaler Fahrbetrieb (Basis)
    print("\n[TEST 1] Normaler Fahrbetrieb:")
    df_normal = pd.DataFrame({
        "dt": [10.0, 10.0, 10.0, 10.0],
        "I_motor": [5.0, 2.0, -1.0, 4.0], # Mischung aus Verbrauch und Rekuperation
        "Gesamtzeit": [10, 20, 30, 40]
    })
    bat1 = BatteryPack(capacity_nom_cell_Ah=10, initial_soc=0.8, anz_parallel=2)
    sim1 = BatterySimulator(bat1)
    df_normal["SOC"] = sim1.simulation_ladezustand(df_normal)

    # Tiefenentladung (SOC < 0%)
    print("\n[TEST 2] Extrem hoher Stromverbrauch (Tiefenentladung):")
    df_empty = pd.DataFrame({
        "dt": [1000.0, 5000.0, 5000.0],
        "I_motor": [100.0, 500.0, 500.0], # Extrem hoher Entladestrom
        "Gesamtzeit": [1000, 6000, 11000]
    })
    bat2 = BatteryPack(capacity_nom_cell_Ah=10, initial_soc=0.2, anz_parallel=2)
    sim2 = BatterySimulator(bat2)
    df_empty["SOC"] = sim2.simulation_ladezustand(df_empty)
    print(f"End-SOC nach Tiefenentladungsversuch: {df_empty['SOC'].iloc[-1] * 100}%") # gibt letzten SOC der BErechnung aus

    # Überladung (SOC > 100%) durch Rekuperation
    print("\n[TEST 3] Extreme Rekuperation (Überladungsschutz):")
    df_overcharge = pd.DataFrame({
        "dt": [2000.0, 2000.0],
        "I_motor": [-200.0, -200.0], # Negativer Strom = Laden
        "Gesamtzeit": [2000, 4000]
    })
    bat3 = BatteryPack(capacity_nom_cell_Ah=10, initial_soc=0.95, anz_parallel=2)
    sim3 = BatterySimulator(bat3)
    df_overcharge["SOC"] = sim3.simulation_ladezustand(df_overcharge)
    print(f"End-SOC nach Überladungsversuch: {df_overcharge['SOC'].iloc[-1] * 100}%")

    # Fehlerhafte Daten (Strings & negative Zeiten)
    print("\n[TEST 4] Fehlerhafte Daten (Strings und negative Deltas):")
    df_corrupt = pd.DataFrame({
        "dt": [10.0, -5.0, 10.0, "keine_zahl"], # Fehlerquellen eingebaut
        "I_motor": [2.0, 4.0, 3.0, 1.0],
        "Gesamtzeit": [10, 15, 25, 35]
    })
    bat4 = BatteryPack(capacity_nom_cell_Ah=10, initial_soc=0.5, anz_parallel=2)
    sim4 = BatterySimulator(bat4)
    df_corrupt["SOC"] = sim4.simulation_ladezustand(df_corrupt)

    #ursprüngliche tests
    load_current = [3.0, 11.0, 4.0, -1.5, 1.0]
    load_durations = [300.0, 240.0, 90.0, 150.0, 120.0]

    plot_current_profile(current_profile=load_current, duration_profile=load_durations)

    battery = BatteryPack(capacity_nom_cell_Ah=10, initial_soc=0.7, anz_parallel = 2)
    bat_sim = BatterySimulator(battery)
    bat_sim.simulate(load_current, load_durations)
    print(battery)

    plot_voltage_profile(voltage_profile=bat_sim.voltage_profile, duration_profile=load_durations)
    plot_voltage_and_current_profile(bat_sim.voltage_profile, load_current, load_durations)
    input("press Enter to cuntinue:")
