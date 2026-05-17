// Memory Map Definitions
#define LEDS_BASE     0x20000000 // 16-bit (R/W)
#define SWITCHES_BASE 0x20000004 // 16-bit (RO)

void main() {
    volatile int* led_ptr = (int*)LEDS_BASE;
    volatile int* sw_ptr = (int*)SWITCHES_BASE;
    
    while(1) {
        // Lê os switches
        int sw_val = *sw_ptr;
        
        int high_byte = (sw_val & 0xFF00) >> 8;
        int low_byte = sw_val & 0x00FF;
        
        // Escreve nos LEDs
        *led_ptr = high_byte + low_byte;
    }
}