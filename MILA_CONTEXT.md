# MiLa — Mobility Intelligence Lab Context

MiLa, the **Mobility Intelligence Lab**, is a research laboratory at the **University of Oklahoma** focused on autonomous vehicles, intelligent transportation, vehicle control, robotics, embedded systems, and artificial intelligence.

The lab is led by **Dr. Bin Xu** in OU's School of Aerospace and Mechanical Engineering.

MiLa works across the complete autonomous-vehicle stack rather than focusing on only one area such as AI or mechanical design. Its research combines software, electronics, embedded systems, sensors, vehicle control, machine learning, robotics, and real-world vehicle testing.

Major areas of work include:

- Autonomous vehicles
- Intelligent transportation
- Drive-by-wire systems
- Embedded systems
- Microcontrollers
- ESP32
- CAN bus
- Vehicle electronics
- Cameras
- LiDAR
- Radar
- GPS / GNSS
- IMUs
- Perception
- Localization
- Path planning
- Machine learning
- Reinforcement learning
- Inverse reinforcement learning
- Model Predictive Control
- Data-driven control
- End-to-end autonomous driving
- Steering control
- Accelerator control
- Brake control
- ROS / ROS 2
- Linux
- C / C++
- Python
- Real-time systems
- Hardware/software integration
- Real-world vehicle testing

# MiLa's Overall Goal

A major goal of MiLa is to make autonomous-driving technology **cheaper, more accessible, practical, and easier to deploy on ordinary production vehicles**.

Traditional autonomous-vehicle research platforms and commercial drive-by-wire conversions can be extremely expensive. MiLa is investigating ways to convert normal production vehicles into autonomous research platforms using relatively inexpensive sensors, microcontrollers, embedded computers, vehicle electronics, and software.

The basic concept is:

Normal Production Vehicle
        ↓
Add Sensors
        ↓
Add Onboard Computer
        ↓
Add Embedded Controllers
        ↓
Interface With Vehicle Electronics
        ↓
Add Autonomous-Driving Software
        ↓
Autonomous Research Vehicle

The broader engineering question is:

> How can autonomous transportation systems be made inexpensive, reliable, adaptable, and practical enough to deploy in real-world transportation?

MiLa is not simply trying to create software that can drive a simulated car. The lab modifies actual vehicles, installs hardware into them, develops algorithms, interfaces with the vehicle's electronics, and performs real-world autonomous-driving experiments.

# The Autonomous-Vehicle Stack

A simplified autonomous-driving system looks like this:

Cameras / LiDAR / Radar / GPS / IMU
                  ↓
          Perception
                  ↓
          Localization
                  ↓
          Path Planning
                  ↓
       Vehicle Controller
                  ↓
          Drive-by-Wire
                  ↓
 Steering / Brake / Accelerator
                  ↓
           Physical Vehicle
                  ↓
      Sensors + CAN Feedback
                  ↓
             Controller
                  ↓
                Repeat

Each layer solves a different engineering problem.

# Sensors

The vehicle first needs information about itself and the surrounding environment.

MiLa research may use sensors such as:

- Cameras
- LiDAR
- Automotive radar
- GPS / GNSS
- IMUs
- Steering-angle sensors
- Wheel-speed information
- Vehicle CAN-bus data

These sensors can provide information about:

- Vehicle position
- Vehicle velocity
- Vehicle heading
- Acceleration
- Lane location
- Nearby vehicles
- Obstacles
- Roads
- Traffic lights
- Stop signs
- Vehicle state

# Perception

Perception converts raw sensor information into information the autonomous-driving software can understand.

For example:

Camera Image
     ↓
Computer Vision / Neural Network
     ↓
Lane Boundaries
Vehicles
Pedestrians
Traffic Lights
Stop Signs
Obstacles

MiLa works on perception and end-to-end autonomous-driving methods in addition to more traditional modular autonomous-driving systems.

# Localization

Localization answers the question:

> Where is the vehicle and how is it moving?

The system may combine information from:

- GPS
- IMU
- Maps
- Cameras
- Wheel movement
- Steering sensors
- Vehicle CAN data

The resulting vehicle state may contain information such as:

- X position
- Y position
- Heading
- Velocity
- Acceleration
- Steering angle

This information can then be used by the path planner and vehicle controller.

# Path Planning

Path planning determines where the vehicle should go.

A simplified process is:

Current Vehicle Position
        ↓
Destination / Road Information
        ↓
Lane Information + Obstacles
        ↓
Path-Planning Algorithm
        ↓
Desired Vehicle Trajectory

The desired trajectory can be represented as a sequence of positions:

(x1, y1)
(x2, y2)
(x3, y3)
(x4, y4)
...

The path planner determines the route the car should attempt to follow.

MiLa has researched multiple approaches to autonomous path planning, including reinforcement-learning-based methods, inverse reinforcement learning, model-based planning, and end-to-end autonomous-driving systems.

# Inverse Reinforcement Learning

One MiLa research area is **Inverse Reinforcement Learning**, or IRL.

Traditional reinforcement learning starts with a reward function.

For example:

Stay in lane        +10
Reach destination   +100
Collision           -1000
Hard braking        -10

An agent then learns behavior that attempts to maximize this reward.

The problem is that designing a good reward function for real driving is difficult.

Human driving behavior includes many complicated tradeoffs involving:

- Safety
- Comfort
- Speed
- Distance from obstacles
- Lane position
- Traffic laws
- Other drivers
- Road geometry

Inverse Reinforcement Learning reverses the normal reinforcement-learning process.

Instead of manually telling the AI what good driving looks like, the system studies demonstrations from an experienced driver.

Human Driver
     ↓
Driving Demonstrations
     ↓
Inverse Reinforcement Learning
     ↓
Infer What the Human Driver Values
     ↓
Learn a Reward Function
     ↓
Generate Autonomous Behavior

The goal is to allow an autonomous vehicle to learn driving behavior from examples rather than requiring engineers to manually define every driving rule and preference.

# Vehicle Control

Once the path planner decides where the vehicle should go, a controller must determine how to make the physical vehicle follow that trajectory.

For example:

Desired Trajectory
       ↓
Vehicle Controller
       ↓
Desired Steering
Desired Acceleration
Desired Braking

This is where control theory becomes important.

# Model Predictive Control

MiLa works with **Model Predictive Control**, or MPC.

MPC repeatedly predicts what the vehicle will do over a short period of time and chooses the control inputs that produce the best future behavior.

A simplified process is:

Current Vehicle State
        ↓
Predict Future Vehicle Motion
        ↓
Evaluate Possible Control Inputs
        ↓
Compare Predicted Trajectories
        ↓
Choose Best Steering / Throttle / Brake Commands
        ↓
Apply Commands
        ↓
Receive New Sensor Data
        ↓
Repeat

The controller may try to minimize things such as:

- Path-tracking error
- Steering error
- Steering aggressiveness
- Passenger discomfort
- Excessive acceleration
- Excessive braking
- Control effort

while respecting constraints such as:

- Maximum steering angle
- Maximum steering rate
- Maximum acceleration
- Maximum braking
- Vehicle dynamics

# Data-Driven Model Predictive Control

Traditional MPC normally requires a mathematical model of the vehicle.

Conceptually:

Vehicle Physics
      ↓
Mathematical Model
      ↓
MPC
      ↓
Vehicle Control

A simplified mathematical model might be written as:

x(k+1) = A x(k) + B u(k)

where:

- x represents the state of the vehicle
- u represents the control input
- A and B describe how the system behaves

The problem is that real vehicles are difficult to model perfectly.

Vehicle behavior changes because of:

- Tire characteristics
- Road surfaces
- Vehicle load
- Mechanical friction
- Steering delays
- Sensor delays
- Nonlinear behavior
- Temperature
- Vehicle speed

MiLa has investigated **data-driven control**, where measurements from the real system can be used more directly rather than relying entirely on a perfect mathematical model.

The basic idea is:

Send Different Inputs to the System
                ↓
Measure the Response
                ↓
Store Input / Output Data
                ↓
Build a Data Representation
                ↓
Optimization Algorithm
                ↓
Predict Future Behavior
                ↓
Choose Control Inputs

One MiLa project uses concepts involving **Hankel matrices** and **Willems' Fundamental Lemma**.

Rather than identifying a traditional mathematical model first, sufficiently rich measured input/output data can be used to represent the possible behavior of the system.

This approach is closely related to data-enabled predictive control.

A simplified example is:

Input Data:
u1, u2, u3, u4, u5...

Measured Output Data:
y1, y2, y3, y4, y5...

These values can be organized into structured matrices that represent how the system responds to different inputs.

The controller can then use this information inside an optimization problem to calculate future control actions.

# Persistently Exciting Inputs

A data-driven controller needs useful training data.

If the system only observes a car driving perfectly straight at a constant speed, it learns very little about how the vehicle responds to different steering commands.

Instead, the system needs sufficiently varied inputs.

This is called **persistent excitation**.

Conceptually:

Excitation Signal
      ↓
Real Vehicle / System
      ↓
Measured Response
      ↓
Stored Data
      ↓
Data-Driven Controller

The input signal needs to contain enough variation to capture important system dynamics.

# Drive-by-Wire

One of MiLa's important hardware research areas is **low-cost drive-by-wire**, or DBW.

Drive-by-wire allows a computer to control:

- Steering
- Accelerator
- Brakes

without requiring a human to physically operate those controls.

A high-level autonomous-driving computer might calculate:

Steering = 8° Left
Throttle = 15%
Brake = 0%

However, those numbers alone cannot physically move a car.

Something must translate the software commands into electrical or mechanical control of the vehicle.

That is the purpose of the drive-by-wire system.

# MiLa's Low-Cost Drive-by-Wire Architecture

MiLa has experimented with embedded hardware such as:

- ESP32 microcontrollers
- CAN interfaces
- Digital-to-analog converters
- Relay boards
- Automotive wiring
- Vehicle sensors
- Existing electric power-steering systems

A simplified steering architecture can look like this:

Autonomous Computer
        ↓
Desired Steering Command
        ↓
ESP32
        ↓
Control Algorithm
        ↓
DAC / Electrical Interface
        ↓
Vehicle Steering Electronics
        ↓
Electric Power Steering System
        ↓
Physical Steering Mechanism
        ↓
Front Wheels Turn

Vehicle feedback can travel in the opposite direction:

Vehicle Steering Sensor
        ↓
CAN Bus
        ↓
CAN Interface
        ↓
ESP32
        ↓
Controller
        ↓
Compare Desired vs Actual Steering

This creates a **closed-loop feedback-control system**.

The controller continuously compares:

Desired Steering Angle

with:

Actual Steering Angle

and adjusts the command until the error becomes small.

# ESP32

MiLa has used ESP32 microcontrollers in drive-by-wire systems.

The ESP32 can act as a bridge between the high-level autonomous-driving computer and the vehicle electronics.

For example:

ROS 2 Computer
      ↓
USB / CAN / Bluetooth
      ↓
ESP32
      ↓
DAC / Relay / CAN Interface
      ↓
Vehicle Electronics
      ↓
Physical Vehicle

The ESP32 can perform tasks such as:

- Receive steering commands
- Receive braking commands
- Receive acceleration commands
- Read CAN messages
- Control relays
- Produce analog signals
- Run PID or other feedback controllers
- Monitor vehicle state
- Handle safety logic
- Communicate with higher-level software

This means the ESP32 belongs to the embedded real-time control layer of the autonomous vehicle.

# Digital-to-Analog Converters

A microcontroller normally works with digital values.

However, some vehicle systems expect analog electrical signals.

For example, a vehicle sensor might normally output something like:

0.5 V
1.2 V
2.8 V
4.0 V

depending on the driver's input or vehicle state.

A **DAC**, or digital-to-analog converter, allows the microcontroller to generate controlled analog voltages.

Conceptually:

Digital Value From ESP32
        ↓
DAC
        ↓
Analog Voltage
        ↓
Vehicle Electronic System

This can allow an embedded controller to interface with existing vehicle electronics without installing a large mechanical actuator.

# Relays

Relays can allow the system to switch between human control and autonomous control.

In manual mode:

Human Control
      ↓
Factory Vehicle Wiring
      ↓
Vehicle

In autonomous mode:

Autonomous Computer
      ↓
ESP32
      ↓
Vehicle Interface
      ↓
Vehicle

The relay determines which signal path is connected.

This is useful because it allows the original human controls to remain available while also allowing autonomous control.

# CAN Bus

Modern cars contain many electronic control units, or ECUs.

These modules communicate over vehicle networks.

One of the most common is **CAN**, or Controller Area Network.

CAN allows modules such as the:

- Engine controller
- Electric power steering controller
- ABS controller
- Battery controller
- Instrument cluster
- Body-control module
- Transmission controller

to communicate.

CAN messages may contain information such as:

- Vehicle speed
- Steering angle
- Wheel speed
- Accelerator position
- Brake status
- Motor status
- Battery information
- Steering torque

MiLa uses CAN data for vehicle feedback, sensing, and control.

A simplified CAN architecture is:

Vehicle Sensor / ECU
        ↓
CAN Bus
        ↓
CAN Interface
        ↓
ESP32 or Onboard Computer
        ↓
Autonomous Software

# CAN Bypass Concept

One challenge with autonomous vehicle retrofits is that every manufacturer may use different CAN messages and proprietary control schemes.

Instead of relying entirely on sending proprietary CAN control messages to command steering, MiLa has explored methods that interface with existing electrical signals and vehicle hardware more directly.

The idea is that the vehicle's own electronic systems, such as electric power steering, can still provide the physical force needed to steer the car.

The autonomous controller instead produces signals that cause the existing vehicle system to respond appropriately.

CAN can still be used for feedback and vehicle-state information.

# ROS 2

ROS 2 is a robotics software framework commonly used to connect sensors, algorithms, controllers, and hardware interfaces.

Instead of writing the entire autonomous-driving system as one huge program, different parts of the system can run as separate nodes.

For example:

Camera Node
     ↓
Perception Node
     ↓
Localization Node
     ↓
Path Planner
     ↓
Vehicle Controller
     ↓
Drive-by-Wire Node
     ↓
Vehicle

ROS 2 is useful for:

- Sensor communication
- Robotics algorithms
- Message passing
- Visualization
- Data logging
- Hardware interfaces
- Distributed computing
- Real-time robotics systems

# Old-Vehicle vs New-Vehicle Autonomous Conversion

MiLa has explored multiple ways to convert vehicles to autonomous operation.

Older vehicles may require external actuators.

For example:

Servo Motor
     ↓
Mechanical Steering

or:

Linear Actuator
     ↓
Physical Accelerator / Brake Pedal

This approach physically moves the same mechanisms a human driver would normally move.

Newer vehicles already have systems such as:

- Electric power steering
- Electronic throttle
- Electronic braking
- Electronic sensors
- CAN-connected controllers

This makes it possible to interface electronically with the vehicle rather than installing large external motors and actuators.

Conceptually:

Older Vehicle:

Computer
   ↓
Motor Driver
   ↓
Servo / Linear Actuator
   ↓
Physical Vehicle Control

Newer Vehicle:

Computer
   ↓
Microcontroller
   ↓
Electronic Interface
   ↓
Existing Vehicle Electronics
   ↓
Existing Vehicle Actuator

This can significantly reduce the amount of hardware required.

# Real Vehicle Testing

A major characteristic of MiLa is that the lab performs research using actual production vehicles.

The system may contain:

Cameras
LiDAR
Radar
GPS
IMU
        ↓
Onboard Computer / GPU
        ↓
Autonomous-Driving Software
        ↓
Path Planner
        ↓
Controller
        ↓
Embedded Microcontroller
        ↓
Drive-by-Wire
        ↓
Production Vehicle

This means the lab has to solve practical engineering problems that do not always appear in simulation.

Examples include:

- Electrical noise
- Sensor synchronization
- CAN communication
- Wiring
- Mechanical limitations
- Communication delays
- Controller timing
- Safety systems
- Power distribution
- Real-time software
- Vehicle dynamics
- Sensor failures

# Why Low-Cost Autonomous Vehicles Matter

Autonomous-driving research can be extremely expensive.

A research platform may require:

- Vehicle purchase
- Drive-by-wire conversion
- LiDAR
- Radar
- Cameras
- High-performance computers
- GPUs
- GPS / GNSS
- IMUs
- Safety systems
- Data acquisition systems

If the drive-by-wire system alone is extremely expensive, autonomous research becomes difficult for smaller universities, researchers, startups, or transportation organizations.

MiLa is investigating ways to reduce this cost by using existing production vehicles and lower-cost embedded hardware.

Potential applications include:

- Autonomous public transportation
- Rural transportation
- Autonomous shuttles
- Freight transportation
- Tribal transportation systems
- Autonomous electric vehicles
- Driver-assistance systems
- University research vehicles
- Robotics research

# MiLa's Overall Engineering Philosophy

A useful way to understand MiLa is as the intersection of three major fields:

             Artificial Intelligence
                    /\
                   /  \
                  /    \
                 /      \
                /        \
        Robotics -------- Embedded Systems

Artificial intelligence determines:

> What should the vehicle do?

Control systems determine:

> How should the vehicle accomplish it?

Embedded hardware determines:

> How do those commands physically reach the vehicle?

The complete process is:

UNDERSTAND THE ENVIRONMENT
          ↓
DECIDE WHERE TO GO
          ↓
CALCULATE HOW TO GET THERE
          ↓
GENERATE VEHICLE COMMANDS
          ↓
SEND ELECTRICAL COMMANDS
          ↓
MOVE THE PHYSICAL VEHICLE
          ↓
MEASURE WHAT HAPPENED
          ↓
CORRECT THE ERROR
          ↓
REPEAT

# Three Important MiLa Research Areas

## 1. Low-Cost Drive-by-Wire

Main problem:

> How can a normal production vehicle physically obey commands from an autonomous computer without requiring an extremely expensive commercial drive-by-wire system?

Relevant technologies include:

- ESP32
- C / C++
- CAN
- DACs
- Relays
- Automotive electronics
- Embedded systems
- Steering
- Braking
- Acceleration
- Feedback control
- ROS 2

This is one of the most hardware-focused MiLa research areas.

## 2. Data-Driven Model Predictive Control

Main problem:

> How can an autonomous system control a vehicle using measured system behavior without depending entirely on a perfectly accurate mathematical model?

Relevant topics include:

- Linear algebra
- Optimization
- Control theory
- Vehicle dynamics
- Data collection
- Hankel matrices
- Willems' Fundamental Lemma
- Data-driven control
- Real-time computing

This research attempts to use real input/output behavior from the system directly in the control process.

## 3. Inverse Reinforcement Learning Path Planning

Main problem:

> How can an autonomous vehicle learn good driving behavior from human demonstrations instead of requiring engineers to manually specify every driving rule and preference?

Relevant topics include:

- AI
- Machine learning
- Reinforcement learning
- Inverse reinforcement learning
- Path planning
- Driver demonstrations
- Reward functions
- Autonomous decision making

# How the MiLa Projects Connect

These projects represent different layers of one autonomous vehicle.

Inverse Reinforcement Learning / Path Planning
        ↓
"Where should the vehicle go?"

Data-Driven MPC / Vehicle Controller
        ↓
"What steering, throttle, and braking commands will make the vehicle follow that path?"

Drive-by-Wire
        ↓
"How do those commands physically control the real vehicle?"

Physical Vehicle
        ↓
Sensors + CAN Feedback
        ↓
Controller
        ↓
Repeat

Therefore, the projects are not isolated.

Together they represent major parts of a complete autonomous-driving architecture.

# Why MiLa Is Especially Relevant to Computer Engineering

MiLa is highly relevant to computer engineering because much of its work occurs directly at the hardware/software boundary.

A computer engineering student working in MiLa could potentially encounter:

## Embedded Systems

- ESP32
- Microcontrollers
- Firmware
- Timers
- Interrupts
- GPIO
- ADCs
- DACs
- Communication protocols
- Real-time systems

## Electronics

- PCBs
- Relays
- Sensors
- Signal conditioning
- Automotive wiring
- Power electronics
- Voltage levels
- Electrical interfaces

## Automotive Networking

- CAN bus
- Vehicle ECUs
- Message decoding
- CAN interfaces
- Automotive communication

## Programming

- C
- C++
- Python
- Embedded firmware
- Linux
- ROS 2

## Robotics

- Sensors
- Actuators
- Feedback control
- Localization
- Path planning
- Perception

## Artificial Intelligence

- Computer vision
- Neural networks
- Reinforcement learning
- Inverse reinforcement learning
- End-to-end autonomous driving

## Control Systems

- PID control
- Model Predictive Control
- Data-driven control
- Feedback systems
- State estimation
- Optimization

## Computer Hardware

- GPUs
- Embedded computers
- Microcontrollers
- Sensor interfaces
- Communication interfaces

MiLa is therefore a strong example of **hardware/software co-design**.

A computer engineer working in this environment may:

- Write C/C++ firmware
- Program an ESP32
- Analyze CAN packets
- Connect sensors
- Debug electrical signals
- Design or modify a PCB
- Work with relays
- Test vehicle electronics
- Write Python scripts
- Use Linux
- Work with ROS 2
- Implement a controller
- Analyze autonomous-driving data
- Connect AI algorithms to real hardware

# Main Engineering Pipeline

The MiLa research environment can be summarized as:

Sensors
    ↓
Perception
    ↓
Localization
    ↓
Path Planning / AI
    ↓
Control Algorithm
    ↓
ROS 2 / Software Interface
    ↓
Embedded Controller
    ↓
CAN / DAC / Relays / Electronics
    ↓
Drive-by-Wire
    ↓
Steering / Brake / Accelerator
    ↓
Physical Vehicle
    ↓
Sensor + CAN Feedback
    ↓
Repeat

# Short Summary

MiLa is the **Mobility Intelligence Lab at the University of Oklahoma**, a research group focused on autonomous vehicles, intelligent transportation, embedded systems, vehicle control, robotics, and artificial intelligence.

The lab works across the complete autonomous-driving stack, from cameras, sensors, perception, path planning, and AI to Model Predictive Control, ESP32 microcontrollers, CAN communication, drive-by-wire electronics, and real vehicle testing.

MiLa is not only developing software simulations. It modifies real production vehicles, integrates embedded electronics and sensors, develops autonomous-driving algorithms, and tests those systems on physical vehicles.

Its broader goal is to make autonomous transportation more affordable, practical, adaptable, and accessible by developing lower-cost hardware and software systems that can be integrated into existing production vehicles.

The most important way to understand MiLa is:

> The AI decides where the car should go, the controller determines how to make the car follow that path, and the embedded drive-by-wire hardware physically makes the vehicle obey those commands.

For a computer engineering student, MiLa is especially relevant because it combines embedded systems, electronics, CAN bus, sensors, microcontrollers, C/C++, Python, Linux, ROS 2, robotics, control systems, real-time computing, AI, and hardware/software integration in one research environment.
