'use strict';

const { ToolExecutor } = require('./tool-executor');
const { MCPClient }    = require('./mcp-client');

/**
 * Enhanced tool executor — combines the 18 basic tools with all available
 * MCP server tools.  MCP servers that fail to connect are skipped gracefully.
 */
class EnhancedToolExecutor {
  /**
   * @param {object} opts
   * @param {string}  opts.workingDir
   * @param {boolean} opts.noApproval
   */
  constructor({ workingDir = process.cwd(), noApproval = false } = {}) {
    this._basic = new ToolExecutor({ workingDir, noApproval });
    this._mcp   = new MCPClient();
  }

  /** Connect MCP servers.  Call once after construction. */
  async init() {
    await this._mcp.init();
  }

  /** Return the names of all available tools (basic + MCP). */
  listTools() {
    return [
      ...this._basic.listBasicTools(),
      ...this._mcp.listTools(),
    ];
  }

  /**
   * Execute a tool by name.
   *
   * @param {string} name   - Tool name, e.g. "read_file" or "github:create_issue"
   * @param {object} args   - Tool arguments
   */
  async execute(name, args = {}) {
    // MCP tools are prefixed "server:tool"
    if (name.includes(':')) {
      const [server, tool] = name.split(':', 2);
      return this._mcp.callTool(server, tool, args);
    }

    // Basic tools
    switch (name) {
      case 'read_file':          return this._basic.readFile(args.path);
      case 'write_to_file':      return this._basic.writeToFile(args.path, args.content);
      case 'replace_in_file':    return this._basic.replaceInFile(args.path, args.old_str, args.new_str);
      case 'append_to_file':     return this._basic.appendToFile(args.path, args.content);
      case 'delete_file':        return this._basic.deleteFile(args.path);
      case 'list_files':         return this._basic.listFiles(args.path);
      case 'file_exists':        return this._basic.fileExists(args.path);
      case 'get_file_info':      return this._basic.getFileInfo(args.path);
      case 'execute_command':    return this._basic.executeCommand(args.command, args.cwd);
      case 'grep_files':         return this._basic.grepFiles(args.pattern, args.path, args.options);
      case 'git_status':         return this._basic.gitStatus();
      case 'git_diff':           return this._basic.gitDiff();
      case 'git_log':            return this._basic.gitLog(args.limit);
      case 'git_commit':         return this._basic.gitCommit(args.message);
      default:
        throw new Error(`Unknown tool: "${name}"`);
    }
  }
}

module.exports = { EnhancedToolExecutor };
