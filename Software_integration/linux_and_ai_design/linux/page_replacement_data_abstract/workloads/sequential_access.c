#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define SIZE (200 * 1024 * 1024) // 200MB
#define PATTERNS 3

void sequential_access() {
    printf("Starting sequential access pattern...\n");
    char *memory = malloc(SIZE);
    if (!memory) {
        printf("Failed to allocate memory!\n");
        return;
    }
    
    printf("Allocated 200MB for sequential access\n");
    
    // Pattern 1: Sequential forward
    for (int pattern = 0; pattern < PATTERNS; pattern++) {
        printf("Running sequential pattern %d...\n", pattern + 1);
        for (int i = 0; i < SIZE; i += 4096) {
            memory[i] = (i / 4096 + pattern) % 256;
        }
    }
    
    printf("Sequential access completed.\n");
    free(memory);
}

int main() {
    printf("=== Sequential Memory Access Workload ===\n");
    printf("Process PID: %d\n", getpid());
    sequential_access();
    return 0;
}
