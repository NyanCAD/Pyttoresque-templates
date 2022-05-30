from PySpice.Spice.Parser import SpiceParser
from glob import glob
import sys
import asyncio
from aiocouch import CouchDB

pdk = "sky130"
decl = ".lib /usr/local/share/pdk/sky130A/libs.tech/ngspice/sky130.lib.spice {corner}"

files = sys.argv[1:]
devices = set()
for f in files:
    try:
        p = SpiceParser(f)
    except Exception as e:
        # print(e)
        continue
    # print([m.name for m in p.models])
    devices.update([m.name for m in p.subcircuits])

pmos = []
nmos = []
diode = []
capacitor = []
resistor = []
inductor = []
npn = []
pnp = []
for d in devices:
    if "pfet" in d:
        pmos.append(d)
    elif "nfet" in d:
        nmos.append(d)
    elif "diode" in d:
        diode.append(d)
    elif "res" in d:
        resistor.append(d)
    elif "cap" in d:
        capacitor.append(d)
    elif "ind" in d:
        inductor.append(d)
    elif "npn" in d:
        npn.append(d)
    elif "pnp" in d:
        pnp.append(d)
    else:
        print(d)
        # raise ValueError(d)

async def add_models(db, cellname, models):
    docid = "models:"+cellname
    cell = await db.get(docid,
        {"name":docid,
         "models":{}})
    for m in models:
        cell["models"][m] = {
            "name": m,
            "type": "spice",
            "reftempl": "X{name} {ports} {properties}",
            "decltempl": decl,
            "categories": [pdk+"_rf" if "rf" in m else pdk]
        }
    await cell.save()

async def main():
    async with CouchDB(
        "http://localhost:5984", user="admin", password="fietspomp"
    ) as couchdb:
        db = await couchdb["schematics"]
        await add_models(db, "pmos", pmos)
        await add_models(db, "nmos", nmos)
        await add_models(db, "diode", diode)
        await add_models(db, "capacitor", capacitor)
        await add_models(db, "resistor", resistor)
        await add_models(db, "inductor", inductor)
        await add_models(db, "npn", npn)
        await add_models(db, "pnp", pnp)

asyncio.run(main())