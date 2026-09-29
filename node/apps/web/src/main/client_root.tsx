"use client";
import { useEffect, useState, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CreateJob } from "@/app/commands/create_job";
import { ListJobs } from "@/app/queries/list_jobs";
import { EntityStore } from "@/env/cache";
import { TransportJobRepo } from "@/env/repos/job";
import { HttpTransport } from "@/env/transport";
import { DependenciesContext } from "@/ui/di";
import type { EntityRef } from "@/core/entities";

export function ClientRoot({ children }: { children: ReactNode }) {
  const [runtime] = useState(() => {
    const repo = new TransportJobRepo(new HttpTransport());

    return {
      client: new QueryClient(),
      deps: {
        createJob: new CreateJob(repo),
        listJobs: new ListJobs(repo),
        entities: new EntityStore(),
      },
    };
  });
  useEffect(() => {
    const timer = setInterval(() => {
      const retained = new Set<EntityRef>();
      for (const query of runtime.client.getQueryCache().getAll()) {
        if (Array.isArray(query.state.data))
          for (const ref of query.state.data)
            if (typeof ref === "string") retained.add(ref as EntityRef);
      }
      runtime.deps.entities.collect(retained);
    }, 60_000);

    return () => {
      clearInterval(timer);
      runtime.client.clear();
    };
  }, [runtime]);

  return (
    <QueryClientProvider client={runtime.client}>
      <DependenciesContext.Provider value={runtime.deps}>{children}</DependenciesContext.Provider>
    </QueryClientProvider>
  );
}
