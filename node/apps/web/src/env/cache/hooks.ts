"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useStore } from "zustand";
import type { CreateJob } from "@/app/commands/create_job";
import type { ListJobs } from "@/app/queries/list_jobs";
import type { EntityRef, SubmitImage } from "@/core/entities";
import { EntityStore } from "./entity_store";

export function useRead(query: ListJobs, store: EntityStore) {
  const result = useQuery({
    queryKey: [query.name],
    queryFn: async ({ signal }) => {
      const jobs = await query.execute(undefined, { signal });
      for (const job of jobs) store.upsert(job.ref, job);

      return jobs.map((job) => job.ref);
    },
    meta: { tags: query.reads() },
    refetchInterval: 2000,
    staleTime: 1000,
  });
  const entities = useStore(store.state, (state) => state.entities);

  return { ...result, data: result.data?.map((ref) => entities[ref]).filter(Boolean) };
}
export function useCommand(command: CreateJob, store: EntityStore) {
  const client = useQueryClient();
  const mutation = useMutation({
    mutationFn: (input: SubmitImage) => command.execute(input),
    onSuccess: async (job) => {
      store.upsert(job.ref, job);
      await client.invalidateQueries({
        predicate: (query) => {
          const tags = (query.meta?.tags ?? []) as EntityRef[];

          return command.writes().some((ref) => tags.includes(ref));
        },
      });
    },
  });

  return { execute: mutation.mutateAsync, isPending: mutation.isPending, error: mutation.error };
}
