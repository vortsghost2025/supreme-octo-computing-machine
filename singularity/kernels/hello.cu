#include <stdio.h>

__global__ void hello() {
    printf("Hello from GPU kernel\n");
}

int main() {
    hello<<<1,1>>>();
    cudaDeviceSynchronize();
    return 0;
}
