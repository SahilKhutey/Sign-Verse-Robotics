"use client";

import React, { useEffect, useMemo, useState } from 'react';
import { Settings2, Activity, ShieldCheck, Zap, RefreshCw, Folder } from 'lucide-react';
import { useStore } from '@/store/useStore';
import SkeletonRenderer from '@/components/SkeletonRenderer';
import RobotRenderer from '@/components/RobotRenderer';
import { apiUrl } from '@/lib/api';
import type { RetargetFrame, Simulation2DFrame } from '@/types/telemetry';

export default function Retargeting() {
  const [requestedSession, setRequestedSession] = useState<string | null>(null);
  const { jointAngles, isConnected } = useStore();

  const [smoothing, setSmoothing] = useState(0.4);
  const [damping, setDamping] = useState(0.05);
  const [isLoading, setIsLoading] = useState(false);
  const [sessions, setSessions] = useState<string[]>([]);
  const [selectedSession, setSelectedSession] = useState<string | null>(requestedSession);
  const [retargetFrames, setRetargetFrames] = useState<RetargetFrame[]>([]);
  const [humanFrames, setHumanFrames] = useState<Simulation2DFrame[]>([]);
  const [playbackIndex, setPlaybackIndex] = useState(0);
  const [playbackEnabled, setPlaybackEnabled] = useState(Boolean(requestedSession));

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const session = params.get('session');
    setRequestedSession(session);
    setSelectedSession(session);
    setPlaybackEnabled(Boolean(session));
  }, []);

  const updateHeuristics = async () => {
    setIsLoading(true);
    try {
      await fetch(apiUrl(`/control/kinematics/config?smoothing=${smoothing}&damping=${damping}`), {
        method: 'POST'
      });
    } catch (e) {
      console.error("Failed to update heuristics:", e);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const res = await fetch(apiUrl("/dataset/sessions"));
        const data = await res.json();
        const nextSessions = data.sessions || [];
        setSessions(nextSessions);
        if (!selectedSession && nextSessions.length > 0) {
          setSelectedSession(requestedSession && nextSessions.includes(requestedSession) ? requestedSession : nextSessions[0]);
        }
      } catch (e) {
        console.error("Failed to load archive sessions:", e);
      }
    };
    fetchSessions();
  }, [requestedSession, selectedSession]);

  useEffect(() => {
    if (requestedSession) {
      setSelectedSession(requestedSession);
      setPlaybackEnabled(true);
    }
  }, [requestedSession]);

  useEffect(() => {
    if (!selectedSession) return;
    const loadPlayback = async () => {
      try {
        const [retargetRes, humanRes] = await Promise.all([
          fetch(apiUrl(`/dataset/session/${selectedSession}/simulation/retarget`)),
          fetch(apiUrl(`/dataset/session/${selectedSession}/simulation/2d`)),
        ]);
        if (!retargetRes.ok || !humanRes.ok) {
          throw new Error("playback-load");
        }
        const retargetData = await retargetRes.json();
        const humanData = await humanRes.json();
        setRetargetFrames(retargetData.frames || []);
        setHumanFrames(humanData.frames || []);
        setPlaybackIndex(0);
      } catch (e) {
        console.error("Failed to load session playback:", e);
        setRetargetFrames([]);
        setHumanFrames([]);
      }
    };
    loadPlayback();
  }, [selectedSession]);

  useEffect(() => {
    if (!playbackEnabled || retargetFrames.length === 0) return;
    const interval = setInterval(() => {
      setPlaybackIndex((prev) => (prev + 1) % retargetFrames.length);
    }, 333);
    return () => clearInterval(interval);
  }, [playbackEnabled, retargetFrames]);

  const activeRetargetFrame = retargetFrames[playbackIndex];
  const activeHumanFrame = humanFrames[Math.min(playbackIndex, humanFrames.length - 1)];
  const displayRobotJoints = playbackEnabled && activeRetargetFrame ? activeRetargetFrame.robot_joints : jointAngles;
  const displayHumanJoints = useMemo(
    () => activeHumanFrame?.pose?.map((joint) => [joint.x, joint.y, joint.z] as number[]) || [],
    [activeHumanFrame]
  );

  return (
    <div className="p-8 max-w-[1700px] mx-auto text-on-surface h-[calc(100vh-64px)] flex flex-col gap-8 overflow-hidden">
      <div className="flex justify-between items-start flex-shrink-0 gap-6">
        <div>
          <h1 className="text-4xl font-space-grotesk font-light uppercase tracking-tighter">
            Robot <span className="text-primary font-bold">Retargeting</span>
          </h1>
          <p className="font-jetbrains-mono text-[10px] text-neutral-500 mt-2 flex items-center gap-2">
            <ShieldCheck className="w-3 h-3" /> KINEMATIC SOLVER // KERNEL V.3.2
          </p>
        </div>

        <div className="flex gap-4">
          <div className="bg-surface-container-high px-4 py-2 rounded-xl border border-outline-variant/10 text-right">
            <span className="block text-[9px] text-neutral-500 uppercase font-jetbrains-mono">Source Mode</span>
            <span className="text-[18px] font-jetbrains-mono text-primary font-bold">
              {playbackEnabled ? 'ARCHIVE' : isConnected ? 'LIVE' : 'IDLE'}
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3 bg-surface-container-high rounded-2xl border border-outline-variant/10 px-4 py-3 flex-shrink-0">
        <Folder className="w-4 h-4 text-primary" />
        <select
          value={selectedSession || ''}
          onChange={(e) => {
            setSelectedSession(e.target.value || null);
            setPlaybackEnabled(Boolean(e.target.value));
          }}
          className="bg-black/30 border border-outline-variant/10 rounded-xl px-3 py-2 text-[11px] font-jetbrains-mono min-w-[320px]"
        >
          <option value="">Live telemetry</option>
          {sessions.map((session) => (
            <option key={session} value={session}>{session}</option>
          ))}
        </select>
        <button
          onClick={() => setPlaybackEnabled((value) => !value)}
          disabled={!selectedSession}
          className="px-4 py-2 rounded-xl border border-primary/20 bg-primary/10 text-primary text-[10px] font-jetbrains-mono uppercase disabled:opacity-40"
        >
          {playbackEnabled ? 'Using Archive Replay' : 'Switch To Replay'}
        </button>
      </div>

      <div className="flex-grow grid grid-cols-12 gap-8 overflow-hidden">
        <div className="col-span-12 lg:col-span-8 grid grid-cols-2 gap-6 overflow-hidden">
          <div className="flex flex-col gap-4 overflow-hidden">
            <div className="flex items-center justify-between px-2">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-primary" />
                <h3 className="font-jetbrains-mono text-[11px] uppercase tracking-[0.2em] text-neutral-400">Human Source_01</h3>
              </div>
              <span className="text-[9px] text-neutral-500 font-jetbrains-mono">{playbackEnabled ? 'ARCHIVE_POSE_2D' : 'RAW_LANDMARKS'}</span>
            </div>
            <div className="flex-grow bg-black rounded-3xl border border-outline-variant/10 relative overflow-hidden flex items-center justify-center p-8 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-from)_0%,_transparent_70%)] from-primary/5 shadow-2xl">
              <SkeletonRenderer joints={displayHumanJoints} />
              <div className="absolute inset-0 border border-primary/5 pointer-events-none grid grid-cols-6 grid-rows-6">
                {Array(36).fill(0).map((_, i) => <div key={i} className="border border-primary/5" />)}
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-4 overflow-hidden">
            <div className="flex items-center justify-between px-2">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-primary" />
                <h3 className="font-jetbrains-mono text-[11px] uppercase tracking-[0.2em] text-neutral-400">Robot Target_01</h3>
              </div>
              <span className="text-[9px] text-primary font-jetbrains-mono bg-primary/10 px-2 py-0.5 rounded">{playbackEnabled ? 'REPLAY_ACTIVE' : 'SOLVER_ACTIVE'}</span>
            </div>
            <div className="flex-grow bg-black rounded-3xl border border-outline-variant/10 relative overflow-hidden flex items-center justify-center p-8 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-from)_0%,_transparent_70%)] from-primary/10 shadow-2xl">
              <RobotRenderer jointAngles={displayRobotJoints} />
            </div>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4 flex flex-col gap-4">
          <div className="flex items-center gap-2 px-2">
            <Settings2 className="w-4 h-4 text-primary" />
            <h3 className="font-jetbrains-mono text-[11px] uppercase tracking-[0.2em] text-neutral-400">Kinematic Heuristics</h3>
          </div>

          <div className="flex-grow bg-surface-container rounded-3xl border border-outline-variant/10 p-6 space-y-8 shadow-xl overflow-y-auto custom-scrollbar">
            <div className="space-y-4">
              <div className="flex justify-between items-end">
                <label className="text-[10px] font-jetbrains-mono text-neutral-300 uppercase">Smoothing Factor</label>
                <span className="text-[12px] font-jetbrains-mono text-primary font-bold">{smoothing.toFixed(2)}</span>
              </div>
              <input type="range" min={0} max={0.95} step={0.05} value={smoothing} onChange={(e) => setSmoothing(parseFloat(e.target.value))} className="w-full h-1.5 bg-neutral-900 rounded-lg appearance-none cursor-pointer accent-primary" />
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-end">
                <label className="text-[10px] font-jetbrains-mono text-neutral-300 uppercase">Damping Coefficient</label>
                <span className="text-[12px] font-jetbrains-mono text-primary font-bold">{damping.toFixed(3)}</span>
              </div>
              <input type="range" min={0.001} max={0.2} step={0.001} value={damping} onChange={(e) => setDamping(parseFloat(e.target.value))} className="w-full h-1.5 bg-neutral-900 rounded-lg appearance-none cursor-pointer accent-primary" />
            </div>

            <div className="pt-4 border-t border-outline-variant/10">
              <button onClick={updateHeuristics} disabled={isLoading} className="w-full py-4 bg-primary text-black rounded-2xl font-space-grotesk font-bold uppercase text-[12px] hover:bg-primary-light transition-all shadow-lg shadow-primary/20">
                {isLoading ? 'DEPLOYING KERNEL...' : 'PUSH HEURISTICS TO CORE'}
              </button>
            </div>

            <div className="pt-4 border-t border-outline-variant/10 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[9px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest">Replay Frame</span>
                <button onClick={() => setPlaybackIndex(0)} className="text-neutral-400 hover:text-primary">
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              </div>
              <input
                type="range"
                min={0}
                max={Math.max(0, retargetFrames.length - 1)}
                value={Math.min(playbackIndex, Math.max(0, retargetFrames.length - 1))}
                onChange={(e) => setPlaybackIndex(parseInt(e.target.value))}
                className="w-full accent-primary h-1 bg-neutral-900 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-jetbrains-mono text-neutral-500">
                <span>{retargetFrames.length ? playbackIndex + 1 : 0} / {retargetFrames.length}</span>
                <span>{selectedSession || 'live'}</span>
              </div>
            </div>

            <div className="space-y-4 pt-4">
              <h4 className="text-[9px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest border-b border-outline-variant/10 pb-2">Active Joint Payload</h4>
              <div className="grid grid-cols-2 gap-x-6 gap-y-3">
                {Object.entries(displayRobotJoints).filter(([k]) => k.includes('pitch') || k.includes('yaw')).map(([joint, angle]) => (
                  <div key={joint} className="flex justify-between items-center bg-black/30 p-2 rounded-lg border border-outline-variant/5">
                    <span className="text-[9px] font-jetbrains-mono text-neutral-500 truncate mr-2">{joint.replace('_pitch', '')}</span>
                    <span className={`${Math.abs(angle) > 90 ? 'text-error' : 'text-tertiary'} text-[10px] font-bold font-jetbrains-mono`}>{`${angle.toFixed(1)} deg`}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
