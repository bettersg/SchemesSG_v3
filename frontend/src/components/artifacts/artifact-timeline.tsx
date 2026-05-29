"use client";

import { Artifact, useChat } from "@/app/(main)/providers";
import clsx from "clsx";

const formatArtifactTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Now";
  }
  return new Intl.DateTimeFormat("en-SG", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
};

const buildArtifactSubtitle = (artifact: Artifact) => {
  const total = artifact.totalCount;
  if (artifact.queryText && artifact.queryText.trim() !== "") {
    return `${total} cards from \"${artifact.queryText}\"`;
  }
  return `${total} cards`;
};

export default function ArtifactTimeline() {
  const {
    artifacts,
    activeArtifactId,
    setActiveArtifactId,
    setSchemes,
    setTotalCount,
    setIsArtifactsPanelOpen,
  } = useChat();

  if (artifacts.length === 0) {
    return null;
  }

  return (
    <div className="mb-3 rounded-xl border border-slate-200 bg-white/80 p-2">
      <p className="px-1 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
        Session Snapshots
      </p>
      <div className="mt-2 flex gap-2 overflow-x-auto pb-1">
        {artifacts.map((artifact, index) => {
          const isActive = artifact.artifactId === activeArtifactId;
          return (
            <button
              key={artifact.artifactId}
              type="button"
              onClick={() => {
                setActiveArtifactId(artifact.artifactId);
                setSchemes(artifact.schemes);
                setTotalCount(artifact.totalCount);
                setIsArtifactsPanelOpen(true);
              }}
              className={clsx(
                "min-w-[220px] rounded-lg border p-3 text-left transition-colors",
                "hover:border-schemes-blue/50 hover:bg-schemes-blue/[0.06]",
                isActive
                  ? "border-schemes-blue bg-schemes-blue/[0.08]"
                  : "border-slate-200 bg-white"
              )}
            >
              <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                Snapshot {index + 1}
              </p>
              <p className="mt-1 truncate text-sm font-semibold text-slate-800">
                {artifact.title}
              </p>
              <p className="mt-1 line-clamp-2 text-xs text-slate-600">
                {buildArtifactSubtitle(artifact)}
              </p>
              <p className="mt-2 text-[11px] text-slate-500">
                {formatArtifactTime(artifact.createdAt)}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
