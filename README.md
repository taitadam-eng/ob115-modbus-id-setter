Change the Modbus RTU slave ID of an OB115-MOD energy meter from a Python script.
The OB115-MOD is a single-phase 100A MID-certified energy meter from Owen Brothers Metering, also sold as the EM115 and the GivEnergy EM115. It's widely used in UK solar and sub-metering installations, but its Modbus configuration behaviour is poorly documented — the manufacturer's manual simply says "the user can program the meter parameter by sending commands via the RS485 port" without specifying which registers, function codes, or data formats to use.
After some trial and error, the working combination is:

Register: 0x0524 (decimal 1316)
Function code: 0x10 (Write Multiple Registers) — 0x06 always returns exception code 7 (NAK)
Value: a single 16-bit unsigned integer (not a float, unlike the Eastron SDM120 it's often confused with)

This script wraps that sequence in a reusable utility that reads the current ID, writes the new one, and verifies the change by reading back on the new ID. It works with any USB-to-RS485 adapter and supports both old and new pymodbus APIs.
