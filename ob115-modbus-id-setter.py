"""
Change the Modbus ID of an OB115-MOD / EM115 energy meter.

Register 0x0524 (1316 decimal) holds the Modbus slave ID per the
manufacturer's register map. We write the new ID there, then verify
by reading it back on the new ID.

Requires: pip install pymodbus pyserial
"""

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
import sys
import time

# --- EDIT THESE --------------------------------------------------------------
PORT         = "COM3"   # "COM3" on Windows
BAUDRATE     = 9600             # OB115-MOD default
PARITY       = "N"              # default: None
STOPBITS     = 1
CURRENT_ID   = 3                # meter's current Modbus address
NEW_ID       = 1                # address you want (1-247 is safe; spec allows up to 255)
MODBUS_ID_REGISTER = 0x0524     # holding register for Modbus ID
# -----------------------------------------------------------------------------


def _id_kwarg(client) -> str:
    """pymodbus renamed `slave=` to `device_id=` in 3.9+. Detect which to use."""
    import inspect
    params = inspect.signature(client.read_holding_registers).parameters
    if "device_id" in params:
        return "device_id"
    return "slave"


def main() -> int:
    if not 1 <= NEW_ID <= 247:
        print(f"NEW_ID {NEW_ID} out of range (1-247).")
        return 1

    client = ModbusSerialClient(
        port=PORT,
        baudrate=BAUDRATE,
        parity=PARITY,
        stopbits=STOPBITS,
        bytesize=8,
        timeout=1,
    )

    if not client.connect():
        print(f"Could not open serial port {PORT}.")
        return 1

    id_kw = _id_kwarg(client)  # "slave" on old pymodbus, "device_id" on 3.9+

    try:
        # 1. Confirm we can talk to the meter on its current ID.
        rr = client.read_holding_registers(
            address=MODBUS_ID_REGISTER, count=1, **{id_kw: CURRENT_ID}
        )
        if rr.isError():
            print(f"Couldn't read from meter at ID {CURRENT_ID}: {rr}")
            return 1
        print(f"Meter at ID {CURRENT_ID} currently reports Modbus ID = {rr.registers[0]}")

        if rr.registers[0] == NEW_ID:
            print("Meter is already set to the target ID. Nothing to do.")
            return 0

        # 2. Write the new ID.
        #    The OB115-MOD accepts ID changes ONLY via FC 0x10 (write
        #    multiple registers) to 0x0524, with a 16-bit integer value.
        #    FC 0x06 (write single register) returns exception 7 (NAK).
        wr = client.write_registers(
            address=MODBUS_ID_REGISTER, values=[NEW_ID], **{id_kw: CURRENT_ID}
        )
        if wr.isError():
            print(f"Write failed: {wr}")
            return 1
        print(f"Wrote new ID {NEW_ID} to meter.")

        # 3. Give the meter a moment to commit to EEPROM and switch IDs.
        time.sleep(1.0)

        # 4. Verify by reading back on the NEW ID.
        check = client.read_holding_registers(
            address=MODBUS_ID_REGISTER, count=1, **{id_kw: NEW_ID}
        )
        if check.isError():
            print(
                f"Wrote OK but couldn't read back on ID {NEW_ID}. "
                f"Try power-cycling the meter, then query it on the new ID."
            )
            return 1

        print(f"Verified: meter now responds on ID {NEW_ID} "
              f"(register reads {check.registers[0]}).")
        return 0

    except ModbusException as e:
        print(f"Modbus error: {e}")
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
