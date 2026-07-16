import asyncio
from unittest.mock import patch

class Sim:
    VAL = False
    
    def sync_f(self):
        return self.VAL
        
    async def run(self):
        print("in run:", self.VAL)
        return await asyncio.wait_for(asyncio.to_thread(self.sync_f), timeout=3.0)

@patch("__main__.Sim.VAL", True)
async def test_sim():
    s = Sim()
    res = await s.run()
    print("res:", res)

asyncio.run(test_sim())
