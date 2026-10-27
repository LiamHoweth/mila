#pragma once

#include <Arduino.h>

// ESP32 DevKit VSPI defaults. Change these to match the actual board wiring.
constexpr uint8_t kCanSckPin = 18;
constexpr uint8_t kCanMisoPin = 19;
constexpr uint8_t kCanMosiPin = 23;
constexpr uint8_t kCanChipSelectPin = 5;
constexpr uint8_t kCanInterruptPin = 4;  // MCP2518FD build only.

// TX is allowed only while this pin is physically jumpered to GND and the
// operator has typed ARM over serial. Opening the jumper stops TX immediately.
constexpr uint8_t kTxEnablePin = 27;

// The current Nissan openpilot buses use Classical CAN at 500 kbit/s. Confirm
// the target bus with a scope/analyzer before changing this value.
constexpr uint32_t kCanBitrate = 500000;

// Read the marking on the module's oscillator before choosing these values.
constexpr uint8_t kMcp2515OscillatorMhz = 8;
constexpr uint8_t kMcp2518FdOscillatorMhz = 40;

// Bench-only standard identifier. It is absent from the current upstream
// nissan_leaf_2018 DBC, but that does not make it safe to transmit in a car.
constexpr uint16_t kTestCanId = 0x5A5;
constexpr uint32_t kTransmitPeriodMs = 500;   // 2 Hz
constexpr uint32_t kTransmitWindowMs = 30000; // Auto-disarm after 30 seconds
constexpr uint8_t kProtocolVersion = 1;
