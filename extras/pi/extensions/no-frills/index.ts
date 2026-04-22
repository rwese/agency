/**
 * Pi No-Frills Extension
 *
 * Hides or modifies decorations in the pi TUI:
 * - Tool boxes (bash, read, edit, write, find, grep, ls)
 * - Thinking blocks
 * - Working indicator
 * - Footer
 * - Header
 *
 * Settings are read from ~/.pi/agent/settings.json under the "noFrills" key:
 *
 * {
 *   "noFrills": {
 *     "tools": "borderless",  // "full" | "borderless" | "minimal"
 *     "thinking": true,        // hide thinking blocks
 *     "workingIndicator": true, // hide working spinner
 *     "footer": false,         // hide footer
 *     "header": false          // hide header
 *   }
 * }
 *
 * Or use /deco command to toggle interactively.
 */

import {
	CustomEditor,
	ExtensionAPI,
	type ExtensionContext,
	type ReadonlySessionManager,
} from "@mariozechner/pi-coding-agent";
import {
	createBashTool,
	createEditTool,
	createFindTool,
	createGrepTool,
	createLsTool,
	createReadTool,
	createWriteTool,
	getSettingsListTheme,
} from "@mariozechner/pi-coding-agent";
import { Container, SettingsList, Text, truncateToWidth, visibleWidth, type SettingItem } from "@mariozechner/pi-tui";

export interface LineSymbolPresets {
	/** Horizontal line character */
	horizontal?: string;
	/** Vertical line character (for future use) */
	vertical?: string;
	/** Corner/border characters (top-left, top-right, bottom-left, bottom-right) */
	corners?: [string, string, string, string];
	/** Prompt icon shown at start of each content line */
	promptIcon?: string;
}

export interface NoFrillsSettings {
	/** Tool box style: "full" (default boxes), "borderless" (no bg), "minimal" (call only) */
	tools?: "full" | "borderless" | "minimal";
	/** Hide thinking blocks */
	thinking?: boolean;
	/** Hide working indicator spinner */
	workingIndicator?: boolean;
	/** Hide footer */
	footer?: boolean;
	/** Hide header */
	header?: boolean;
	/** Custom line symbols for editor borders */
	lineSymbols?: LineSymbolPresets | string; // Preset name or custom config
}

/** Built-in line symbol presets */
const LINE_SYMBOL_PRESETS: Record<string, LineSymbolPresets> = {
	double: { horizontal: "═", vertical: "║", corners: ["╔", "╗", "╚", "╝"], promptIcon: "║ " },
	light: { horizontal: "─", vertical: "│", corners: ["┌", "┐", "└", "┘"], promptIcon: "│ " },
	heavy: { horizontal: "━", vertical: "┃", corners: ["┏", "┓", "┗", "┛"], promptIcon: "┃ " },
	lightTriple: { horizontal: "─", vertical: "│", corners: ["╭", "╮", "╰", "╯"], promptIcon: "│ " },
	block: { horizontal: "█", vertical: "█", corners: ["█", "█", "█", "█"], promptIcon: "█ " },
	minimal: { horizontal: " ", vertical: " ", corners: [" ", " ", " ", " "] },
	pipe: { horizontal: "-", vertical: "|", corners: ["+", "+", "+", "+"], promptIcon: "| " },
	dots: { horizontal: "·", vertical: ":", corners: ["·", "·", "·", "·"], promptIcon: ": " },
	stars: { horizontal: "*", vertical: "*", corners: ["*", "*", "*", "*"], promptIcon: "* " },
};

const DEFAULT_SETTINGS: NoFrillsSettings = {
	tools: "full",
	thinking: false,
	workingIndicator: false,
	footer: false,
	header: false,
	lineSymbols: "light",
};

let currentSettings: NoFrillsSettings = { ...DEFAULT_SETTINGS };
let cwd = process.cwd();

/**
 * Load settings from settings.json, then override with env vars.
 *
 * Env vars (all optional):
 *   PI_NOFILLS_TOOLS         - "full" | "borderless" | "minimal"
 *   PI_NOFILLS_THINKING      - "1" | "0" | "true" | "false"
 *   PI_NOFILLS_WORKING       - "1" | "0" | "true" | "false"
 *   PI_NOFILLS_FOOTER        - "1" | "0" | "true" | "false"
 *   PI_NOFILLS_HEADER        - "1" | "0" | "true" | "false"
 *   PI_NOFILLS_LINES         - line symbol preset name (e.g. "minimal", "double")
 */
function loadSettings(): NoFrillsSettings {
	// Start with defaults, then json, then env (env wins)
	let settings = { ...DEFAULT_SETTINGS };

	try {
		const settingsPath = `${process.env.HOME || "~"}/.pi/agent/settings.json`;
		const fs = require("node:fs");
		if (fs.existsSync(settingsPath)) {
			const content = fs.readFileSync(settingsPath, "utf-8");
			const json = JSON.parse(content);
			if (json.noFrills) {
				settings = { ...settings, ...json.noFrills };
			}
		}
	} catch {
		// Ignore errors, use defaults
	}

	// Env overrides
	if (process.env.PI_NOFILLS_TOOLS) {
		const val = process.env.PI_NOFILLS_TOOLS!;
		if (val === "full" || val === "borderless" || val === "minimal") {
			settings.tools = val;
		}
	}
	if (process.env.PI_NOFILLS_THINKING !== undefined) {
		settings.thinking = isTruthy(process.env.PI_NOFILLS_THINKING);
	}
	if (process.env.PI_NOFILLS_WORKING !== undefined) {
		settings.workingIndicator = isTruthy(process.env.PI_NOFILLS_WORKING);
	}
	if (process.env.PI_NOFILLS_FOOTER !== undefined) {
		settings.footer = isTruthy(process.env.PI_NOFILLS_FOOTER);
	}
	if (process.env.PI_NOFILLS_HEADER !== undefined) {
		settings.header = isTruthy(process.env.PI_NOFILLS_HEADER);
	}
	if (process.env.PI_NOFILLS_LINES) {
		settings.lineSymbols = process.env.PI_NOFILLS_LINES;
	}

	return settings;
}

/**
 * Parse boolean from env string: "1", "true", "yes" → true; anything else → false
 */
function isTruthy(val: string): boolean {
	return val === "1" || val.toLowerCase() === "true" || val.toLowerCase() === "yes";
}

/**
 * Save settings to settings.json
 */
function saveSettings(settings: NoFrillsSettings): void {
	try {
		const settingsPath = `${process.env.HOME}/.pi/agent/settings.json`;
		const fs = require("node:fs");
		let existing: Record<string, unknown> = {};
		if (fs.existsSync(settingsPath)) {
			existing = JSON.parse(fs.readFileSync(settingsPath, "utf-8"));
		}
		existing.noFrills = settings;
		fs.writeFileSync(settingsPath, JSON.stringify(existing, null, 2) + "\n");
	} catch (e) {
		console.error("Failed to save settings:", e);
	}
}

/**
 * Apply all decoration settings
 */
function applySettings(ctx: ExtensionContext): void {
	const s = currentSettings;

	// Tool style is applied via registerTool() calls
	// For now, we re-register on settings change

	// Thinking
	ctx.ui.setHiddenThinkingLabel(s.thinking ? "..." : undefined);

	// Working indicator
	if (s.workingIndicator) {
		ctx.ui.setWorkingIndicator({ frames: [] });
	} else {
		ctx.ui.setWorkingIndicator();
	}

	// Footer
	if (s.footer) {
		ctx.ui.setFooter(() => ({
			render: () => [],
			invalidate: () => {},
		}));
	} else {
		ctx.ui.setFooter(undefined);
	}

	// Header
	if (s.header) {
		ctx.ui.setHeader(() => ({
			render: () => [],
			invalidate: () => {},
		}));
	} else {
		ctx.ui.setHeader(undefined);
	}
}

/**
 * Create a borderless/minimal tool registration
 */
function createToolRenderers(
	toolName: string,
	originalTool: ReturnType<typeof createReadTool>,
	style: "borderless" | "minimal",
) {
	return {
		name: toolName,
		label: toolName,
		description: originalTool.description,
		parameters: originalTool.parameters,

		async execute(toolCallId: string, params: any, signal: any, onUpdate: any) {
			return originalTool.execute(toolCallId, params, signal, onUpdate);
		},

		renderCall(args: any, theme: any, _context: any) {
			switch (toolName) {
				case "read": {
					const path = args.path || "...";
					let text = theme.fg("toolTitle", theme.bold("read")) + " ";
					text += theme.fg("accent", path);
					if (args.offset || args.limit) {
						const start = args.offset ?? 1;
						const end = args.limit ? start + args.limit - 1 : "";
						text += theme.fg("muted", `:${start}${end ? `-${end}` : ""}`);
					}
					return new Text(text, 0, 0);
				}
				case "bash": {
					const cmd = args.command || "...";
					return new Text(
						theme.fg("toolTitle", theme.bold("$")) +
							" " +
							theme.fg("accent", cmd.length > 80 ? cmd.slice(0, 77) + "..." : cmd),
						0,
						0,
					);
				}
				case "write": {
					const path = args.path || "...";
					const lines = args.content ? args.content.split("\n").length : 0;
					let text = theme.fg("toolTitle", theme.bold("write")) + " ";
					text += theme.fg("accent", path);
					if (lines > 0) {
						text += theme.fg("muted", ` (${lines} lines)`);
					}
					return new Text(text, 0, 0);
				}
				case "edit": {
					const path = args.path || "...";
					return new Text(
						theme.fg("toolTitle", theme.bold("edit")) + " " + theme.fg("accent", path),
						0,
						0,
					);
				}
				case "find": {
					const pattern = args.pattern || "";
					const path = args.path || ".";
					return new Text(
						theme.fg("toolTitle", theme.bold("find")) +
							" " +
							theme.fg("accent", pattern) +
							theme.fg("muted", ` in ${path}`),
						0,
						0,
					);
				}
				case "grep": {
					const pattern = args.pattern || "";
					const path = args.path || ".";
					return new Text(
						theme.fg("toolTitle", theme.bold("grep")) +
							" " +
							theme.fg("accent", `/${pattern}/`) +
							theme.fg("muted", ` in ${path}`),
						0,
						0,
					);
				}
				case "ls": {
					const path = args.path || ".";
					return new Text(
						theme.fg("toolTitle", theme.bold("ls")) + " " + theme.fg("accent", path),
						0,
						0,
					);
				}
				default:
					return new Text(theme.fg("toolTitle", theme.bold(toolName)), 0, 0);
			}
		},

		renderResult(result: any, opts: any, theme: any, _context: any) {
			const { expanded, isPartial } = opts;

			if (isPartial) {
				return new Text(theme.fg("muted", "..."), 0, 0);
			}

			// Minimal: show nothing
			if (style === "minimal") {
				return new Text("", 0, 0);
			}

			// Borderless: show result text only
			const textContent = result.content.find((c: any) => c.type === "text");
			if (!textContent) {
				return new Text("", 0, 0);
			}

			const text = textContent.text.trim();
			if (!text) {
				return new Text("", 0, 0);
			}

			// Count lines/matches for summary
			const lines = text.split("\n").filter(Boolean);
			const count = lines.length;

			if (style === "borderless") {
				// Show count only in collapsed mode
				if (!expanded) {
					let summary = "";
					if (toolName === "bash" && text.includes("exit code:")) {
						const exitMatch = text.match(/exit code: (\d+)/);
						if (exitMatch) {
							const code = parseInt(exitMatch[1], 10);
							summary = code === 0
								? theme.fg("success", "✓")
								: theme.fg("error", `✗ ${code}`);
						}
					} else if (toolName === "read") {
						summary = theme.fg("muted", `${count} lines`);
					} else {
						summary = theme.fg("muted", `${count} lines`);
					}
					return new Text(summary, 0, 0);
				}

				// Expanded: show first 10 lines
				const preview = lines.slice(0, 10).join("\n");
				return new Text(
					theme.fg("toolOutput", preview) +
						(count > 10 ? `\n${theme.fg("muted", `... ${count - 10} more`)}` : ""),
					0,
					0,
				);
			}

			return new Text(theme.fg("toolOutput", text), 0, 0);
		},
	};
}

/**
 * Get the current line symbol configuration
 */
function getLineSymbols(): { horizontal: string; corners: [string, string, string, string]; promptIcon: string } {
	const config = currentSettings.lineSymbols;
	
	if (typeof config === "string") {
		const preset = LINE_SYMBOL_PRESETS[config];
		if (preset) {
			return {
				horizontal: preset.horizontal || "─",
				corners: preset.corners || ["┌", "┐", "└", "┘"],
				promptIcon: preset.promptIcon || "> ",
			};
		}
	}
	
	if (config && typeof config === "object") {
		return {
			horizontal: config.horizontal || "─",
			corners: config.corners || ["┌", "┐", "└", "┘"],
			promptIcon: config.promptIcon || "> ",
		};
	}
	
	return { horizontal: "─", corners: ["┌", "┐", "└", "┘"], promptIcon: "> " };
}

/**
 * Custom editor with customizable line symbols and prompt icon
 */
class LineSymbolEditor extends CustomEditor {
	render(width: number): string[] {
		// Get custom line symbols
		const { horizontal, corners, promptIcon } = getLineSymbols();
		const [tl, tr, bl, br] = corners;
		
		// Get default rendering
		const lines = super.render(width);
		
		if (lines.length < 2) return lines;
		
		// Replace top border
		lines[0] = tl + horizontal.repeat(width - 2) + tr;
		
		// Add prompt icon to content lines (between borders)
		for (let i = 1; i < lines.length - 1; i++) {
			// Remove existing padding from left
			lines[i] = lines[i].trimStart();
			// Truncate content to make room for icon
			const maxContentWidth = width - promptIcon.length;
			lines[i] = truncateToWidth(lines[i], maxContentWidth, "");
			// Add prompt icon
			if (lines[i].length > 0 || promptIcon.trim().length > 0) {
				lines[i] = promptIcon + lines[i];
			}
		}
		
		// Replace bottom border
		lines[lines.length - 1] = bl + horizontal.repeat(width - 2) + br;
		
		// Apply border color to borders
		lines[0] = this.borderColor(lines[0]);
		lines[lines.length - 1] = this.borderColor(lines[lines.length - 1]);
		
		return lines;
	}
}

/**
 * Register all tool overrides based on current settings
 */
function registerToolOverrides(pi: ExtensionAPI, style: "full" | "borderless" | "minimal") {
	if (style === "full") {
		// Don't override - use default rendering
		return;
	}

	// Re-create tools with custom rendering
	const tools = {
		read: createReadTool(cwd),
		bash: createBashTool(cwd),
		write: createWriteTool(cwd),
		edit: createEditTool(cwd),
		find: createFindTool(cwd),
		grep: createGrepTool(cwd),
		ls: createLsTool(cwd),
	};

	// Register each tool with borderless/minimal rendering
	for (const [name, tool] of Object.entries(tools)) {
		pi.registerTool(createToolRenderers(name, tool as any, style) as any);
	}
}

export default function (pi: ExtensionAPI) {
	// Load settings on startup
	currentSettings = loadSettings();

	// Get initial cwd for tool creation
	cwd = process.cwd();

	// Register tool overrides based on settings
	registerToolOverrides(pi, currentSettings.tools || "full");

	// Session start: apply all settings and register custom editor
	pi.on("session_start", async (_event, ctx) => {
		cwd = ctx.cwd;
		applySettings(ctx);
		
		// Register custom editor with line symbols
		ctx.ui.setEditorComponent((tui, theme, kb) => new LineSymbolEditor(tui, theme, kb));
	});

	// /deco command - opens settings UI when no args
	pi.registerCommand("deco", {
		description: "Toggle decorations on/off. Usage: /deco [setting] [on|off]",
		handler: async (args, ctx) => {
			const parts = args.trim().split(/\s+/);
			const setting = parts[0]?.toLowerCase();
			const value = parts[1]?.toLowerCase();

			// If no args, open settings UI
			if (!setting) {
				await ctx.ui.custom((tui, theme, _kb, done) => {
					const updateSetting = (key: keyof NoFrillsSettings, newValue: any) => {
						currentSettings[key] = newValue;
						saveSettings(currentSettings);
					};

					const lineSymbolPresets = Object.keys(LINE_SYMBOL_PRESETS);
					const currentLineSymbol = typeof currentSettings.lineSymbols === "string" 
						? currentSettings.lineSymbols 
						: "custom";

					const items: SettingItem[] = [
						{
							id: "tools",
							label: "Tool Rendering",
							currentValue: currentSettings.tools || "full",
							values: ["full", "borderless", "minimal"],
						},
						{
							id: "lineSymbols",
							label: "Editor Lines",
							currentValue: currentLineSymbol,
							values: lineSymbolPresets,
						},
						{
							id: "thinking",
							label: "Thinking Blocks",
							currentValue: currentSettings.thinking ? "hidden" : "shown",
							values: ["shown", "hidden"],
						},
						{
							id: "workingIndicator",
							label: "Working Indicator",
							currentValue: currentSettings.workingIndicator ? "hidden" : "shown",
							values: ["shown", "hidden"],
						},
						{
							id: "footer",
							label: "Footer",
							currentValue: currentSettings.footer ? "hidden" : "shown",
							values: ["shown", "hidden"],
						},
						{
							id: "header",
							label: "Header",
							currentValue: currentSettings.header ? "hidden" : "shown",
							values: ["shown", "hidden"],
						},
					];

					const container = new Container();
					container.addChild(
						new (class {
							render(_width: number) {
								return [
									theme.fg("accent", theme.bold("Decoration Settings")),
									"",
								];
							}
							invalidate() {}
						})(),
					);

					const settingsList = new SettingsList(
						items,
						Math.min(items.length + 2, 10),
						getSettingsListTheme(),
						(id, newValue) => {
							switch (id) {
								case "tools":
									currentSettings.tools = newValue as any;
									updateSetting("tools", currentSettings.tools);
									registerToolOverrides(pi, currentSettings.tools || "full");
									ctx.ui.notify("Tool changes require /reload to take effect", "info");
									break;
								case "lineSymbols":
									if (newValue === "custom") {
										ctx.ui.notify("Custom via settings.json", "info");
										break;
									}
									currentSettings.lineSymbols = newValue;
									updateSetting("lineSymbols", currentSettings.lineSymbols);
									ctx.ui.notify(`Lines: ${newValue}`, "info");
									break;
								case "thinking":
									currentSettings.thinking = newValue === "hidden";
									updateSetting("thinking", currentSettings.thinking);
									ctx.ui.setHiddenThinkingLabel(currentSettings.thinking ? "..." : undefined);
									break;
								case "workingIndicator":
									currentSettings.workingIndicator = newValue === "hidden";
									updateSetting("workingIndicator", currentSettings.workingIndicator);
									if (currentSettings.workingIndicator) {
										ctx.ui.setWorkingIndicator({ frames: [] });
									} else {
										ctx.ui.setWorkingIndicator();
									}
									break;
								case "footer":
									currentSettings.footer = newValue === "hidden";
									updateSetting("footer", currentSettings.footer);
									if (currentSettings.footer) {
										ctx.ui.setFooter(() => ({ render: () => [], invalidate: () => {} }));
									} else {
										ctx.ui.setFooter(undefined);
									}
									break;
								case "header":
									currentSettings.header = newValue === "hidden";
									updateSetting("header", currentSettings.header);
									if (currentSettings.header) {
										ctx.ui.setHeader(() => ({ render: () => [], invalidate: () => {} }));
									} else {
										ctx.ui.setHeader(undefined);
									}
									break;
							}
						},
						() => {
							done(undefined);
						},
					);

					container.addChild(settingsList);

					const component = {
						render(width: number) {
							return container.render(width);
						},
						invalidate() {
							container.invalidate();
						},
						handleInput(data: string) {
							settingsList.handleInput?.(data);
							tui.requestRender();
						},
					};

					return component;
				});
				return;
			}

			// Toggle or set specific setting
			if (setting === "tools") {
				const modes = ["full", "borderless", "minimal"];
				if (value && modes.includes(value)) {
					currentSettings.tools = value as any;
				} else {
					const idx = modes.indexOf(currentSettings.tools || "full");
					currentSettings.tools = modes[(idx + 1) % modes.length] as any;
				}
				ctx.ui.notify(`tools = ${currentSettings.tools}`, "info");

				// Re-register tool overrides
				registerToolOverrides(pi, currentSettings.tools || "full");
				ctx.ui.notify("Reload /reload to apply tool changes", "info");
			} else if (setting === "thinking") {
				currentSettings.thinking = !currentSettings.thinking;
				ctx.ui.notify(`thinking = ${currentSettings.thinking}`, "info");
				ctx.ui.setHiddenThinkingLabel(currentSettings.thinking ? "..." : undefined);
			} else if (setting === "working") {
				currentSettings.workingIndicator = !currentSettings.workingIndicator;
				ctx.ui.notify(`workingIndicator = ${currentSettings.workingIndicator}`, "info");
				if (currentSettings.workingIndicator) {
					ctx.ui.setWorkingIndicator({ frames: [] });
				} else {
					ctx.ui.setWorkingIndicator();
				}
			} else if (setting === "footer") {
				currentSettings.footer = !currentSettings.footer;
				ctx.ui.notify(`footer = ${currentSettings.footer}`, "info");
				if (currentSettings.footer) {
					ctx.ui.setFooter(() => ({ render: () => [], invalidate: () => {} }));
				} else {
					ctx.ui.setFooter(undefined);
				}
			} else if (setting === "header") {
				currentSettings.header = !currentSettings.header;
				ctx.ui.notify(`header = ${currentSettings.header}`, "info");
				if (currentSettings.header) {
					ctx.ui.setHeader(() => ({ render: () => [], invalidate: () => {} }));
				} else {
					ctx.ui.setHeader(undefined);
				}
			} else if (setting === "all") {
				const newVal = value !== "off";
				currentSettings.thinking = newVal;
				currentSettings.workingIndicator = newVal;
				currentSettings.footer = newVal;
				currentSettings.header = newVal;
				ctx.ui.notify(`all = ${newVal}`, "info");
				applySettings(ctx);
			} else {
				ctx.ui.notify(`Unknown setting: ${setting}`, "warning");
				ctx.ui.notify("Use: tools, thinking, working, footer, header, all", "info");
				return;
			}

			// Save settings
			saveSettings(currentSettings);
		},
	});

	// /deco-list command to show all settings
	pi.registerCommand("deco-list", {
		description: "List all decoration settings",
		handler: async (_args, ctx) => {
			const s = currentSettings;
			const lines = [
				"Decoration Settings:",
				`  tools:        ${s.tools || "full"}`,
				`  thinking:     ${s.thinking ? "hidden" : "shown"}`,
				`  working:      ${s.workingIndicator ? "hidden" : "shown"}`,
				`  footer:       ${s.footer ? "hidden" : "shown"}`,
				`  header:       ${s.header ? "hidden" : "shown"}`,
				"",
				"Edit ~/.pi/agent/settings.json to persist.",
			];

			for (const line of lines) {
				ctx.ui.notify(line, "info");
			}
		},
	});
}
