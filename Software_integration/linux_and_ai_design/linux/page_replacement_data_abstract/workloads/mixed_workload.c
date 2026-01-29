#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define CHUNK_SIZE (50 * 1024 * 1024) // 50MB chunks
#define NUM_CHUNKS 4

void mixed_workload() {
    printf("Starting mixed access pattern...\n");
    
    // Allocate multiple chunks
    char *chunks[NUM_CHUNKS];
    for (int i = 0; i < NUM_CHUNKS; i++) {
        chunks[i] = malloc(CHUNK_SIZE);
        if (!chunks[i]) {
            printf("Failed to allocate chunk %d\n", i);
            return;
        }
        printf("Allocated chunk %d (%dMB)\n", i, CHUNK_SIZE / (1024 * 1024));
    }
    
    srand(time(NULL));
    
    // Mixed access pattern
    for (int round = 0; round < 3; round++) {
        printf("Mixed pattern round %d...\n", round + 1);
        
        // Sequential access within chunks
        for (int chunk = 0; chunk < NUM_CHUNKS; chunk++) {
            for (int i = 0; i < CHUNK_SIZE; i += 8192) { // 8KB steps
                chunks[chunk][i] = (i + chunk + round) % 256;
            }
        }
        
        // Random cross-chunk access
        for (int i = 0; i < 100000; i++) {
            int chunk = rand() % NUM_CHUNKS;
            int block = rand() % (CHUNK_SIZE / 4096);
            chunks[chunk][block * 4096] = rand() % 256;
        }
    }
    
    // Cleanup
    for (int i = 0; i < NUM_CHUNKS; i++) {
        free(chunks[i]);
    }
    
    printf("Mixed workload completed.\n");
}

int main() {
    printf("=== Mixed Memory Access Workload ===\n");
    printf("Process PID: %d\n", getpid());
    mixed_workload();
    return 0;
}
