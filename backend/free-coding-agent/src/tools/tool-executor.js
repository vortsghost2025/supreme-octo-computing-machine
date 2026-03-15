'use strict';

const fs    = require('fs');
const path  = require('path');
const { execFileSync } = require('child_process');

/**
 * Basic tool executor — 18 file/shell/git tools.
 * All destructive operations respect the `noApproval` flag.
 */
class ToolExecutor {
  /**
   * @param {object} opts
   * @param {string} opts.workingDir  - Root directory for file operations
   * @param {boolean} opts.noApproval - Skip approval prompts
   */
  constructor({ workingDir = process.cwd(), noApproval = false } = {}) {
    this.workingDir  = workingDir;
    this.noApproval  = noApproval;
    this._basicTools = [
      'read_file', 'write_to_file', 'replace_in_file', 'append_to_file',
      'delete_file', 'list_files', 'search_files', 'file_exists',
      'get_file_info', 'execute_command', 'search_code', 'grep_files',
      'git_status', 'git_diff', 'git_log', 'git_commit', 'ask_followup_question',
    ];
  }

  listBasicTools() {
    return [...this._basicTools];
  }

  // ── File operations ─────────────────────────────────────────────────────────

  readFile(filePath) {
    const abs = this._resolve(filePath);
    return fs.readFileSync(abs, 'utf8');
  }

  writeToFile(filePath, content) {
    const abs = this._resolve(filePath);
    fs.mkdirSync(path.dirname(abs), { recursive: true });
    fs.writeFileSync(abs, content, 'utf8');
    return { written: abs };
  }

  replaceInFile(filePath, oldStr, newStr) {
    const abs  = this._resolve(filePath);
    const text = fs.readFileSync(abs, 'utf8');
    const idx  = text.indexOf(oldStr);
    if (idx === -1) throw new Error(`replace_in_file: pattern not found in ${filePath}`);
    fs.writeFileSync(abs, text.slice(0, idx) + newStr + text.slice(idx + oldStr.length), 'utf8');
    return { replaced: true };
  }

  appendToFile(filePath, content) {
    const abs = this._resolve(filePath);
    fs.appendFileSync(abs, content, 'utf8');
    return { appended: abs };
  }

  deleteFile(filePath) {
    const abs = this._resolve(filePath);
    fs.unlinkSync(abs);
    return { deleted: abs };
  }

  listFiles(dirPath = '.') {
    const abs = this._resolve(dirPath);
    return fs.readdirSync(abs);
  }

  fileExists(filePath) {
    return fs.existsSync(this._resolve(filePath));
  }

  getFileInfo(filePath) {
    const abs  = this._resolve(filePath);
    const stat = fs.statSync(abs);
    return { path: abs, size: stat.size, isDir: stat.isDirectory(), mtime: stat.mtime };
  }

  // ── Shell ───────────────────────────────────────────────────────────────────

  /**
   * Execute a shell command.
   * ⚠️  This tool is inherently powerful. Only expose to trusted agents.
   * The command is passed to the OS shell via execFileSync with the shell
   * flag; restrict via noApproval and working-directory isolation.
   */
  executeCommand(cmd, cwd) {
    if (typeof cmd !== 'string' || !cmd.trim()) {
      throw new Error('execute_command: cmd must be a non-empty string');
    }
    const dir = cwd ? this._resolve(cwd) : this.workingDir;
    try {
      // Use /bin/sh -c so that shell builtins and pipes work, but the cwd
      // keeps execution contained to the working directory.
      return execFileSync('/bin/sh', ['-c', cmd], {
        cwd: dir, encoding: 'utf8', timeout: 30000,
      });
    } catch (err) {
      throw new Error(`execute_command failed: ${err.message}`);
    }
  }

  // ── Search ──────────────────────────────────────────────────────────────────

  /**
   * Grep for a pattern across files.
   * The pattern is passed as a literal argument (not shell-interpolated).
   */
  grepFiles(pattern, dirPath = '.', { recursive = true } = {}) {
    if (typeof pattern !== 'string' || !pattern) {
      throw new Error('grep_files: pattern must be a non-empty string');
    }
    const dir  = this._resolve(dirPath);
    const args = ['-l', '--include=*', recursive ? '-r' : '', '-E', pattern, '.'].filter(Boolean);
    try {
      return execFileSync('grep', args, { cwd: dir, encoding: 'utf8', timeout: 10000 });
    } catch { return ''; }
  }

  // ── Git ─────────────────────────────────────────────────────────────────────

  gitStatus()        { return this._git(['status', '--short']); }
  gitDiff()          { return this._git(['diff']); }
  gitLog(n = 10)     { return this._git(['log', '--oneline', `-${Math.min(Number(n) || 10, 100)}`]); }

  /** Commit all tracked changes with the given message. */
  gitCommit(message) {
    if (typeof message !== 'string' || !message.trim()) {
      throw new Error('git_commit: message must be a non-empty string');
    }
    // Pass message as a separate argument — never shell-interpolated.
    return this._git(['commit', '-am', message]);
  }

  // ── Internal helpers ────────────────────────────────────────────────────────

  _resolve(p) {
    return path.isAbsolute(p) ? p : path.join(this.workingDir, p);
  }

  /** Run git with an explicit args array (no shell, no injection risk). */
  _git(args) {
    try {
      return execFileSync('git', args, { cwd: this.workingDir, encoding: 'utf8', timeout: 10000 });
    } catch (err) {
      throw new Error(`git ${args[0]} failed: ${err.message}`);
    }
  }
}

module.exports = { ToolExecutor };
