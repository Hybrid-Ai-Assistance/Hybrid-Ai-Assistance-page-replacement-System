#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define SIZE (150 * 1024 * 1024) // 150MB
#define ACCESSES 500000

void random_access() {
    printf("Starting random access pattern...\n");
    char *memory = malloc(SIZE);
    if (!memory) {
        printf("Failed to allocate memory!\n");
        return;
    }
    
    printf("Allocated 150MB for random access\n");
    srand(time(NULL));
    
    // Random access pattern
    for (int i = 0; i < ACCESSES; i++) {
        int block = rand() % (SIZE / 4096);
        memory[block * 4096] = rand() % 256;
        
        if (i % 100000 == 0) {
            printf("Completed %d/%d random accesses...\n", i, ACCESSES);
        }
    }
    
    printf("Random access completed.\n");
    free(memory);
}

int main() {
    printf("=== Random Memory Access Workload ===\n");
    printf("Process PID: %d\n", getpid());
    random_access();
    return 0;
}
