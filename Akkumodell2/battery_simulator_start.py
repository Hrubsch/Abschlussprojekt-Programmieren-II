from battery_pack_start import BatteryPack
import matplotlib.pyplot as plt
from plotting_utils import (
    plot_current_profile,
    plot_voltage_profile,
    plot_voltage_and_current_profile,
)

class BatterySimulator:
    """Simple simulator for a battery pack. The simulator applies a current profile to the battery pack and records the voltage profile."""

    def __init__(self, battery_pack: BatteryPack) -> None:
        self.voltage_profile = []
        self.battery_pack = battery_pack

    def simulate(self, current_profile: list[float], duration_profile: list[float]) -> None:
        self.voltage_profile = []
        self.voltage_profile.append(self.battery_pack.voltage()) 
        
        for i, j in zip(current_profile, duration_profile):
            self.battery_pack.apply_current(i,j)
            v = self.battery_pack.voltage(i)
            self.voltage_profile.append(v)

    
    # Enwicklung des Ladezustandes des Akkus über die Fahrt
    def simulation_ladezustand(self, df , battery : BatteryPack = BatteryPack()):
        """Simulation des Ladezustands des Akkus über die Fahrt"""

        df_bereinigt = df.dropna(subset=["dt"]) #ohne erste Zeile, weil keine Werte

        soc_liste = []
        soc_liste.append(battery.soc )

        for i,j in df_bereinigt.iterrows():
            dt = j["dt"]
            I_motor = j["I_motor"]
            battery.apply_current(I_motor, dt)
            soc_liste.append(battery.soc ) 

        df["SOC"] = soc_liste
        return df["SOC"]

    def plot_ladezustand(self, df):
        """ploten des Ladezustandes"""
        fig, ax = plt.subplots()
        ax.plot(df["Gesamtzeit"],df["SOC"] * 100,label = "SOC(%)")
        ax.set_xlabel("t / s")
        ax.set_ylabel("SOC / %")
        ax.set_title("Ladezustand des Akkus über die Zeit")
        ax.grid()
        ax.legend(loc="upper right")
        plt.show()


if __name__ == "__main__":
    load_current = [3.0, 11.0, 4.0, -1.5, 1.0]
    load_durations = [300.0, 240.0, 90.0, 150.0, 120.0]

    plot_current_profile(current_profile=load_current, duration_profile=load_durations)

    battery = BatteryPack(capacity_nom_cell_Ah=10, initial_soc=0.7, anz_parallel = 2)
    bat_sim = BatterySimulator(battery)
    bat_sim.simulate(load_current, load_durations)
    print(battery)

    plot_voltage_profile(voltage_profile=bat_sim.voltage_profile, duration_profile=load_durations)
    plot_voltage_and_current_profile(bat_sim.voltage_profile, load_current, load_durations)

