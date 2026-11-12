import type { EngineInterface } from "claude-code";

export type Insertion =
	| { via: "prompt" }
	| { via: "clipboard"; reason: string }
	| { via: "none"; reason: string };

// The one insertion path list mode and pane mode both call. It writes the
// draft at the cursor and never submits, runs or calls a tool.
export async function insertCommand(
	$: EngineInterface,
	command: string,
): Promise<Insertion> {
	const filled = await $.prompt.fill({ text: command, mode: "insert" });
	if (filled.isFilled) return { via: "prompt" };

	// A hook's refusal carries no cause: an absent one reads as plain refused.
	const reason = filled.refusal ?? "refused";
	const copied = await $.ui.copy({ text: command });
	if (copied.isCopied) {
		$.ui.toast(`quiver: prompt unavailable (${reason}); copied to clipboard`);
		return { via: "clipboard", reason };
	}

	const both = `${reason}, ${copied.reason}`;
	$.ui.toast(`quiver: could not insert or copy (${both})`);
	return { via: "none", reason: both };
}
