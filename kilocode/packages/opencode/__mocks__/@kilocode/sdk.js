module.exports = {
  createKilo: async () => ({
    client: {},
    server: { url: 'http://localhost', close: () => {} },
  }),
  createKiloClient: () => ({}),
};
