from battery_pack_start import BatteryPack

class lifepo4(BatteryPack): 


    def voltage(self, current: float = 0.0) -> float:
        """Return the current voltage of the battery at the SoC and the given current flow"""
        uoc = self.vmin + self.soc**0.3 * (self.vmax - self.vmin)
        u = uoc - self.internal_resistance_mOhm * current
        return u 
    
if __name__ == "__main__":
    b1 = BatteryPack(10.0)
    b2 = lifepo4(10.0)

    print(b1)
    print(b2)

    b1.apply_current(10,120)
    b2.apply_current(10,120)

    print(b1)
    print(b2)
    
    batteries = [b1,b2]

    for b in batteries:
        print(b)
        b.apply_current(10,120)
        print(b)