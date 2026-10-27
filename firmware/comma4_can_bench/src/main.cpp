#include <Arduino.h>
#include <SPI.h>

#include "can_config.h"

#if defined(MILA_CAN_CONTROLLER_MCP2515) == defined(MILA_CAN_CONTROLLER_MCP2518FD)
#error "Select exactly one CAN controller build target"
#endif

#if defined(MILA_CAN_CONTROLLER_MCP2515)
#include <mcp2515.h>
MCP2515 canController(kCanChipSelectPin);
#else
#include <ACAN2517FD.h>
ACAN2517FD canController(kCanChipSelectPin, SPI, kCanInterruptPin);
#endif

namespace {

bool armed = false;
uint16_t sequence = 0;
uint32_t armedAtMs = 0;
uint32_t nextTransmitMs = 0;
char commandBuffer[16] = {};
size_t commandLength = 0;

bool txJumperInstalled() {
  return digitalRead(kTxEnablePin) == LOW;
}

void printFrame(uint32_t id, const uint8_t *data, uint8_t length, const char *prefix) {
  Serial.printf("%s id=0x%03lX dlc=%u data=", prefix,
                static_cast<unsigned long>(id), length);
  for (uint8_t i = 0; i < length; ++i) {
    Serial.printf("%02X", data[i]);
  }
  Serial.println();
}

#if defined(MILA_CAN_CONTROLLER_MCP2515)
CAN_CLOCK mcp2515Clock() {
  if (kMcp2515OscillatorMhz == 8) {
    return MCP_8MHZ;
  }
  if (kMcp2515OscillatorMhz == 16) {
    return MCP_16MHZ;
  }
  return MCP_20MHZ;
}

CAN_SPEED mcp2515Bitrate() {
  switch (kCanBitrate) {
    case 125000:
      return CAN_125KBPS;
    case 250000:
      return CAN_250KBPS;
    case 500000:
      return CAN_500KBPS;
    case 1000000:
      return CAN_1000KBPS;
    default:
      Serial.println("Unsupported MCP2515 bitrate; using 500 kbit/s");
      return CAN_500KBPS;
  }
}
#else
ACAN2517FDSettings::Oscillator mcp2518FdOscillator() {
  if (kMcp2518FdOscillatorMhz == 4) {
    return ACAN2517FDSettings::OSC_4MHz10xPLL;
  }
  if (kMcp2518FdOscillatorMhz == 20) {
    return ACAN2517FDSettings::OSC_20MHz;
  }
  return ACAN2517FDSettings::OSC_40MHz;
}
#endif

bool beginCan() {
  pinMode(kCanChipSelectPin, OUTPUT);
  digitalWrite(kCanChipSelectPin, HIGH);
  SPI.begin(kCanSckPin, kCanMisoPin, kCanMosiPin, kCanChipSelectPin);

#if defined(MILA_CAN_CONTROLLER_MCP2515)
  if (canController.reset() != MCP2515::ERROR_OK) {
    Serial.println("MCP2515 reset failed");
    return false;
  }
  if (canController.setBitrate(mcp2515Bitrate(), mcp2515Clock()) != MCP2515::ERROR_OK) {
    Serial.println("MCP2515 bitrate configuration failed; verify the crystal marking");
    return false;
  }
#if defined(MILA_CAN_INTERNAL_LOOPBACK)
  const MCP2515::ERROR modeResult = canController.setLoopbackMode();
#else
  const MCP2515::ERROR modeResult = canController.setNormalMode();
#endif
  if (modeResult != MCP2515::ERROR_OK) {
    Serial.println("MCP2515 mode configuration failed");
    return false;
  }
#else
  ACAN2517FDSettings settings(mcp2518FdOscillator(), kCanBitrate,
                              DataBitRateFactor::x1);
#if defined(MILA_CAN_INTERNAL_LOOPBACK)
  settings.mRequestedMode = ACAN2517FDSettings::InternalLoopBack;
#else
  // The Nissan test is Classical CAN. Do not emit CAN FD frames on this bus.
  settings.mRequestedMode = ACAN2517FDSettings::Normal20B;
#endif
  const uint32_t errorCode = canController.begin(settings, [] { canController.isr(); });
  if (errorCode != 0) {
    Serial.printf("MCP2518FD configuration failed: 0x%08lX\n",
                  static_cast<unsigned long>(errorCode));
    return false;
  }
  Serial.printf("MCP2518FD actual arbitration bitrate: %lu bit/s\n",
                static_cast<unsigned long>(settings.actualArbitrationBitRate()));
#endif
  return true;
}

void stopTransmit(const char *reason) {
  if (armed) {
    Serial.printf("TX stopped: %s\n", reason);
  }
  armed = false;
}

void handleCommand(const char *command) {
  if (strcasecmp(command, "ARM") == 0) {
    if (!txJumperInstalled()) {
      Serial.printf("ARM rejected: jumper GPIO %u to GND first\n", kTxEnablePin);
      return;
    }
    armed = true;
    armedAtMs = millis();
    nextTransmitMs = armedAtMs;
    Serial.printf("TX armed for %lu seconds; type STOP or remove the jumper\n",
                  static_cast<unsigned long>(kTransmitWindowMs / 1000));
  } else if (strcasecmp(command, "STOP") == 0) {
    stopTransmit("operator command");
  } else if (strcasecmp(command, "STATUS") == 0) {
    Serial.printf("status armed=%s jumper=%s sequence=%u\n",
                  armed ? "yes" : "no", txJumperInstalled() ? "closed" : "open",
                  sequence);
  } else if (command[0] != '\0') {
    Serial.println("Commands: ARM, STOP, STATUS");
  }
}

void readSerialCommands() {
  while (Serial.available() > 0) {
    const char value = static_cast<char>(Serial.read());
    if (value == '\n' || value == '\r') {
      if (commandLength > 0) {
        commandBuffer[commandLength] = '\0';
        handleCommand(commandBuffer);
        commandLength = 0;
      }
    } else if (commandLength < sizeof(commandBuffer) - 1) {
      commandBuffer[commandLength++] = value;
    }
  }
}

bool sendHeartbeat() {
  const uint8_t payload[8] = {
      'M', 'I', 'L', 'A',
      static_cast<uint8_t>(sequence & 0xFF),
      static_cast<uint8_t>((sequence >> 8) & 0xFF),
#if defined(MILA_CAN_CONTROLLER_MCP2515)
      0x15,
#else
      0x18,
#endif
      kProtocolVersion,
  };

#if defined(MILA_CAN_CONTROLLER_MCP2515)
  struct can_frame frame = {};
  frame.can_id = kTestCanId;
  frame.can_dlc = sizeof(payload);
  memcpy(frame.data, payload, sizeof(payload));
  const bool sent = canController.sendMessage(&frame) == MCP2515::ERROR_OK;
#else
  CANFDMessage frame;
  frame.id = kTestCanId;
  frame.ext = false;
  frame.type = CANFDMessage::CAN_DATA;
  frame.len = sizeof(payload);
  memcpy(frame.data, payload, sizeof(payload));
  const bool sent = canController.tryToSend(frame);
#endif

  if (sent) {
    printFrame(kTestCanId, payload, sizeof(payload), "TX queued");
    ++sequence;
  } else {
    Serial.println("TX queue failure");
  }
  return sent;
}

#if defined(MILA_CAN_INTERNAL_LOOPBACK)
void receiveLoopbackFrames() {
#if defined(MILA_CAN_CONTROLLER_MCP2515)
  struct can_frame frame = {};
  if (canController.readMessage(&frame) == MCP2515::ERROR_OK) {
    printFrame(frame.can_id, frame.data, frame.can_dlc, "RX");
  }
#else
  CANFDMessage frame;
  if (canController.available() && canController.receive(frame)) {
    printFrame(frame.id, frame.data, frame.len, "RX");
  }
#endif
}
#endif

void printControllerHealth() {
#if defined(MILA_CAN_CONTROLLER_MCP2515)
  const uint8_t flags = canController.getErrorFlags();
  if (flags != 0) {
    Serial.printf("MCP2515 EFLG=0x%02X (check bitrate, ACK, wiring, and termination)\n", flags);
  }
#else
  const uint32_t counters = canController.errorCounters();
  if (counters != 0) {
    Serial.printf("MCP2518FD error counters=0x%08lX\n",
                  static_cast<unsigned long>(counters));
  }
#endif
}

}  // namespace

void setup() {
  Serial.begin(115200);
  delay(1000);
  pinMode(kTxEnablePin, INPUT_PULLUP);

  Serial.println("MiLa ESP32 -> comma 4 CAN bench test");
#if defined(MILA_CAN_INTERNAL_LOOPBACK)
  Serial.println("Mode: controller internal loopback (no CAN bus required)");
#else
  Serial.println("Mode: external Classical CAN bus");
#endif
  Serial.printf("CAN ID=0x%03X bitrate=%lu TX-enable GPIO=%u\n", kTestCanId,
                static_cast<unsigned long>(kCanBitrate), kTxEnablePin);

  if (!beginCan()) {
    Serial.println("CAN initialization failed; halted");
    while (true) {
      delay(1000);
    }
  }
  Serial.println("Ready. Jumper TX-enable to GND, then type ARM.");
}

void loop() {
  readSerialCommands();

  if (armed && !txJumperInstalled()) {
    stopTransmit("physical TX-enable jumper opened");
  }
  if (armed && millis() - armedAtMs >= kTransmitWindowMs) {
    stopTransmit("30-second window expired");
  }
  if (armed && static_cast<int32_t>(millis() - nextTransmitMs) >= 0) {
    sendHeartbeat();
    nextTransmitMs += kTransmitPeriodMs;
  }

#if defined(MILA_CAN_INTERNAL_LOOPBACK)
  receiveLoopbackFrames();
#endif

  static uint32_t nextHealthMs = 0;
  if (static_cast<int32_t>(millis() - nextHealthMs) >= 0) {
    printControllerHealth();
    nextHealthMs = millis() + 2000;
  }
  delay(1);
}
