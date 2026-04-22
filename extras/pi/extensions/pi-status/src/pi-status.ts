/**
 * pi-status Extension
 *
 * Unix socket server providing read-only access to pi agent state.
 * Enables external monitoring, health checks, and integration
 * with external dashboards or scripts.
 *
 * Socket path: PI_STATUS_SOCKET env var or ~/.pi/pi-status-<pid>.sock
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { createServer, type Server, type Socket } from "node:net";
import { homedir } from "node:os";
import { join } from "node:path";
import { existsSync, unlinkSync } from "node:fs";

// Socket file path
const getSocketPath = (): string =>
	process.env.PI_STATUS_SOCKET || join(homedir(), ".pi", `pi-status-${process.pid}.sock`);

// Current task being worked on (set by manager or agent)
let currentTask: string | undefined;
let currentTaskId: string | undefined;

// Response types
interface StatusResponse {
	type: "ok" | "error" | "pong";
	data?: AgentStatus;
	message?: string;
}

interface AgentStatus {
	// Core state
	running: boolean;
	idle: boolean;
	sessionActive: boolean;

	// Session info
	sessionName?: string;
	sessionFile?: string;
	cwd: string;

	// Current task (for agency integration)
	currentTask?: string;
	currentTaskId?: string;

	// Turn info
	currentTurn?: {
		index: number;
		startTime: number;
		durationMs: number;
	};

	// Message stats
	messageCount: number;
	userMessageCount: number;
	assistantMessageCount: number;
	toolResultCount: number;

	// Tool execution
	currentToolCalls: Array<{
		toolCallId: string;
		toolName: string;
		startTime: number;
	}>;
	completedToolCalls: number;

	// Model info
	model?: {
		id: string;
		provider: string;
	};

	// Timestamps
	startedAt: number;
	lastActivityAt: number;
}

export default function (pi: ExtensionAPI) {
	let server: Server | null = null;

	// State tracking
	let isIdle = true;
	let sessionActive = false;
	let sessionFile: string | undefined;
	let currentTurnIndex = 0;
	let turnStartTime = 0;
	let startedAt = Date.now();
	let lastActivityAt = Date.now();
	let completedToolCalls = 0;
	let currentModel: { id: string; provider: string } | undefined;

	const currentToolCalls: Array<{ toolCallId: string; toolName: string; startTime: number }> = [];
	const messageCounts = { user: 0, assistant: 0, toolResult: 0 };

	// Track events
	pi.on("session_start", async (_event, ctx) => {
		sessionActive = true;
		isIdle = true;
		sessionFile = ctx.sessionManager.getSessionFile() ?? undefined;
		startedAt = Date.now();
		lastActivityAt = Date.now();
		currentTurnIndex = 0;
		currentToolCalls.length = 0;
		completedToolCalls = 0;
		messageCounts.user = 0;
		messageCounts.assistant = 0;
		messageCounts.toolResult = 0;
		// Capture initial model from context
		if (ctx.model) {
			currentModel = { id: ctx.model.id, provider: ctx.model.provider };
		}
	});

	pi.on("session_shutdown", () => {
		sessionActive = false;
		isIdle = true;
	});

	pi.on("agent_start", () => {
		isIdle = false;
		lastActivityAt = Date.now();
	});

	pi.on("agent_end", () => {
		isIdle = true;
		lastActivityAt = Date.now();
	});

	pi.on("turn_start", (event) => {
		currentTurnIndex = event.turnIndex;
		turnStartTime = event.timestamp;
		isIdle = false;
		lastActivityAt = Date.now();
		currentToolCalls.length = 0;
	});

	pi.on("turn_end", () => {
		isIdle = true;
		lastActivityAt = Date.now();
	});

	pi.on("tool_execution_start", (event) => {
		currentToolCalls.push({
			toolCallId: event.toolCallId,
			toolName: event.toolName,
			startTime: Date.now(),
		});
		lastActivityAt = Date.now();
	});

	pi.on("tool_execution_end", (event) => {
		const idx = currentToolCalls.findIndex(t => t.toolCallId === event.toolCallId);
		if (idx !== -1) {
			currentToolCalls.splice(idx, 1);
		}
		completedToolCalls++;
		lastActivityAt = Date.now();
	});

	pi.on("message_end", (event) => {
		if (event.message.role === "user") {
			messageCounts.user++;
		} else if (event.message.role === "assistant") {
			messageCounts.assistant++;
		} else if (event.message.role === "toolResult") {
			messageCounts.toolResult++;
		}
		lastActivityAt = Date.now();
	});

	pi.on("model_select", (event) => {
		currentModel = { id: event.model.id, provider: event.model.provider };
	});

	/**
	 * Build current status snapshot
	 */
	function getStatus(): AgentStatus {
		return {
			running: sessionActive,
			idle: isIdle,
			sessionActive,
			sessionName: pi.getSessionName() ?? undefined,
			sessionFile,
			cwd: process.cwd(),
			currentTask,
			currentTaskId,
			currentTurn: currentTurnIndex > 0 ? {
				index: currentTurnIndex,
				startTime: turnStartTime,
				durationMs: Date.now() - turnStartTime,
			} : undefined,
			messageCount: messageCounts.user + messageCounts.assistant + messageCounts.toolResult,
			userMessageCount: messageCounts.user,
			assistantMessageCount: messageCounts.assistant,
			toolResultCount: messageCounts.toolResult,
			currentToolCalls: [...currentToolCalls],
			completedToolCalls,
			model: currentModel,
			startedAt,
			lastActivityAt,
		};
	}

	/**
	 * Start the Unix socket server
	 */
	function startServer(): void {
		if (server) return;

		const socketPath = getSocketPath();

		// Clean up existing socket
		try {
			if (existsSync(socketPath)) {
				unlinkSync(socketPath);
			}
		} catch {
			// Ignore
		}

		server = createServer((socket: Socket) => {
			let buffer = "";

			socket.on("data", (data: Buffer) => {
				buffer += data.toString();

				let newlineIndex: number;
				while ((newlineIndex = buffer.indexOf("\n")) !== -1) {
					const line = buffer.slice(0, newlineIndex);
					buffer = buffer.slice(newlineIndex + 1);

					if (!line.trim()) continue;

					const response = processMessage(line.trim());
					socket.write(JSON.stringify(response) + "\n");
				}
			});

			socket.on("error", (err) => {
				console.error("[pi-status] Socket error:", err.message);
			});

			socket.on("close", () => {
				buffer = "";
			});
		});

		server.listen(socketPath, () => {
			console.log(`[pi-status] Listening on ${socketPath}`);
		});

		server.on("error", (err: NodeJS.ErrnoException) => {
			if (err.code === "EADDRINUSE") {
				console.log("[pi-status] Socket already in use, skipping");
			} else {
				console.error("[pi-status] Server error:", err.message);
			}
			server = null;
		});
	}

	/**
	 * Process incoming message
	 */
	function processMessage(raw: string): StatusResponse {
		try {
			const msg = JSON.parse(raw);
			const action = msg.action || msg.type;

			switch (action) {
				case "ping":
					return { type: "pong" };

				case "status":
				case "get":
					return { type: "ok", data: getStatus() };

				case "health":
					return {
						type: "ok",
						data: {
							running: sessionActive,
							idle: isIdle,
							sessionFile,
							currentTask,
							currentTaskId,
							lastActivityAt,
						} as AgentStatus,
					};

				case "set_task": {
					// Set the current task (used by agency)
					const taskId = msg.taskId as string | undefined;
					const taskDescription = msg.task as string | undefined;
					if (taskId !== undefined) {
						currentTaskId = taskId;
						currentTask = taskDescription;
						return { type: "ok", message: `Task set to ${taskId}` };
					}
					return { type: "error", message: "taskId required" };
				}

				case "clear_task": {
					currentTask = undefined;
					currentTaskId = undefined;
					return { type: "ok", message: "Task cleared" };
				}

				default:
					return { type: "error", message: `Unknown action: ${action}` };
			}
		} catch (err) {
			return { type: "error", message: `Parse error: ${(err as Error).message}` };
		}
	}

	// Register commands
	pi.registerCommand("status-socket", {
		description: "Check pi-status socket status",
		handler: async (_args, ctx) => {
			if (server) {
				ctx.ui.notify(`pi-status: listening on ${getSocketPath()}`, "info");
			} else {
				ctx.ui.notify("pi-status: not running", "warning");
			}
		},
	});

	// Start server
	pi.on("session_start", async () => {
		startServer();
	});

	// Cleanup
	pi.on("session_shutdown", async () => {
		if (server) {
			server.close();
			server = null;
		}
	});
}
