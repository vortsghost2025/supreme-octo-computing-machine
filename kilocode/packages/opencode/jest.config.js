export default {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/test'],
  moduleFileExtensions: ['ts', 'js'],
  transform: {
    '^.+\.ts$': 'ts-jest',
  },
};
