export type Entry = { label: string; command: string; tags: string[] };
export type View = { term: string; entries: Entry[]; error?: string };

declare module "claude-code" {
	interface PluginState {
		quiver: { view: Shaped<View> };
	}
}
