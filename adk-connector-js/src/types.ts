export interface ConnectorConfig {
  /**
   * Telegram Bot Token from @BotFather.
   */
  token: string;
  /**
   * The root ADK Agent instance.
   */
  agent: any;
  /**
   * Optional application name. Defaults to agent's name.
   */
  appName?: string;
  /**
   * Whether to enable cross-device session synchronization (e.g. for adk web).
   */
  sessionManagementAcrossDevice?: boolean;
  /**
   * Optional developer Telegram user ID to map to the 'user' namespace.
   */
  devUserId?: string;
}
