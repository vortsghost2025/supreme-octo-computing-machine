'use strict';

const { EnhancedToolExecutor } = require('./tools/enhanced-executor');

/**
 * Creates a free coding agent instance.
 *
 * @param {object} [opts]
 * @param {string} [opts.provider]    - LLM provider (ollama | groq | together)
 * @param {string} [opts.model]       - Model name
 * @param {boolean} [opts.noApproval] - Skip approval prompts for destructive ops
 * @param {string} [opts.workingDir]  - Working directory for file operations
 */
async function createAgent(opts = {}) {
  const provider   = opts.provider   || process.env.PROVIDER    || 'ollama';
  const model      = opts.model      || process.env.MODEL       || 'llama3.2';
  const noApproval = opts.noApproval ?? (process.env.NO_APPROVAL === 'true');
  const workingDir = opts.workingDir || process.env.WORKING_DIR || process.cwd();

  const executor = new EnhancedToolExecutor({ workingDir, noApproval });
  await executor.init();

  return {
    /**
     * List all tools available to this agent.
     * @returns {Promise<string[]>}
     */
    async listTools() {
      return executor.listTools();
    },

    /**
     * Run a task with the agent.
     * This is a stub — replace with real LLM orchestration loop.
     *
     * @param {string} task
     * @returns {Promise<object>}
     */
    async run(task) {
      console.log(`[agent] run — provider=${provider} model=${model} task="${task.slice(0, 80)}..."`);

      // Stub: return a plan without actually calling the LLM.
      // Replace this block with a real LLM + tool-use loop.
      return {
        provider,
        model,
        task,
        steps: [],
        note: 'Agent stub — connect an LLM provider to activate full execution.',
      };
    },
  };
}

module.exports = { createAgent };
