"use client";
import { createContext, useContext } from "react";
import type { CreateJob } from "@/app/commands/create_job";
import type { ListJobs } from "@/app/queries/list_jobs";
import type { EntityStore } from "@/env/cache";
export interface Dependencies {
  createJob: CreateJob;
  listJobs: ListJobs;
  entities: EntityStore;
}
export const DependenciesContext = createContext<Dependencies | null>(null);
export function useDependencies() {
  const value = useContext(DependenciesContext);
  if (!value) throw new Error("Dependencies provider is missing");

  return value;
}
