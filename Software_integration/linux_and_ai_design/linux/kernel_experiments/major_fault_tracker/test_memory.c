// test_memory.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SIZE 100*1024*1024 // 100MB

int main() {
    printf("🚀 Starting memory intensive test...\n");
    
    char *buffer = malloc(SIZE);
    if (!buffer) {
        printf("Memory allocation failed\n");
        return 1;
    }
    
    // Access memory to trigger page faults
    for (int i = 0; i < SIZE; i += 4096) {
        buffer[i] = 'A';  // Trigger page faults
    }
    
    printf("✅ First access done. Now forcing swap...\n");
    
    // Allocate more memory to force swapping
    char *buffer2 = malloc(SIZE);
    if (buffer2) {
        for (int i = 0; i < SIZE; i += 4096) {
            buffer2[i] = 'B';
        }
    }
    
    free(buffer);
    free(buffer2);
    printf("✅ Test completed.\n");
    return 0;
}