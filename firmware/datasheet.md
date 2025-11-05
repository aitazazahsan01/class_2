# Thermostat Controller — Interface Datasheet

**Component:** `thermostat_controller` firmware · **Interface:** line-based command protocol over the HIL serial link (simulated here as stdin/stdout)

## Safe operating range

The sensor input is valid over **-40°C to 85°C**. Readings at or beyond either bound are outside the safe operating envelope and must trigger a protective shutdown of both actuators.

## Warning margin

Readings within **5°C** of either safety bound (i.e., -40 to -35°C, or 80 to 85°C) should be reported as an elevated-risk state distinct from both normal operation and full shutdown, so upstream systems can respond before a hard cutoff is required.

## Target setpoint

The controller accepts a target setpoint via `SET_TARGET`. Setpoints must fall within the safe operating range above; the interface must reject out-of-range setpoint requests rather than silently accepting them.

## Actuators

Two actuators (heater, cooler) are driven based on the difference between the current reading and the target setpoint, with a small hysteresis band to avoid rapid on/off cycling ("chattering") near the setpoint.

## Commands

| Command | Description |
|---|---|
| `SET_TEMP <float>` | Update the current sensor reading |
| `SET_TARGET <float>` | Update the target setpoint |
| `GET_STATE` | Query current safety state |
| `GET_HEATER` | Query heater actuator |
| `GET_COOLER` | Query cooler actuator |
| `RESET` | Restore default configuration |
| `QUIT` | Terminate |

## Safety note

Actuator behavior during a fault condition, and exact fault-recovery semantics, are safety-relevant implementation details — **consult the firmware source directly** for the authoritative behavior rather than assuming standard thermostat semantics apply.
