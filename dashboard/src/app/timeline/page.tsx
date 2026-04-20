"use client";

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Play, Pause, Rewind, FastForward, Folder, RefreshCw, Layers, Film, GaugeCircle, Boxes } from 'lucide-react';
import SkeletonRenderer from '@/components/SkeletonRenderer';
import { apiUrl } from '@/lib/api';
import type { MotionFrame, SessionSummary } from '@/types/telemetry';

export default function MotionTimeline() {
  const [requestedSession, setRequestedSession] = useState<string | null>(null);
  const [sessions, setSessions] = useState<string[]>([]);
  const [selectedSession, setSelectedSession] = useState<string | null>(requestedSession);
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [frames, setFrames] = useState<MotionFrame[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setRequestedSession(params.get('session'));
  }, []);

  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(apiUrl("/dataset/sessions"));
      const data = await res.json();
      const nextSessions = data.sessions || [];
      setSessions(nextSessions);
      if (!selectedSession && nextSessions.length > 0) {
        setSelectedSession(requestedSession && nextSessions.includes(requestedSession) ? requestedSession : nextSessions[0]);
      }
    } catch (e) {
      console.error("Failed to load sessions:", e);
      setStatusMessage("Session repository unavailable.");
    }
  }, [requestedSession, selectedSession]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  useEffect(() => {
    if (requestedSession) {
      setSelectedSession(requestedSession);
    }
  }, [requestedSession]);

  const loadSession = async (name: string) => {
    setIsLoading(true);
    setSelectedSession(name);
    setIsPlaying(false);
    setStatusMessage(null);
    try {
      const [motionRes, summaryRes] = await Promise.all([
        fetch(apiUrl(`/dataset/session/${name}/motion`)),
        fetch(apiUrl(`/dataset/session/${name}/summary`)),
      ]);

      if (!motionRes.ok || !summaryRes.ok) {
        throw new Error("session-load");
      }

      const motionData = await motionRes.json();
      const summaryData = (await summaryRes.json()) as SessionSummary;
      setFrames(motionData.frames || []);
      setSummary(summaryData);
      setCurrentIndex(0);
      setStatusMessage(`Loaded ${summaryData.motion_frame_count} motion frames from ${name}.`);
    } catch (e) {
      console.error("Failed to load session data:", e);
      setFrames([]);
      setSummary(null);
      setStatusMessage("Failed to load replay session.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedSession) {
      loadSession(selectedSession);
    }
  }, [selectedSession]);

  const frameIntervalMs = useMemo(() => {
    if (summary?.effective_fps && summary.effective_fps > 0) {
      return Math.max(16, Math.round(1000 / summary.effective_fps));
    }
    if (frames.length > 1) {
      const delta = frames[1].timestamp - frames[0].timestamp;
      if (delta > 0) {
        return Math.max(16, Math.round(delta * 1000));
      }
    }
    return 33;
  }, [frames, summary]);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | undefined;
    if (isPlaying && frames.length > 0) {
      interval = setInterval(() => {
        setCurrentIndex((prev) => (prev + 1) % frames.length);
      }, frameIntervalMs);
    }
    return () => clearInterval(interval);
  }, [isPlaying, frames, frameIntervalMs]);

  const currentFrame = frames[currentIndex] || null;
  const previewJoints = currentFrame?.metadata?.pose_2d?.length
    ? currentFrame.metadata.pose_2d.map((joint) => [joint.x, joint.y, joint.z] as number[])
    : currentFrame?.joints || [];
  const timelineStart = frames.length > 0 ? frames[0].timestamp : 0;
  const currentRelativeTime = currentFrame ? currentFrame.timestamp - timelineStart : 0;
  const totalDuration = frames.length > 0 ? frames[frames.length - 1].timestamp - timelineStart : 0;

  return (
    <div className="h-[calc(100vh-64px)] w-full flex text-on-surface overflow-hidden">
      <div className="w-80 flex-shrink-0 bg-surface-container-low p-4 flex flex-col gap-4 border-r border-outline-variant/10">
        <div className="flex items-center justify-between">
          <h3 className="font-jetbrains-mono text-[10px] text-neutral-400 uppercase tracking-widest">Session Repository</h3>
          <button onClick={fetchSessions} className="text-primary hover:rotate-180 transition-transform duration-500">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-grow overflow-y-auto space-y-2 pr-1 custom-scrollbar">
          {sessions.map((session) => (
            <button
              key={session}
              onClick={() => loadSession(session)}
              className={`w-full text-left p-3 rounded-lg border transition-all ${
                selectedSession === session
                  ? 'bg-primary/10 border-primary text-primary'
                  : 'bg-surface-container-high border-outline-variant/10 text-neutral-400 hover:border-outline-variant/30'
              }`}
            >
              <div className="flex items-center gap-3">
                <Folder className="w-4 h-4" />
                <span className="font-jetbrains-mono text-[11px] truncate">{session}</span>
              </div>
            </button>
          ))}
          {sessions.length === 0 && (
            <p className="text-[10px] font-jetbrains-mono text-neutral-600 text-center py-8">NO RECORDINGS DETECTED</p>
          )}
        </div>
      </div>

      <div className="flex-grow flex flex-col p-6 gap-6 bg-surface-container-lowest overflow-hidden">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-space-grotesk font-bold uppercase tracking-tight">Timeline Editor</h2>
            <p className="font-jetbrains-mono text-[10px] text-neutral-500">
              {selectedSession ? `ANALYSING: ${selectedSession}` : 'AWAITING SESSION MOUNT...'}
            </p>
            {statusMessage && <p className="font-jetbrains-mono text-[10px] text-neutral-400 mt-2">{statusMessage}</p>}
          </div>
          {summary && (
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-surface-container-high px-3 py-2 rounded-lg border border-outline-variant/10">
                <span className="block text-[8px] text-neutral-500 uppercase font-jetbrains-mono">Tracked Frames</span>
                <span className="text-[14px] font-jetbrains-mono text-primary font-bold">{summary.tracked_frames}</span>
              </div>
              <div className="bg-surface-container-high px-3 py-2 rounded-lg border border-outline-variant/10">
                <span className="block text-[8px] text-neutral-500 uppercase font-jetbrains-mono">Duration</span>
                <span className="text-[14px] font-jetbrains-mono text-tertiary font-bold">{summary.duration_s.toFixed(1)}s</span>
              </div>
              <div className="bg-surface-container-high px-3 py-2 rounded-lg border border-outline-variant/10">
                <span className="block text-[8px] text-neutral-500 uppercase font-jetbrains-mono">Replay FPS</span>
                <span className="text-[14px] font-jetbrains-mono text-white font-bold">{(summary.effective_fps || 0).toFixed(2)}</span>
              </div>
            </div>
          )}
        </div>

        <div className="grid grid-cols-12 gap-6 min-h-0 flex-grow">
          <div className="col-span-12 xl:col-span-8 flex flex-col min-h-0">
            <div className="flex-grow relative bg-black rounded-2xl overflow-hidden ring-1 ring-outline-variant/20 shadow-2xl flex items-center justify-center p-8">
              {isLoading ? (
                <div className="flex flex-col items-center gap-4">
                  <RefreshCw className="w-12 h-12 text-primary animate-spin" />
                  <span className="font-jetbrains-mono text-primary animate-pulse text-[10px] uppercase">Buffering Kinematics...</span>
                </div>
              ) : currentFrame ? (
                <div className="w-full h-full max-w-[800px] aspect-video">
                  <SkeletonRenderer joints={previewJoints} />
                </div>
              ) : (
                <div className="flex flex-col items-center gap-4 opacity-30">
                  <Layers className="w-16 h-16 text-neutral-500" />
                  <span className="font-jetbrains-mono text-neutral-500 text-[10px] uppercase tracking-[0.2em]">Select session to begin reconstruction</span>
                </div>
              )}
            </div>
          </div>

          <div className="col-span-12 xl:col-span-4 flex flex-col gap-4 min-h-0">
            <div className="bg-surface-container-low border border-outline-variant/10 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <Film className="w-4 h-4 text-primary" />
                <span className="font-jetbrains-mono text-[10px] uppercase text-neutral-400 tracking-widest">Annotated Preview</span>
              </div>
              {selectedSession && summary?.has_preview ? (
                <video
                  key={selectedSession}
                  src={apiUrl(`/dataset/session/${selectedSession}/artifact/preview`)}
                  controls
                  preload="metadata"
                  className="w-full rounded-xl bg-black"
                />
              ) : (
                <div className="h-40 rounded-xl bg-black/40 flex items-center justify-center text-[10px] font-jetbrains-mono text-neutral-600 uppercase">
                  Preview unavailable
                </div>
              )}
            </div>

            <div className="bg-surface-container-low border border-outline-variant/10 rounded-xl p-4 space-y-4">
              <div className="flex items-center gap-2">
                <GaugeCircle className="w-4 h-4 text-primary" />
                <span className="font-jetbrains-mono text-[10px] uppercase text-neutral-400 tracking-widest">Frame Telemetry</span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-[10px] font-jetbrains-mono">
                <div className="bg-surface-container-high px-3 py-2 rounded-lg border border-outline-variant/10">
                  <span className="block text-neutral-500 uppercase">Seek</span>
                  <span className="text-primary">{currentRelativeTime.toFixed(3)}s</span>
                </div>
                <div className="bg-surface-container-high px-3 py-2 rounded-lg border border-outline-variant/10">
                  <span className="block text-neutral-500 uppercase">Confidence</span>
                  <span className="text-tertiary">{((currentFrame?.confidence || 0) * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-surface-container-high px-3 py-2 rounded-lg border border-outline-variant/10">
                  <span className="block text-neutral-500 uppercase">Subject</span>
                  <span className="text-white">{currentFrame?.metadata?.subject_id ?? "--"}</span>
                </div>
                <div className="bg-surface-container-high px-3 py-2 rounded-lg border border-outline-variant/10">
                  <span className="block text-neutral-500 uppercase">Track Hold</span>
                  <span className="text-white">{currentFrame?.metadata?.tracking?.missing_count ?? 0}</span>
                </div>
              </div>
              {summary?.source_video && (
                <div className="bg-black/20 rounded-lg border border-outline-variant/10 px-3 py-2 text-[10px] font-jetbrains-mono text-neutral-400 break-all">
                  <div className="flex items-center gap-2 mb-1">
                    <Boxes className="w-3 h-3 text-primary" />
                    <span className="uppercase tracking-widest">Source</span>
                  </div>
                  {summary.source_video}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="h-32 bg-surface-container-low border border-outline-variant/10 rounded-xl p-4 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              <button onClick={() => setCurrentIndex(0)} className="p-2 hover:bg-surface-container-highest rounded-lg transition-colors">
                <Rewind className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className={`p-2 rounded-lg transition-all ${isPlaying ? 'bg-primary text-on-primary' : 'hover:bg-surface-container-highest'}`}
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </button>
              <button onClick={() => setCurrentIndex(Math.max(0, frames.length - 1))} className="p-2 hover:bg-surface-container-highest rounded-lg transition-colors">
                <FastForward className="w-4 h-4" />
              </button>
            </div>

            <div className="font-jetbrains-mono text-[10px]">
              FRAME: <span className="text-primary">{frames.length ? currentIndex + 1 : 0}</span> / <span className="text-neutral-500">{frames.length}</span>
            </div>
          </div>

          <div className="relative h-6 flex items-center">
            <input
              type="range"
              min={0}
              max={Math.max(0, frames.length - 1)}
              value={currentIndex}
              onChange={(e) => setCurrentIndex(parseInt(e.target.value))}
              className="w-full h-1.5 bg-neutral-900 rounded-lg appearance-none cursor-pointer accent-primary"
            />
            <div className="absolute top-8 left-0 w-full flex justify-between text-[8px] font-jetbrains-mono text-neutral-600 uppercase">
              <span>START: 0.00s</span>
              <span>END: {totalDuration.toFixed(2)}s</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
