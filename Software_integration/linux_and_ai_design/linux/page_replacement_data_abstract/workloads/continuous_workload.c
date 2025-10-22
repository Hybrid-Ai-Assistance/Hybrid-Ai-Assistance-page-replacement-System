#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <signal.h>

#define SIZE (100 * 1024 * 1024) // 100MB
volatile sig_atomic_t keep_running = 1;

void handle_signal(int sig) {
    keep_running = 0;
}

void continuous_access() {
    printf("Starting CONTINUOUS memory access pattern...\n");
    printf("This will run for 5 minutes or until stopped with Ctrl+C\n");
    
    char *memory1 = malloc(SIZE);
    char *memory2 = malloc(SIZE);
    
    if (!memory1 || !memory2) {
        printf("Failed to allocate memory!\n");
        return;
    }
    
    printf("Allocated 200MB total for continuous access\n");
    
    int iteration = 0;
    while (keep_running && iteration < 300) { // 5 minutes max
        printf("Continuous workload iteration %d...\n", iteration + 1);
        
        // Pattern 1: Sequential through first block
        for (int i = 0; i < SIZE && keep_running; i += 4096) {
            memory1[i] = (i / 4096 + iteration) % 256;
        }
        
        // Pattern 2: Random through second block  
        for (int i = 0; i < 10000 && keep_running; i++) {
            int block = rand() % (SIZE / 4096);
            memory2[block * 4096] = rand() % 256;
        }
        
        iteration++;
        sleep(1); // Run for about 5 minutes total
    }
    
    printf("Continuous access completed after %d iterations.\n", iteration);
    free(memory1);
    free(memory2);
}

int main() {
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);
    
    printf("=== CONTINUOUS Memory Access Workload ===\n");
    printf("Process PID: %d\n", getpid());
    continuous_access();
    return 0;
}
