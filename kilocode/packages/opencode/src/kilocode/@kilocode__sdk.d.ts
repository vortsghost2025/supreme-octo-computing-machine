declare module '@kilocode/sdk' {
  /** Minimal stub for the Kilo SDK used in tests */
  export function createKilo(): Promise<{
    client: any;
    server: { url: string; close(): void };
  }>;
  export function createKiloClient(): any;
}
