code="""
# ==============================================================================
# Sequência de Fibonacci via LEDs MMIO
# ==============================================================================

.global _start

_start:
    lui s0, 0x20000      # s0 = 0x20000000 (Endereço base do GPIO / LEDs)
    li s1, 46            # s1 = 46 (Limite de iterações do Fibonacci)
    lui s2, 0x00400      # s2 = Aprox. 4 milhões (Limite do Busy Wait Loop)

main_loop:
    li t0, 0             # Termo atual
    li t1, 1             # Próximo termo
    li t2, 1             # Contador da iteração

fib_loop:
    sw t0, 0(s0)         # MMIO: Acende os LEDs com o valor de Fibonacci

    add t4, t0, t1       # Calcula próximo
    mv t0, t1            # Atualiza termo atual
    mv t1, t4            # Atualiza próximo termo

    addi t2, t2, 1       # ++iteração
    bne t2, s1, fib_loop # Volta se não chegou no limite (46)

    j main_loop          # Reinicia a sequência
"""