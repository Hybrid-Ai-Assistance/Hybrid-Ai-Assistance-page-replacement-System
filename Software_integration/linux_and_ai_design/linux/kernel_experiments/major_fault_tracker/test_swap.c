#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define SIZE 100*1024*1024 // 100MB

int main() {
    printf("🚀 Starting swap test... PID: %d\n", getpid());
    
    // Allocate large memory
    char *buffer1 = malloc(SIZE);
    if (!buffer1) {
        printf("Memory allocation failed\n");
        return 1;
    }
    
    printf("✅ Buffer1 allocated. Accessing to page in...\n");
    
    // Access to page in memory
    for (int i = 0; i < SIZE; i += 4096) {
        buffer1[i] = 'A';
    }
    
    printf("✅ Buffer1 paged in. Now allocating buffer2 to force swap...\n");
    
    // Allocate second buffer to force swapping
    char *buffer2 = malloc(SIZE);
    if (buffer2) {
        for (int i = 0; i < SIZE; i += 4096) {
            buffer2[i] = 'B';
        }
        printf("✅ Buffer2 allocated and accessed.\n");
    }
    
    printf("✅ Now accessing buffer1 again to trigger swap-in...\n");
    
    // Access buffer1 again - this will trigger swap-in
    for (int i = 0; i < SIZE; i += 4096) {
        buffer1[i] = 'C';  // ✅ This will cause major faults
    }
    
    free(buffer1);
    if (buffer2) free(buffer2);
    
    printf("✅ Test completed.\n");
    return 0;
}
