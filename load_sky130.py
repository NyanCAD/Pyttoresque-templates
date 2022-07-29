from PySpice.Spice.Parser import SpiceParser
from glob import glob
import sys
import os
import asyncio
from aiocouch import CouchDB

prefix = os.environ['CONDA_PREFIX']
pdk = "sky130"
decl = f".lib {prefix}/share/pdk/sky130A/libs.tech/ngspice/sky130.lib.spice {{corner}}"
dburl = "https://c6be5bcc-59a8-492d-91fd-59acc17fef02-bluemix.cloudantnosqldb.appdomain.cloud"
dbname = "schematics"
user = None
password = None

files = sys.argv[1:]
devices = set()
for f in files:
    try:
        p = SpiceParser(f)
    except Exception as e:
        print(e)
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
    cell = await db.get(docid, {})
    cell["models"] = {}
    cell["name"] = cellname
    for m in models:
        if "rf" not in m:
            cell["models"][m] = {
                "name": m,
                "type": "spice",
                "reftempl": "X{name} {ports} {properties}" if cellname != "resistor" else "X{name} {ports} GND " + m,
                "decltempl": decl,
                "categories": [pdk]
            }
    await cell.save()

async def main():
    async with CouchDB(dburl, user=user, password=password) as couchdb:
        db = await couchdb[dbname]
        await add_models(db, "pmos", pmos)
        await add_models(db, "nmos", nmos)
        await add_models(db, "diode", diode)
        await add_models(db, "capacitor", capacitor)
        await add_models(db, "resistor", resistor)
        await add_models(db, "inductor", inductor)
        await add_models(db, "npn", npn)
        await add_models(db, "pnp", pnp)

asyncio.run(main())