#!/usr/bin/env node
/**
 * pi-status CLI
 * 
 * Query pi agent status via Unix Domain Socket.
 * 
 * Usage:
 *   pi-status status       Show full status
 *   pi-status health       Quick health check
 *   pi-status ping          Ping the socket
 */

import { createConnection } from "node:net";
import { homedir } from "node:os";
import { join } from "node:path";

const getSocketPath = (): string =>
	process.env.PI_STATUS_SOCKET || join(homedir(), ".pi", "status.sock");

interface StatusResponse {
	type: "ok" | "error" | "pong";
	data?: any;
	message?: string;
}

async function sendMessage(
	socketPath: string,
	action: string,
	timeout = 5
): Promise<StatusResponse> {
	return new Promise((resolve, reject) => {
		const socket = createConnection(socketPath, () => {
			socket.write(JSON.stringify({ action }) + "\n");
		});

		let buffer = "";

		const timer = setTimeout(() => {
			socket.destroy();
			reject(new Error(`Connection timeout after ${timeout}s`));
		}, timeout * 1000);

		socket.on("data", (data: Buffer) => {
			buffer += data.toString();
			const lines = buffer.split("\n");
			buffer = lines.pop() ?? "";

			for (const line of lines) {
				if (line.trim()) {
					try {
						clearTimeout(timer);
						socket.end();
						resolve(JSON.parse(line.trim()));
					} catch {
						// Continue
					}
				}
			}
		});

		socket.on("error", (err: NodeJS.ErrnoException) => {
			clearTimeout(timer);
			if (err.code === "ECONNREFUSED") {
				reject(new Error("pi-status socket not running (connection refused)"));
			} else if (err.code === "ENOENT") {
				reject(new Error("pi-status socket not found"));
			} else {
				reject(new Error(`Connection error: ${err.message}`));
			}
		});
	});
}

function formatBytes(bytes: number): string {
	if (bytes < 1024) return `${bytes}B`;
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
	return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

function formatDuration(ms: number): string {
	if (ms < 1000) return `${ms}ms`;
	if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
	return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
}

async function main(): Promise<void> {
	const args = process.argv.slice(2);
	const action = args[0] || "status";

	try {
		const socketPath = getSocketPath();

		if (action === "ping") {
			const res = await sendMessage(socketPath, "ping");
			if (res.type === "pong") {
				console.log("pong");
				process.exit(0);
			}
			console.error(`Error: ${res.message}`);
			process.exit(1);
		}

		if (action === "health") {
			const res = await sendMessage(socketPath, "health");
			if (res.type !== "ok" || !res.data) {
				console.error(`Error: ${res.message}`);
				process.exit(1);
			}
			
			const { running, idle, lastActivityAt } = res.data;
			const elapsed = Date.now() - lastActivityAt;
			
			console.log(`Running: ${running ? "yes" : "no"}`);
			console.log(`Idle:    ${idle ? "yes" : "no"}`);
			console.log(`Idle for: ${formatDuration(elapsed)}`);
			process.exit(0);
		}

		// Default: full status
		const res = await sendMessage(socketPath, "status");
		if (res.type !== "ok" || !res.data) {
			console.error(`Error: ${res.message}`);
			process.exit(1);
		}

		const d = res.data;
		
		console.log("=== pi Status ===");
		console.log(`Session:   ${d.sessionActive ? "active" : "inactive"}`);
		console.log(`State:     ${d.idle ? "idle" : "busy"}`);
		if (d.sessionName) console.log(`Name:      ${d.sessionName}`);
		console.log(`CWD:       ${d.cwd}`);
		
		if (d.model) {
			console.log(`Model:     ${d.model.provider}/${d.model.id}`);
		}
		
		console.log("\n--- Activity ---");
		console.log(`Messages:  ${d.messageCount} (${d.userMessageCount}u/${d.assistantMessageCount}a/${d.toolResultCount}t)`);
		console.log(`Tools:     ${d.completedToolCalls} completed`);
		
		if (d.currentToolCalls?.length > 0) {
			console.log(`Running:   ${d.currentToolCalls.map((t: any) => t.toolName).join(", ")}`);
		}
		
		console.log("\n--- Timing ---");
		console.log(`Started:   ${new Date(d.startedAt).toISOString()}`);
		console.log(`Active:    ${formatDuration(Date.now() - d.lastActivityAt)} ago`);
		
		if (d.currentTurn) {
			console.log(`Turn:      #${d.currentTurn.index} (${formatDuration(d.currentTurn.durationMs)})`);
		}
	} catch (err) {
		console.error(`Error: ${(err as Error).message}`);
		process.exit(1);
	}
}

main();
