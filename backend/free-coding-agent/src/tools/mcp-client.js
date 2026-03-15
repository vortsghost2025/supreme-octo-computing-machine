'use strict';

/**
 * MCP client wrapper.
 *
 * Connects to Cline MCP servers (GitHub, filesystem, brave-search, postgres,
 * context7) and exposes a unified tool-call interface.
 *
 * Each server is optional — if a required env var is missing or the server
 * fails to connect, that server is skipped and the agent continues with
 * whatever servers ARE available.  This prevents a missing GitHub token from
 * crashing the whole container.
 */
class MCPClient {
  constructor() {
    this._servers = {};  // name → { client, tools[] }
    this._ready   = false;
  }

  /**
   * Attempt to connect to all configured MCP servers.
   * Failures are logged and skipped — never thrown.
   */
  async init() {
    await Promise.all([
      this._tryConnect('github',     this._githubConfig()),
      this._tryConnect('filesystem', this._filesystemConfig()),
      this._tryConnect('brave',      this._braveConfig()),
      this._tryConnect('postgres',   this._postgresConfig()),
    ]);
    this._ready = true;
    const connected = Object.keys(this._servers).join(', ') || 'none';
    console.log(`[mcp-client] connected servers: ${connected}`);
  }

  /** Return flat list of available MCP tool names. */
  listTools() {
    const names = [];
    for (const [server, data] of Object.entries(this._servers)) {
      for (const tool of data.tools) {
        names.push(`${server}:${tool}`);
      }
    }
    return names;
  }

  /**
   * Call an MCP tool.
   * @param {string} serverName
   * @param {string} toolName
   * @param {object} args
   */
  async callTool(serverName, toolName, args = {}) {
    const srv = this._servers[serverName];
    if (!srv) throw new Error(`MCP server "${serverName}" not connected`);
    return srv.client.callTool({ name: toolName, arguments: args });
  }

  // ── Config builders ─────────────────────────────────────────────────────────

  _githubConfig() {
    if (!process.env.GITHUB_TOKEN) return null;
    return {
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-github'],
      env: { GITHUB_PERSONAL_ACCESS_TOKEN: process.env.GITHUB_TOKEN },
      tools: ['create_issue', 'search_repositories', 'get_file_contents', 'create_pull_request'],
    };
  }

  _filesystemConfig() {
    const dir = process.env.WORKING_DIR || process.cwd();
    return {
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-filesystem', dir],
      env: {},
      tools: ['read_file', 'write_file', 'list_directory', 'get_file_info'],
    };
  }

  _braveConfig() {
    if (!process.env.BRAVE_API_KEY) return null;
    return {
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-brave-search'],
      env: { BRAVE_API_KEY: process.env.BRAVE_API_KEY },
      tools: ['brave_web_search', 'brave_local_search'],
    };
  }

  _postgresConfig() {
    if (!process.env.DATABASE_URL) return null;
    return {
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-postgres', process.env.DATABASE_URL],
      env: {},
      tools: ['query', 'execute'],
    };
  }

  // ── Internal helpers ────────────────────────────────────────────────────────

  async _tryConnect(name, config) {
    if (!config) {
      console.log(`[mcp-client] skipping "${name}" (not configured)`);
      return;
    }
    try {
      // Lazy-import the MCP SDK to keep startup fast when the package
      // is not installed (e.g. in dev without npm install).
      const { Client }             = require('@modelcontextprotocol/sdk/client/index.js');
      const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');

      const transport = new StdioClientTransport({
        command: config.command,
        args:    config.args,
        env:     { ...process.env, ...config.env },
      });
      const client = new Client({ name: `snac-${name}`, version: '1.0' }, { capabilities: {} });
      await client.connect(transport);

      this._servers[name] = { client, tools: config.tools };
      console.log(`[mcp-client] "${name}" connected`);
    } catch (err) {
      console.warn(`[mcp-client] "${name}" failed to connect: ${err.message} — continuing without it`);
    }
  }
}

module.exports = { MCPClient };
