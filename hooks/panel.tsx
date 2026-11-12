import type { EngineInterface, Register } from "claude-code";
import { atom, read, update } from "claude-code";
import type { Entry, View } from "../types";
import { insertCommand } from "./insert";

export const PANE = "quiver";

// Change the tag when View's fields change: it declines what an earlier
// version stored, which outlives a reload.
const view = atom(
	{ plugin: "quiver", key: "view" } as const,
	{ term: "", entries: [] },
	{ shape: "view-1" },
);

// Matching is the selector's (`filter_entries`), shared with list mode.
export async function runSelector(
	$: EngineInterface,
	term: string,
): Promise<View> {
	let ran: Awaited<ReturnType<EngineInterface["process"]["run"]>>;
	try {
		ran = await $.process.run([
			"python3",
			`${$.plugin.root}/cli/quiver.py`,
			"list",
			`--filter=${term}`,
		]);
	} catch (err) {
		const why = err instanceof Error ? err.message : String(err);
		return {
			term,
			entries: [],
			error: `error [selector]: could not run python3: ${why}`,
		};
	}
	if (ran.exitCode !== 0) {
		const first = ran.stderr.split("\n").find((line) => line.trim());
		return {
			term,
			entries: [],
			error: first ?? `error [selector]: exited ${ran.exitCode}`,
		};
	}
	try {
		const { entries } = JSON.parse(ran.stdout);
		if (Array.isArray(entries)) return { term, entries };
	} catch {}
	return { term, entries: [], error: "error [selector]: unreadable output" };
}

// The term typed last: a run that finishes after a newer one started is dropped.
// ponytail: one selector run per keystroke; debounce if typing lags
let latest = "";

async function filter($: EngineInterface, term: string) {
	latest = term;
	const fresh = await runSelector($, term);
	if (fresh.term === latest) await update($, view, () => fresh);
}

async function choose($: EngineInterface, entry: Entry | undefined) {
	if (!entry) return;
	await insertCommand($, entry.command);
	await $.ui.close({ id: PANE });
}

// The engine takes one unmatched session.start per module: register.ts
// registers the quiver command there.
export const registerPanel: Register = (on) => {
	on("command.run", { command: "quiver" }, async ($) => {
		await filter($, "");
		await $.ui.open({
			id: PANE,
			title: "Quiver",
			focus: true,
			closeOnEscape: true,
		});
		return { text: "Quiver pane opened." };
	});

	on("ui.render", { component: "Pane", requestId: PANE }, async ($, e) => {
		const { Box, Button, Input, Text } = $.ui.resolve(e);
		const { term, entries, error } = await read($, view);

		return (
			<Box flexDirection="column">
				<Input
					key="filter"
					autoFocus
					placeholder="filter"
					value={term}
					onInput={(value) => filter($, value)}
					onSubmit={() => choose($, entries[0])}
				/>
				{error && <Text color="red">{error}</Text>}
				{!error && entries.length === 0 && (
					<Text dimColor>No command matches "{term}".</Text>
				)}
				{entries.map((entry, i) => (
					<Button
						key={`row:${i}`}
						label={entry.label}
						onPress={() => choose($, entry)}
					>
						{entry.label} <Text dimColor>{entry.tags.join(" ")}</Text>
					</Button>
				))}
			</Box>
		);
	});
};
