class BatteryPack:
    """
    Simple model of a battery pack as a single cell.
    The battery is modeled as an ideal voltage source (open circuit voltage) in series with an internal resistance.
    The open circuit voltage is a linear function of the state of charge (SoC).
    The SoC is updated based on the applied current and duration.
    """

    def __init__(
        self,
        capacity_nom_Ah: float,
        internal_resistance_mOhm: float = 80.0,
        initial_soc: float = 1.0,
        Vmin: float = 3.0,
        Vmax: float = 4.2,
    ):
        self.capacity_nom_As = capacity_nom_Ah * 60 * 60 # ah in as umwandeln
        self.internal_resistance_mOhm = internal_resistance_mOhm /1000 # mOhm in Ohm
        self.soc = initial_soc
        self.vmin = Vmin
        self.vmax = Vmax

    def apply_current(self, current: float, duration: float) -> None:
        """Modify the SoC based on the applied current & duration"""
        self.soc = self.soc - (current * duration ) / self.capacity_nom_As
        self.soc = max(0, min(1, self.soc))

    def is_empty(self) -> bool:
        pass

    def is_full(self) -> bool:
        pass

    def voltage(self, current: float = 0.0) -> float:
        """Return the current voltage of the battery at the SoC and the given current flow"""
        uoc = self.vmin + self.soc * (self.vmax - self.vmin)
        u = uoc - self.internal_resistance_mOhm * current
        return u 

    def __str__(self):
        return f"BatteryPack(SoC={self.soc * 100:.1f}%, V={self.voltage():.2f} V)"




if __name__ == "__main__":

    battery = BatteryPack(capacity_nom_Ah=10, initial_soc=0.7, Vmin=32.0, Vmax=42.0)
    print(battery)

    battery.apply_current(current=5.0, duration=300.0)
    print(battery)
    battery.apply_current(current=10.0, duration=240.0)
    print(battery)
    battery.apply_current(current=-5.0, duration=150.0)

    print(battery)
