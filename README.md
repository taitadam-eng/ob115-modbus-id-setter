# ob115-modbus-id-setter
Python script to change the Modbus RTU slave ID of an OB115-MOD energy meter (also sold as EM115 / GivEnergy EM115) over RS485. Works around the meter's undocumented quirk of rejecting FC 0x06 writes with exception 7 (NAK) — uses FC 0x10 against register 0x0524 instead.
