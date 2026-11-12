import type { Register } from "claude-code";
import { insertCommand } from "./insert";
import { registerPanel } from "./panel";

const ANSWER = {
	prompt: "Inserted into the prompt.",
	clipboard: "Prompt unavailable; the command is on the clipboard.",
	none: "The command could not be placed anywhere.",
} as const;

export const register: Register = (on, options) => {
	on("session.start", async ($, e, next) => {
		await $.command.register({
			name: "quiver-insert",
			description: "Put a command in the prompt without submitting it",
			argumentHint: "<command>",
		});
		await $.command.register({
			name: "quiver",
			description: "Pick a saved command in a pane and insert it",
		});
		return next(e);
	});

	on("command.run", { command: "quiver-insert" }, async ($, e) => {
		if (!e.args.trim()) return { text: "Usage: /quiver-insert <command>" };
		const done = await insertCommand($, e.args);
		return { text: ANSWER[done.via] };
	});

	registerPanel(on, options);
};
