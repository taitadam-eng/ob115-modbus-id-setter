# ob115-modbus-id-setter

Change the Modbus RTU slave ID of an **OB115-MOD** energy meter from a Python script.

The OB115-MOD is a single-phase 100A MID-certified energy meter from Owen Brothers Metering, also sold as the **EM115** and the **GivEnergy EM115**. It's widely used in UK solar and sub-metering installations, but its Modbus configuration behaviour is poorly documented — the manufacturer's manual simply says *"the user can program the meter parameter by sending commands via the RS485 port"* without specifying which registers, function codes, or data formats to use.

After some trial and error, the working combination is:

- **Register:** `0x0524` (decimal 1316)
- **Function code:** `0x10` (Write Multiple Registers) — `0x06` always returns exception code 7 (NAK)
- **Value:** a single 16-bit unsigned integer

This script wraps that sequence in a reusable utility: it reads the current ID, writes the new one, then verifies the change by reading back on the new ID.

## Requirements

- Python 3.9+
- A USB-to-RS485 adapter wired to the meter's RS485 terminals
- `pymodbus` and `pyserial`

```bash
pip install pymodbus pyserial
```

The script is compatible with both pymodbus 3.8 (which uses `slave=`) and 3.9+ (which renamed it to `device_id=`) — it detects which your version expects at runtime.

## Wiring

Connect your RS485 adapter to the meter:

| Meter terminal | Adapter |
|----------------|---------|
| 10             | A / TX+/RX+ / D+ |
| 9              | B / TX-/RX- / D-  |
| 8              | GND (G485), optional but recommended on long runs |

The meter must be powered (230V AC on terminals 1/2) for it to respond.

## Configuration

Open `change_ob115_id.py` and edit the parameters at the top of the file:

```python
PORT         = "COM3"    # Windows: "COM3", "COM4" etc.  Linux: "/dev/ttyUSB0"
BAUDRATE     = 9600      # OB115-MOD factory default
PARITY       = "N"       # "N" (None), "E" (Even), or "O" (Odd). Default: None
STOPBITS     = 1
CURRENT_ID   = 1         # The meter's CURRENT Modbus address (1-247)
NEW_ID       = 2         # The address you want it to have (1-247)
MODBUS_ID_REGISTER = 0x0524   # Don't change this
```

### What each parameter means

- **`PORT`** — The serial port your RS485 adapter appears on.
  - On **Windows**, find this in Device Manager → *Ports (COM & LPT)*. It'll look like `COM3`, `COM4`, etc.
  - On **Linux/macOS**, it's usually `/dev/ttyUSB0` (for FTDI/CH340 adapters) or `/dev/ttyACM0`.
- **`BAUDRATE`** — Must match what the meter is currently using. Factory default is **9600**. If someone changed it, try `1200`, `2400`, `4800`, `9600`, or `19200` until the read succeeds.
- **`PARITY`** — Must match the meter. Factory default is `"N"` (None). Other options are `"E"` (Even) and `"O"` (Odd).
- **`STOPBITS`** — Leave at `1` unless you've explicitly changed it.
- **`CURRENT_ID`** — The address the meter answers on **right now**. Factory default is **1**. GivEnergy-branded units are often shipped pre-configured as ID 1 or ID 2. If you don't know, see [Finding the current ID](#finding-the-current-id) below.
- **`NEW_ID`** — The address you want to set. Valid range is **1–247** (the Modbus spec reserves 248–255).
- **`MODBUS_ID_REGISTER`** — Don't change this. `0x0524` is the confirmed register for the Modbus slave ID on this meter.

## Usage

Once the parameters are set:

```bash
python change_ob115_id.py
```

Expected output on success:

```
Meter at ID 1 currently reports Modbus ID = 1
Wrote new ID 2 to meter.
Verified: meter now responds on ID 2 (register reads 2).
```

The new ID takes effect immediately — no power cycle needed.

## Finding the current ID

If you don't know what address the meter is currently on, you have two options:

1. **Read it off the LCD.** The OB115-MOD cycles through a series of display screens; one of them is labelled `iD xxx` and shows the current Modbus address.
2. **Scan for it.** Use a tool like `mbpoll`, QModMaster, or the included diagnostic script (see below) and try reading register `0x0524` from each address 1 through 247 until one replies.

## Troubleshooting

### `Couldn't read from meter at ID X` (timeout)

- Double-check `PORT` matches your actual adapter.
- Verify `BAUDRATE`, `PARITY`, and `CURRENT_ID` match the meter's current settings.
- Make sure nothing else is holding the serial port open (e.g. a previous Python session, the GivEnergy portal, another Modbus tool).
- Check A/B wiring isn't swapped — some adapters label them backwards.
- On long runs (>10m) add a 120Ω termination resistor across A/B at the far end.

### `ExceptionResponse ... exception_code=7` (NAK)

This means the meter rejected the write. If the script is using the current version (function code 0x10 / Write Multiple Registers), this shouldn't happen. If you're hand-rolling your own Modbus client, make sure you're **not** using FC 0x06 (Write Single Register) — it always NAKs on this meter.

### Write succeeds but verify fails

Power-cycle the meter and try reading on the new ID manually. Some firmware revisions commit to EEPROM on power-off.

### Diagnostic script

If something unexpected happens, `diagnose_ob115.py` probes multiple candidate registers and attempts writes with several function-code/encoding combinations, reporting the result of each. Useful if you're dealing with a firmware revision that differs from the one this repo was tested against.

## Technical reference

Confirmed register map for Modbus configuration (OB115-MOD, firmware as tested):

| Register | Parameter   | Format   | Write FC | Notes |
|----------|-------------|----------|----------|-------|
| `0x0524` | Modbus ID   | uint16   | `0x10`   | 1–247. FC `0x06` returns NAK |
| `0x0525` | Baud rate   | uint16   | `0x10`   | Hex codes per manual: `0x04B0`=1200, `0x0960`=2400, `0x12C0`=4800, `0x2580`=9600, `0x4B00`=19200 |
| `0x0526` | Parity/stop | uint16   | `0x10`   | `0x0000` = None |

## Related products

This script should also work on the following, which share the same firmware family:

- Owen Brothers **OB115-MOD** (original)
- Owen Brothers **OB115-MOD-DO** (with digital output) — likely compatible, not tested
- MetersUK **EM115-MOD**
- GivEnergy **EM115** (rebadged OB115-MOD)

It will **not** work on the OB115-MOD-V2, which uses Eastron SDM registers (float-encoded, different addresses).

## Licence

MIT
