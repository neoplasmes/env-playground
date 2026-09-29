import { createStore } from "zustand/vanilla";
import type { EntityRef, Job } from "@/core/entities";
export type EntityPatch =
  | { ref: EntityRef; patch: Partial<Job> }
  | { ref: EntityRef; remove: true };
export class EntityStore {
  readonly state = createStore<{ entities: Record<string, Job> }>(() => ({ entities: {} }));
  private base: Record<string, Job> = {};
  private layers = new Map<symbol, EntityPatch[]>();
  get(ref: EntityRef) {
    return this.state.getState().entities[ref];
  }
  upsert(ref: EntityRef, partial: Partial<Job>) {
    const fields = Object.fromEntries(Object.entries(partial).filter(([, v]) => v !== undefined));
    this.base = { ...this.base, [ref]: { ...this.base[ref], ...fields, ref } as Job };
    this.publish();
  }
  remove(ref: EntityRef) {
    const next = { ...this.base };
    delete next[ref];
    this.base = next;
    this.publish();
  }
  begin() {
    const key = Symbol();
    this.layers.set(key, []);

    return {
      apply: (patches: EntityPatch[]) => {
        if (this.layers.has(key)) {
          this.layers.set(key, patches);
          this.publish();
        }
      },
      discard: () => {
        this.layers.delete(key);
        this.publish();
      },
    };
  }
  collect(retained: Set<EntityRef>) {
    const keep = new Set(retained);
    for (const patches of this.layers.values()) for (const patch of patches) keep.add(patch.ref);
    for (const key of Object.keys(this.base))
      if (!keep.has(key as EntityRef)) delete this.base[key];
    this.publish();
  }
  private publish() {
    const next = { ...this.base };
    for (const patches of this.layers.values())
      for (const entry of patches) {
        if ("remove" in entry) delete next[entry.ref];
        else
          next[entry.ref] = {
            ...next[entry.ref],
            ...Object.fromEntries(Object.entries(entry.patch).filter(([, v]) => v !== undefined)),
            ref: entry.ref,
          } as Job;
      }
    const previous = this.state.getState().entities;
    for (const key of Object.keys(next)) {
      if (previous[key] && JSON.stringify(previous[key]) === JSON.stringify(next[key]))
        next[key] = previous[key];
    }
    if (
      Object.keys(next).length === Object.keys(previous).length &&
      Object.keys(next).every((key) => next[key] === previous[key])
    )
      return;
    this.state.setState({ entities: next });
  }
}
