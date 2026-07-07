import logging

logging.basicConfig(format="%(asctime)s:%(levelname)s: %(message)s", level=logging.INFO, filename="Batterypack.log")
class BatteryPack:
    """
    Simple model of a battery pack as a single cell.
    The battery is modeled as an ideal voltage source (open circuit voltage) in series with an internal resistance.
    The open circuit voltage is a linear function of the state of charge (SoC).
    The SoC is updated based on the applied current and duration.
    """
    def __init__(
        self,
        capacity_nom_cell_Ah : float = 10,
        initial_soc: float = 1.0,
        anz_parallel = 2,
        
  
    ):
        self.anz_parallel = anz_parallel
        self.anz_serie = 10
        self.internal_resistance_cell_mOhm = 8
        self.internal_resistance_pack_mOhm = self.anz_serie * self.internal_resistance_cell_mOhm / self.anz_parallel
        self.internal_resistance_pack_Ohm = self.internal_resistance_pack_mOhm  /1000 # mOhm in Ohm
        self.capacity_nom_As = capacity_nom_cell_Ah * anz_parallel * 60 * 60 # ah in as umwandeln
        self.vmin = 3.2 * self.anz_serie
        self.vmax = 4.2 * self.anz_serie

        if not (0.0 <= initial_soc <= 1.0):
            raise ValueError(f"Ungültiger initial_soc: {initial_soc}. Der SoC muss zwischen 0.0 und 1.0 liegen!")
        
        self.soc = initial_soc
        logging.info("BatteryPack erfolgreich initialisiert.")


    def apply_current(self, current: float, duration: float) -> None:
        """Modify the SoC based on the applied current & duration"""
        self.soc = self.soc - (current * duration ) / self.capacity_nom_As
        self.soc = max(0, min(1, self.soc))
        if self.soc == 0:
            logging.warning("Batterie ist vollständig entladen!")
        if self.soc == 1:
            logging.info("Batterie ist vollständig geladen.")

    def is_empty(self) -> bool:
        pass

    def is_full(self) -> bool:
        pass
    
    def uoc(self) -> float:
        return self.vmin + self.soc * (self.vmax - self.vmin)

    def voltage(self, current: float = 0.0) -> float:
        """Return the current voltage of the battery at the SoC and the given current flow"""
        # uoc = self.vmin + self.soc * (self.vmax - self.vmin)
        u = self.uoc() - self.internal_resistance_pack_Ohm * current
        return max(0.0,u) 

    def __str__(self):
        return f"BatteryPack(SoC={self.soc * 100:.1f}%, V={self.voltage():.2f} V)"




if __name__ == "__main__":

    battery = BatteryPack(capacity_nom_cell_Ah=10, initial_soc=0.7, Vmin=32.0, Vmax=42.0)
    print(battery)

    battery.apply_current(current=5.0, duration=300.0)
    print(battery)
    battery.apply_current(current=10.0, duration=240.0)
    print(battery)
    battery.apply_current(current=-5.0, duration=150.0)

    print(battery)
