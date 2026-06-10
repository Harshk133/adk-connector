import { Telegraf } from 'telegraf';
import { InMemoryRunner, isFinalResponse, stringifyContent } from '@google/adk';
import { ConnectorConfig } from './types.js';

/**
 * Dynamically extract all placeholder variables from agent instructions
 */
function findAllPlaceholders(agent: any): Set<string> {
  const placeholders = new Set<string>();
  if (!agent) return placeholders;

  const instruction = agent.instruction;

  if (typeof instruction === 'string') {
    const regex = /{+([^{}]+)}+/g;
    let match;
    while ((match = regex.exec(instruction)) !== null) {
      let varName = match[1].trim();
      if (varName.endsWith('?')) {
        varName = varName.slice(0, -1);
      }
      if (varName.startsWith('artifact.')) {
        continue;
      }
      if (varName.includes(':')) {
        varName = varName.split(':').pop() || '';
      }
      if (/^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(varName)) {
        placeholders.add(varName);
      }
    }
  } else if (instruction && typeof instruction.template === 'string') {
    const regex = /{+([^{}]+)}+/g;
    let match;
    while ((match = regex.exec(instruction.template)) !== null) {
      let varName = match[1].trim();
      if (varName.endsWith('?')) {
        varName = varName.slice(0, -1);
      }
      if (varName.startsWith('artifact.')) {
        continue;
      }
      if (varName.includes(':')) {
        varName = varName.split(':').pop() || '';
      }
      if (/^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(varName)) {
        placeholders.add(varName);
      }
    }
  }

  // Recursively check sub-agents and tools
  const subAgents = agent.subAgents || agent.sub_agents || [];
  const tools = agent.tools || [];

  for (const tool of tools) {
    const subAgent = tool.agent;
    if (subAgent) {
      for (const ph of findAllPlaceholders(subAgent)) {
        placeholders.add(ph);
      }
    }
  }

  for (const sa of subAgents) {
    for (const ph of findAllPlaceholders(sa)) {
      placeholders.add(ph);
    }
  }

  return placeholders;
}

export class TelegramConnector {
  private bot: Telegraf;
  private runner: any;
  private appName: string;
  private agent: any;

  constructor(config: ConnectorConfig) {
    if (!config.token) {
      throw new Error('Telegram Bot Token is required');
    }
    this.bot = new Telegraf(config.token);
    this.agent = config.agent;
    this.appName = config.appName || this.agent.name || 'adk_app';

    // Initialize the ADK Runner
    this.runner = new InMemoryRunner({
      agent: this.agent,
      appName: this.appName,
    });

    this.setupHandlers();
  }

  private setupHandlers() {
    this.bot.on('text', async (ctx) => {
      const userId = String(ctx.from.id);
      const sessionId = `telegram_session_${ctx.chat.id}`;
      const userMessage = ctx.message.text;

      try {
        // Show typing indicator
        await ctx.sendChatAction('typing');

        // Create or get the ADK session
        const session = await this.runner.sessionService.createSession({
          appName: this.appName,
          userId: userId,
          sessionId: sessionId,
        });

        // Seed state if missing to prevent compile KeyErrors in subagents
        const placeholders = findAllPlaceholders(this.agent);
        const coordinatorOutputKey = this.agent.outputKey || this.agent.output_key;

        if (!session.state) {
          session.state = {};
        }

        let stateUpdated = false;
        for (const ph of placeholders) {
          if (session.state[ph] === undefined) {
            stateUpdated = true;
            if (coordinatorOutputKey && ph === coordinatorOutputKey) {
              const fallbackVal = userMessage.trim().length > 5 && userMessage.trim().length < 100
                ? userMessage.trim()
                : 'Attention Is All You Need';
              session.state[ph] = fallbackVal;
            } else {
              session.state[ph] = '';
            }
          }
        }

        // Persist session update if state changed
        if (stateUpdated) {
          if (typeof this.runner.sessionService.updateSession === 'function') {
            await this.runner.sessionService.updateSession(session);
          } else if (typeof this.runner.sessionService.saveSession === 'function') {
            await this.runner.sessionService.saveSession(session);
          }
        }

        // Run the agent stream
        const stream = this.runner.runAsync({
          userId: userId,
          sessionId: session.id,
          newMessage: {
            role: 'user',
            parts: [{ text: userMessage }],
          },
        });

        let replyText = '';

        for await (const event of stream) {
          // Skip sub-agent execution events to keep chat feedback clean
          if (event.branch) {
            continue;
          }

          // Check if it's a final response event
          if (isFinalResponse(event)) {
            replyText = stringifyContent(event);
          }
        }

        if (!replyText.trim()) {
          replyText = '...';
        }

        // Send response back to Telegram
        await ctx.reply(replyText);
      } catch (error: any) {
        console.error('Error running ADK agent:', error);
        await ctx.reply(`⚠️ Error occurred while processing message: ${error.message}`);
      }
    });
  }

  /**
   * Starts the polling process.
   */
  public async start(): Promise<void> {
    console.log(`🚀 Starting Telegram Connector for JS/TS agent '${this.agent.name}'...`);
    this.bot.launch();

    // Enable graceful stop
    process.once('SIGINT', () => this.bot.stop('SIGINT'));
    process.once('SIGTERM', () => this.bot.stop('SIGTERM'));
  }
}
