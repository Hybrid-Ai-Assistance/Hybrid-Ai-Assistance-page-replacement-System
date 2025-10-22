#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define SIZE (200 * 1024 * 1024) // 200MB
#define PATTERNS 10

void sequential_access() {
    printf("Starting LONG sequential access pattern...\n");
    char *memory = malloc(SIZE);
    if (!memory) {
        printf("Failed to allocate memory!\n");
        return;
    }
    
    printf("Allocated 200MB for sequential access\n");
    printf("This will run for about 30 seconds...\n");
    
    for (int pattern = 0; pattern < PATTERNS; pattern++) {
        printf("Running sequential pattern %d/%d...\n", pattern + 1, PATTERNS);
        for (int i = 0; i < SIZE; i += 4096) {
            memory[i] = (i / 4096 + pattern) % 256;
        }
        sleep(3); // Sleep between patterns to make it run longer
    }
    
    printf("Sequential access completed.\n");
    free(memory);
}

int main() {
    printf("=== LONG Sequential Memory Access Workload ===\n");
    printf("Process PID: %d\n", getpid());
    sequential_access();
    return 0;
}
