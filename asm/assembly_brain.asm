;; ============================================================
;; DINING PHILOSOPHERS — 8086 ASSEMBLY BRAIN
;; ============================================================
;; Educational 8086-compatible source.
;;
;; State encoding:
;;   00h = THINKING
;;   01h = HUNGRY
;;   02h = EATING
;;   03h = WAITING
;;
;; Fork encoding:
;;   00h = FREE
;;   01h = LOCKED
;;
;; Mode:
;;   00h = DEADLOCK-PRONE (every philosopher acquires left fork, then waits for right)
;;   01h = DEADLOCK PREVENTION (fair alternating round-robin scheduling)
;;
;; Shared table fork mapping:
;;   P1 sits between F1 (left) and F2 (right)
;;   P2 sits between F2 (left) and F3 (right)
;;   P3 sits between F3 (left) and F4 (right)
;;   P4 sits between F4 (left) and F5 (right)
;;   P5 sits between F5 (left) and F1 (right)
;; ============================================================

.MODEL SMALL
.STACK 100H

.DATA

PHIL1 DB 00H
PHIL2 DB 00H
PHIL3 DB 00H
PHIL4 DB 00H
PHIL5 DB 00H

FORK1 DB 00H
FORK2 DB 00H
FORK3 DB 00H
FORK4 DB 00H
FORK5 DB 00H

CURRENT DB 00H
MODE DB 00H
TICK DB 00H
DEADLOCK DB 00H

.CODE

START:
    MOV AX, 0000H
    MOV BX, 0000H
    MOV CX, 0000H
    MOV DX, 0000H

MAIN:
    INC TICK
    CMP MODE, 00H
    JE  DEADLOCK_MODE
    JMP SAFE_MODE

; ------------------------------------------------------------
; DEADLOCK-PRONE MODE
; Every philosopher acquires their left fork and is blocked
; waiting for their right fork, creating an unresolvable circular wait.
; ------------------------------------------------------------
DEADLOCK_MODE:
    ; P1 takes F1 (left), waits for F2 (right)
    MOV CURRENT, 00H
    MOV FORK1, 01H
    MOV PHIL1, 03H

    ; P2 takes F2 (left), waits for F3 (right)
    MOV CURRENT, 01H
    MOV FORK2, 01H
    MOV PHIL2, 03H

    ; P3 takes F3 (left), waits for F4 (right)
    MOV CURRENT, 02H
    MOV FORK3, 01H
    MOV PHIL3, 03H

    ; P4 takes F4 (left), waits for F5 (right)
    MOV CURRENT, 03H
    MOV FORK4, 01H
    MOV PHIL4, 03H

    ; P5 takes F5 (left), waits for F1 (right)
    MOV CURRENT, 04H
    MOV FORK5, 01H
    MOV PHIL5, 03H

    ; Circular wait condition complete
    MOV DEADLOCK, 01H

DEADLOCK_STALL:
    INC TICK
    CMP MODE, 00H
    JNE RESET_BEFORE_SAFE
    NOP
    JMP DEADLOCK_STALL

RESET_BEFORE_SAFE:
    MOV FORK1, 00H
    MOV FORK2, 00H
    MOV FORK3, 00H
    MOV FORK4, 00H
    MOV FORK5, 00H
    MOV PHIL1, 00H
    MOV PHIL2, 00H
    MOV PHIL3, 00H
    MOV PHIL4, 00H
    MOV PHIL5, 00H
    MOV DEADLOCK, 00H
    JMP SAFE_MODE

; ------------------------------------------------------------
; SAFE MODE (DEADLOCK PREVENTION)
; Fair round-robin scheduling of non-adjacent philosophers.
; Round 1: P1 and P3 eat concurrently (F1+F2, F3+F4).
; Round 2: P2 and P4 eat concurrently (F2+F3, F4+F5).
; Round 3: P5 eats (F5+F1).
; Prevents circular wait; no philosopher starves.
; ------------------------------------------------------------
SAFE_MODE:
    MOV DEADLOCK, 00H

    ;; ── ROUND 1: P1 and P3 Eat ───────────────────────────────
    ; F1, F2, F3, F4 are free. P1 and P3 acquire forks and transition to EATING (02h)
    MOV CURRENT, 00H
    MOV FORK1, 01H
    MOV FORK2, 01H
    MOV PHIL1, 02H

    MOV CURRENT, 02H
    MOV FORK3, 01H
    MOV FORK4, 01H
    MOV PHIL3, 02H

    ; Neighbors wanting adjacent forks enter WAITING (03h)
    MOV PHIL2, 03H
    MOV PHIL4, 03H
    MOV PHIL5, 00H

    NOP
    NOP
    NOP

    ; P1 and P3 finish eating and release their forks (02h -> 00h)
    ; P2 and P4 remain WAITING (03h) until their forks are acquired
    MOV PHIL1, 00H
    MOV PHIL3, 00H
    MOV FORK1, 00H
    MOV FORK2, 00H
    MOV FORK3, 00H
    MOV FORK4, 00H

    ;; ── ROUND 2: Waiting P2 and P4 Eat ───────────────────────
    ; Forks F2, F3, F4, F5 are now free!
    ; P2 and P4 transition DIRECTLY from WAITING (03h) -> EATING (02h)!
    MOV CURRENT, 01H
    MOV FORK2, 01H
    MOV FORK3, 01H
    MOV PHIL2, 02H

    MOV CURRENT, 03H
    MOV FORK4, 01H
    MOV FORK5, 01H
    MOV PHIL4, 02H

    ; Neighbors wanting forks enter WAITING (03h)
    MOV PHIL1, 00H
    MOV PHIL3, 03H
    MOV PHIL5, 03H

    NOP
    NOP
    NOP

    ; P2 and P4 finish eating and release their forks (02h -> 00h)
    ; P3 and P5 remain WAITING (03h)
    MOV PHIL2, 00H
    MOV PHIL4, 00H
    MOV FORK2, 00H
    MOV FORK3, 00H
    MOV FORK4, 00H
    MOV FORK5, 00H

    ;; ── ROUND 3: Waiting P5 Eats ─────────────────────────────
    ; Forks F5 and F1 are now free!
    ; P5 transitions DIRECTLY from WAITING (03h) -> EATING (02h)!
    MOV CURRENT, 04H
    MOV FORK5, 01H
    MOV FORK1, 01H
    MOV PHIL5, 02H

    ; P1 and P3 enter WAITING (03h) in preparation for Round 1
    MOV PHIL1, 03H
    MOV PHIL3, 03H
    MOV PHIL2, 00H
    MOV PHIL4, 00H

    NOP
    NOP
    NOP

    ; P5 finishes eating and releases forks (02h -> 00h)
    ; P1 and P3 remain in WAITING (03h) and will eat in Round 1
    MOV PHIL5, 00H
    MOV FORK5, 00H
    MOV FORK1, 00H

    NOP
    JMP MAIN

END START
