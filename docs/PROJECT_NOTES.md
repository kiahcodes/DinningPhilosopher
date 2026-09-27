# Project Notes / Viva Guide

## Core idea

The Dining Philosophers Problem models five concurrent processes competing for five shared resources.

Each philosopher needs two adjacent forks to eat.

## Why this belongs in Microprocessors & Interfacing

The project demonstrates:

- processor registers
- instruction pointer
- flags
- memory-mapped state
- sequential instruction execution
- shared resources
- synchronization
- deadlock
- deadlock prevention
- a visual interface driven by processor state

## Brain vs interface

The assembly file is the authoritative state machine.

Python performs:

1. Assembly parsing.
2. Execution of the supported instruction subset.
3. Reading the resulting CPU/memory state.
4. Rendering the state.

Python does not contain the philosopher decision algorithm.

## Deadlock scenario

The deadlock demonstration creates:

- P1 owns F1 and waits for F2
- P2 owns F2 and waits for F3
- P3 owns F3 and waits for F4
- P4 owns F4 and waits for F5
- P5 waits for F1

This forms a circular wait.

## Prevention scenario

Safe mode uses an asymmetric ordering strategy. The assembly schedules non-conflicting philosophers and releases forks before the next conflicting pair is allowed to eat.

## Suggested demonstration sequence

1. Start the application.
2. Show the Virtual 8086 register panel.
3. Click `Demonstrate Deadlock`.
4. Explain the five occupied/waiting relationships.
5. Show `DEADLOCK = YES` in shared memory.
6. Click `Reset`.
7. Click `Deadlock Prevention`.
8. Show philosophers eating and forks being released.
9. Click `Step CPU`.
10. Explain that every visual change is caused by assembly instructions updating shared memory.

## Important limitation

This is an educational 8086 subset emulator, not a complete Intel 8086 emulator. The assembly source is deliberately restricted to a small set of instructions needed for the assignment.

For a physical-hardware extension, the same state map can later be connected to an actual 8086 trainer board or serial interface.
