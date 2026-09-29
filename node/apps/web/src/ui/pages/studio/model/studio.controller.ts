"use client";
import { useState, type FormEvent } from "react";
import { useRead, useCommand } from "@/env/cache";
import { useDependencies } from "@/ui/di";
import type { Job } from "@/core/entities";

export function useStudioController() {
  const deps = useDependencies();
  const jobs = useRead(deps.listJobs, deps.entities);
  const submit = useCommand(deps.createJob, deps.entities);
  const [file, setFile] = useState<File | null>(null);
  const [width, setWidth] = useState(1200);
  const [height, setHeight] = useState(1200);
  const [format, setFormat] = useState<Job["format"]>("webp");
  const [error, setError] = useState<string | null>(null);
  const [requestKey, setRequestKey] = useState<string | null>(null);
  const reset = () => setRequestKey(null);
  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!file) {
      setError("Выбери изображение.");

      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("Файл должен быть не больше 10 МиБ.");

      return;
    }
    const key = requestKey ?? crypto.randomUUID();
    setRequestKey(key);
    try {
      await submit.execute({ image: file, width, height, format, idempotencyKey: key });
      setRequestKey(null);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Не удалось создать задание");
    }
  }

  return {
    jobs,
    submit,
    file,
    width,
    height,
    format,
    error,
    onSubmit,
    selectFile: (value: File | null) => {
      setFile(value);
      reset();
    },
    changeWidth: (value: number) => {
      setWidth(value);
      reset();
    },
    changeHeight: (value: number) => {
      setHeight(value);
      reset();
    },
    changeFormat: (value: Job["format"]) => {
      setFormat(value);
      reset();
    },
  };
}
