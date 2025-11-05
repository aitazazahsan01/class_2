/*
 * thermostat_controller.c
 *
 * Simplified embedded firmware for a thermostat / safety-cutoff controller.
 * This stands in for a real target (e.g., a Zephyr or FreeRTOS application)
 * so the whole pipeline can be developed and tested without real hardware.
 * It is intentionally realistic in one specific way: it has a subtle,
 * safety-critical behavior (a LATCHING shutdown) that is easy to miss if
 * you only skim the docs and don't read the source carefully -- which is
 * exactly the kind of thing a good test-generation agent should catch.
 *
 * Communication protocol (simulates a serial/HIL link over stdin/stdout):
 *   Commands in  (one per line):
 *     SET_TEMP <float>      -> update the simulated temperature sensor reading
 *     SET_TARGET <float>    -> set the desired setpoint temperature
 *     GET_STATE             -> query current safety state
 *     GET_HEATER            -> query heater actuator
 *     GET_COOLER            -> query cooler actuator
 *     RESET                 -> clear a latched SHUTDOWN fault, restore defaults
 *     QUIT                  -> terminate the process
 *
 *   Responses out (one per line):
 *     OK
 *     ERROR <reason>
 *     STATE <NORMAL|WARNING|SHUTDOWN>
 *     HEATER <ON|OFF>
 *     COOLER <ON|OFF>
 *
 * Build:  gcc -O2 -o thermostat_controller thermostat_controller.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MIN_SAFE_TEMP   -40.0
#define MAX_SAFE_TEMP    85.0
#define WARNING_MARGIN    5.0
#define HYSTERESIS        1.0
#define DEFAULT_TARGET   22.0
#define DEFAULT_TEMP     20.0

typedef enum { STATE_NORMAL, STATE_WARNING, STATE_SHUTDOWN } state_t;
typedef enum { OFF, ON } actuator_t;

static double current_temp = DEFAULT_TEMP;
static double target_temp  = DEFAULT_TARGET;
static state_t state       = STATE_NORMAL;
static actuator_t heater   = OFF;
static actuator_t cooler   = OFF;
/* Once SHUTDOWN latches, it stays latched even if temperature returns to a
 * safe range -- only an explicit RESET command clears it. This mirrors how
 * real safety-critical firmware usually behaves: a fault should not silently
 * clear itself just because the sensor reading happened to recover. */
static int shutdown_latched = 0;

static const char *state_name(state_t s) {
    switch (s) {
        case STATE_NORMAL:   return "NORMAL";
        case STATE_WARNING:  return "WARNING";
        case STATE_SHUTDOWN: return "SHUTDOWN";
    }
    return "UNKNOWN";
}

static void update_state(void) {
    if (shutdown_latched) {
        state = STATE_SHUTDOWN;
        return;
    }
    if (current_temp <= MIN_SAFE_TEMP || current_temp >= MAX_SAFE_TEMP) {
        state = STATE_SHUTDOWN;
        shutdown_latched = 1;
    } else if (current_temp <= MIN_SAFE_TEMP + WARNING_MARGIN ||
               current_temp >= MAX_SAFE_TEMP - WARNING_MARGIN) {
        state = STATE_WARNING;
    } else {
        state = STATE_NORMAL;
    }
}

static void update_actuators(void) {
    if (state == STATE_SHUTDOWN) {
        /* Safety rule: actuators are always forced off during shutdown. */
        heater = OFF;
        cooler = OFF;
        return;
    }
    if (current_temp < target_temp - HYSTERESIS) {
        heater = ON;
        cooler = OFF;
    } else if (current_temp > target_temp + HYSTERESIS) {
        heater = OFF;
        cooler = ON;
    }
    /* else: within the hysteresis band -- deliberately leave actuators
       in whatever state they were already in (no chattering). */
}

static void reset_controller(void) {
    current_temp = DEFAULT_TEMP;
    target_temp = DEFAULT_TARGET;
    state = STATE_NORMAL;
    heater = OFF;
    cooler = OFF;
    shutdown_latched = 0;
}

int main(void) {
    char line[256];
    setvbuf(stdout, NULL, _IOLBF, 0); /* line-buffered so the harness sees output immediately */

    while (fgets(line, sizeof(line), stdin)) {
        line[strcspn(line, "\r\n")] = 0; /* strip newline */

        if (strncmp(line, "SET_TEMP ", 9) == 0) {
            current_temp = atof(line + 9);
            update_state();
            update_actuators();
            printf("OK\n");
        } else if (strncmp(line, "SET_TARGET ", 11) == 0) {
            double new_target = atof(line + 11);
            if (new_target < MIN_SAFE_TEMP || new_target > MAX_SAFE_TEMP) {
                printf("ERROR invalid_target\n");
            } else {
                target_temp = new_target;
                update_actuators();
                printf("OK\n");
            }
        } else if (strcmp(line, "GET_STATE") == 0) {
            printf("STATE %s\n", state_name(state));
        } else if (strcmp(line, "GET_HEATER") == 0) {
            printf("HEATER %s\n", heater == ON ? "ON" : "OFF");
        } else if (strcmp(line, "GET_COOLER") == 0) {
            printf("COOLER %s\n", cooler == ON ? "ON" : "OFF");
        } else if (strcmp(line, "RESET") == 0) {
            reset_controller();
            printf("OK\n");
        } else if (strcmp(line, "QUIT") == 0) {
            break;
        } else if (strlen(line) > 0) {
            printf("ERROR unknown_command\n");
        }
    }
    return 0;
}
