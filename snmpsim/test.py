# test_snmp.py
from pysnmp.hlapi.asyncio import *
import asyncio

async def test():
    err, status, idx, varBinds = await getCmd(
        SnmpEngine(),
        CommunityData('public'),
        UdpTransportTarget(('127.0.0.1', 1611)),
        ContextData(),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0'))
    )
    if err:
        print(f"Error: {err}")
    else:
        for oid, val in varBinds:
            print(f"{oid} = {val}")

asyncio.run(test())