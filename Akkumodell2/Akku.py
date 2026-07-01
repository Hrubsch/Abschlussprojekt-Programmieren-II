import numpy as np
import matplotlib.pyplot as plt
from .battery_pack_start import BatteryPack

class lifepo(BatteryPack): 
    def __init__(
        self,
        capacity_nom_cell_Ah : float = 10,
        initial_soc: float = 1.0,
        anz_parallel = 2,
  
    ):
        super().__init__( capacity_nom_cell_Ah, initial_soc, anz_parallel)
        self.internal_resistance_cell_mOhm = 8
        self.internal_resistance_pack_mOhm = self.anz_serie * self.internal_resistance_cell_mOhm / self.anz_parallel
        self.internal_resistance_pack_Ohm = self.internal_resistance_pack_mOhm  /1000 # mOhm in Ohm
        self.soc_array = np.array([0.00, 0.04, 0.09, 0.13, 0.17, 0.21, 0.26, 0.30, 0.40, 0.52, 0.64, 0.76, 0.88, 1.00])
        self.uoc_array = np.array([32.00, 35.87, 36.85, 37.56, 37.87, 38.28, 38.81, 39.05, 39.55, 40.27, 40.70, 41.16, 41.65, 42.00])

    def uoc(self) -> float:
        return np.interp(self.soc, self.soc_array, self.uoc_array)
    
class nmc(BatteryPack): 
    def __init__(
        self,
        capacity_nom_cell_Ah : float = 10,
        initial_soc: float = 1.0,
        anz_parallel = 2,
  
    ):
        super().__init__( capacity_nom_cell_Ah, initial_soc, anz_parallel)
        self.internal_resistance_cell_mOhm = 7
        self.internal_resistance_pack_mOhm = self.anz_serie * self.internal_resistance_cell_mOhm / self.anz_parallel
        self.internal_resistance_pack_Ohm = self.internal_resistance_pack_mOhm  /1000 # mOhm in Ohm
        self.soc_array = np.array([0.00, 0.04, 0.09, 0.13, 0.17, 0.21, 0.26, 0.30, 0.40, 0.52, 0.64, 0.76, 0.88, 1.00])
        self.uoc_array = np.array([32.00, 32.61, 33.17, 33.85, 34.24, 34.66, 35.39, 35.65, 36.65, 37.64, 38.91, 40.14, 41.08, 42.00])

    def uoc(self) -> float:
        return np.interp(self.soc, self.soc_array, self.uoc_array)
    

if __name__ == "__main__":

    try:
        # Versuch, eine Batterie mit fehlerhaftem SoC (150%) zu erstellen
        falscher_akku = lifepo(initial_soc=1.5)
    except ValueError as e:
        print(f"Fehler erfolgreich abgefangen: {e}\n")

    b1 = lifepo(capacity_nom_cell_Ah=10.0, initial_soc=1.0)
    b2 = nmc(capacity_nom_cell_Ah=10.0, initial_soc=1.0)
    
    # test der entladung
    print("Entlade Batterien schrittweise")
    for _ in range(5):
        b1.apply_current(current=50.0, duration=300) 
        b2.apply_current(current=50.0, duration=300)

    print(f"Endzustand nach Entladung: Batterie1:{b1} und Batterie2:{b2}")

    #test der kennlinie der beiden akkutypen
    soc_axis = np.linspace(0, 1, 100)
    uoc_lifepo_plot = []
    uoc_nmc_plot = []
    
    for s in soc_axis:
        akku_lfp = lifepo(initial_soc=s)
        akku_nmc = nmc(initial_soc=s)
        uoc_lifepo_plot.append(akku_lfp.uoc())
        uoc_nmc_plot.append(akku_nmc.uoc())

    #ploten des tests
    fig, ax = plt.subplots()
    ax.plot(soc_axis * 100, uoc_lifepo_plot, label = "LiPo Akku Kennlinie")
    ax.plot(soc_axis * 100, uoc_nmc_plot, label = "NMC Akku Kennlinie")
    ax.set_xlabel("SOC / %")
    ax.set_ylabel("Uoc / V")
    ax.grid()
    ax.legend(loc="upper right")
    plt.show()
