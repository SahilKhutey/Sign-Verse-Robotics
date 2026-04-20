"use client";

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Grid, Environment, ContactShadows } from '@react-three/drei';
import { useStore } from '@/store/useStore';
import * as THREE from 'three';
import { Cpu, Zap, Activity, Globe, Sliders, Save, CheckCircle2, Folder } from 'lucide-react';
import { apiUrl } from '@/lib/api';
import type { RetargetFrame } from '@/types/telemetry';

function HumanoidArmature({ jointAngles }: { jointAngles: Record<string, number> }) {
  const group = useRef<THREE.Group>(null);
  const linkColor = "#00f2ff";
  const rad = (deg: number) => (deg * Math.PI) / 180;

  useFrame(() => {
    if (!group.current) return;
    group.current.rotation.y = rad(jointAngles['waist_yaw'] || 0);
  });

  return (
    <group ref={group} position={[0, -1, 0]}>
      <mesh>
        <sphereGeometry args={[0.15]} />
        <meshStandardMaterial color={linkColor} emissive={linkColor} emissiveIntensity={2} />
      </mesh>

      <mesh position={[0, 0.4, 0]}>
        <cylinderGeometry args={[0.05, 0.1, 0.8]} />
        <meshStandardMaterial color="#222" metalness={0.8} />
      </mesh>

      <group position={[-0.2, 0.8, 0]}>
        <group rotation={[rad(jointAngles['l_shoulder_pitch'] || 0), 0, 0]}>
          <mesh position={[0, -0.2, 0]}>
            <cylinderGeometry args={[0.03, 0.03, 0.4]} />
            <meshStandardMaterial color={linkColor} />
          </mesh>
          <group position={[0, -0.4, 0]} rotation={[rad(jointAngles['l_elbow_pitch'] || 0), 0, 0]}>
            <mesh position={[0, -0.2, 0]}>
              <cylinderGeometry args={[0.02, 0.02, 0.4]} />
              <meshStandardMaterial color={linkColor} />
            </mesh>
          </group>
        </group>
      </group>

      <group position={[0.2, 0.8, 0]}>
        <group rotation={[rad(jointAngles['r_shoulder_pitch'] || 0), 0, 0]}>
          <mesh position={[0, -0.2, 0]}>
            <cylinderGeometry args={[0.03, 0.03, 0.4]} />
            <meshStandardMaterial color={linkColor} />
          </mesh>
          <group position={[0, -0.4, 0]} rotation={[rad(jointAngles['r_elbow_pitch'] || 0), 0, 0]}>
            <mesh position={[0, -0.2, 0]}>
              <cylinderGeometry args={[0.02, 0.02, 0.4]} />
              <meshStandardMaterial color={linkColor} />
            </mesh>
          </group>
        </group>
      </group>
    </group>
  );
}

export default function SimulationWorkspace() {
  const [requestedSession, setRequestedSession] = useState<string | null>(null);
  const { isConnected, bridgeStatus, jointAngles } = useStore();

  const [sessions, setSessions] = useState<string[]>([]);
  const [selectedSession, setSelectedSession] = useState<string | null>(requestedSession);
  const [playbackFrames, setPlaybackFrames] = useState<RetargetFrame[]>([]);
  const [playbackIndex, setPlaybackIndex] = useState(0);
  const [playbackEnabled, setPlaybackEnabled] = useState(Boolean(requestedSession));
  const [smoothing, setSmoothing] = useState(0.85);
  const [damping, setDamping] = useState(0.05);
  const [isUpdating, setIsUpdating] = useState(false);
  const [lastSaved, setLastSaved] = useState<number | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const session = params.get('session');
    setRequestedSession(session);
    setSelectedSession(session);
    setPlaybackEnabled(Boolean(session));
  }, []);

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
        console.error("Failed to load sessions:", e);
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
        const res = await fetch(apiUrl(`/dataset/session/${selectedSession}/simulation/retarget`));
        if (!res.ok) {
          throw new Error("simulation-load");
        }
        const data = await res.json();
        setPlaybackFrames(data.frames || []);
        setPlaybackIndex(0);
      } catch (e) {
        console.error("Failed to load simulation frames:", e);
        setPlaybackFrames([]);
      }
    };
    loadPlayback();
  }, [selectedSession]);

  useEffect(() => {
    if (!playbackEnabled || playbackFrames.length === 0) return;
    const interval = setInterval(() => {
      setPlaybackIndex((prev) => (prev + 1) % playbackFrames.length);
    }, 333);
    return () => clearInterval(interval);
  }, [playbackEnabled, playbackFrames]);

  const updateKinematics = async () => {
    setIsUpdating(true);
    try {
      const res = await fetch(
        apiUrl(`/control/kinematics/config?smoothing=${encodeURIComponent(smoothing)}&damping=${encodeURIComponent(damping)}`),
        { method: "POST" }
      );
      if (res.ok) {
        setLastSaved(Date.now());
        setTimeout(() => setLastSaved(null), 2000);
      }
    } catch (e) {
      console.error(e);
    }
    setIsUpdating(false);
  };

  const displayJointAngles = useMemo(() => {
    if (playbackEnabled && playbackFrames[playbackIndex]) {
      return playbackFrames[playbackIndex].robot_joints;
    }
    return jointAngles;
  }, [jointAngles, playbackEnabled, playbackFrames, playbackIndex]);

  return (
    <div className="h-[calc(100vh-64px)] flex text-on-surface p-8 gap-8 overflow-hidden">
      <div className="flex-grow flex flex-col gap-6 overflow-hidden">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-space-grotesk font-light uppercase tracking-tighter">
              Hardware <span className="text-primary font-bold">Simulation</span>
            </h1>
            <p className="font-jetbrains-mono text-[10px] text-neutral-500 mt-2 flex items-center gap-2 uppercase">
              <Globe className="w-3 h-3" /> External Pipeline Integration // {playbackEnabled ? 'Archive_Replay' : 'Mount_Ready'}
            </p>
          </div>

          <div className="flex gap-4">
            <div className="bg-surface-container-high px-4 py-2 rounded-xl border border-outline-variant/10 text-right">
              <span className="block text-[9px] text-neutral-500 uppercase font-jetbrains-mono">Simulation Source</span>
              <span className="text-[18px] font-jetbrains-mono text-primary font-bold">{playbackEnabled ? 'SESSION' : isConnected ? 'LIVE' : 'IDLE'}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 bg-surface-container-high rounded-2xl border border-outline-variant/10 px-4 py-3">
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
            {playbackEnabled ? 'Archive Replay Enabled' : 'Use Session Replay'}
          </button>
        </div>

        <div className="flex-grow relative rounded-[2rem] overflow-hidden bg-black border border-outline-variant/10 shadow-2xl">
          <Canvas camera={{ position: [2, 2, 4], fov: 45 }}>
            <color attach="background" args={['#050505']} />
            <fog attach="fog" args={['#050505', 5, 15]} />

            <ambientLight intensity={0.4} />
            <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={2} color="#00f2ff" />
            <pointLight position={[-10, -10, -10]} intensity={1} color="#ff00ff" />

            <HumanoidArmature jointAngles={displayJointAngles} />

            <ContactShadows resolution={1024} scale={10} blur={2} opacity={0.5} far={10} color="#000000" />
            <Grid position={[0, -1, 0]} args={[10, 10]} cellColor="#111" sectionColor="#222" fadeDistance={15} fadeStrength={1} infiniteGrid />
            <OrbitControls makeDefault minPolarAngle={0} maxPolarAngle={Math.PI / 1.75} />
            <Environment preset="night" />
          </Canvas>

          <div className="absolute top-8 left-8 flex flex-col gap-4 pointer-events-none">
            <div className="bg-black/40 backdrop-blur-xl p-4 rounded-2xl border border-outline-variant/10">
              <div className="flex items-center gap-3 mb-2">
                <Activity className="w-4 h-4 text-primary animate-pulse" />
                <span className="text-[10px] font-jetbrains-mono text-white/50 uppercase tracking-widest">Pipeline Health</span>
              </div>
              <div className="flex gap-1">
                {Array(8).fill(0).map((_, i) => (
                  <div key={i} className={`w-4 h-1 rounded-full ${(isConnected || playbackEnabled) ? 'bg-primary' : 'bg-neutral-800'}`} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="w-80 flex flex-col gap-6 flex-shrink-0">
        <div className="flex items-center gap-2 px-2">
          <Cpu className="w-4 h-4 text-primary" />
          <h2 className="font-jetbrains-mono text-[11px] uppercase tracking-[0.2em] text-neutral-400">Control Plane</h2>
        </div>

        <div className="flex-grow bg-surface-container rounded-[2rem] border border-outline-variant/10 p-6 flex flex-col gap-6 shadow-xl overflow-y-auto custom-scrollbar">
          <div className="space-y-4">
            <h3 className="text-[10px] font-jetbrains-mono text-neutral-500 uppercase">External Bridges</h3>
            <div className="space-y-3">
              <div className={`flex items-center justify-between p-4 rounded-2xl border transition-all ${bridgeStatus.blender ? 'bg-primary/10 border-primary/20' : 'bg-black/20 border-outline-variant/10 opacity-50'}`}>
                <div className="flex items-center gap-3">
                  <Zap className={`w-4 h-4 ${bridgeStatus.blender ? 'text-primary' : 'text-neutral-500'}`} />
                  <span className="text-[12px] font-bold">Blender_WS</span>
                </div>
                <div className={`w-2 h-2 rounded-full ${bridgeStatus.blender ? 'bg-primary animate-pulse' : 'bg-neutral-800'}`}></div>
              </div>

              <div className={`flex items-center justify-between p-4 rounded-2xl border transition-all ${bridgeStatus.isaac ? 'bg-tertiary/10 border-tertiary/20' : 'bg-black/20 border-outline-variant/10 opacity-50'}`}>
                <div className="flex items-center gap-3">
                  <Cpu className={`w-4 h-4 ${bridgeStatus.isaac ? 'text-tertiary' : 'text-neutral-500'}`} />
                  <span className="text-[12px] font-bold">Isaac_UDP</span>
                </div>
                <div className={`w-2 h-2 rounded-full ${bridgeStatus.isaac ? 'bg-tertiary animate-pulse' : 'bg-neutral-800'}`}></div>
              </div>
            </div>
          </div>

          <div className="space-y-6 pt-4 border-t border-outline-variant/10">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-[10px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest">Kinematic Tuning</h3>
              <Sliders className="w-3.5 h-3.5 text-neutral-600" />
            </div>

            <div className="space-y-6">
              <div>
                <div className="flex justify-between text-[11px] font-jetbrains-mono mb-2">
                  <span className="text-neutral-400">EMA Smoothing</span>
                  <span className="text-primary">{smoothing.toFixed(2)}</span>
                </div>
                <input type="range" min="0" max="0.99" step="0.01" value={smoothing} onChange={(e) => setSmoothing(parseFloat(e.target.value))} className="w-full accent-primary h-1 bg-neutral-900 rounded-lg appearance-none cursor-pointer" />
              </div>

              <div>
                <div className="flex justify-between text-[11px] font-jetbrains-mono mb-2">
                  <span className="text-neutral-400">Lock Damping</span>
                  <span className="text-primary">{damping.toFixed(3)}</span>
                </div>
                <input type="range" min="0" max="0.2" step="0.001" value={damping} onChange={(e) => setDamping(parseFloat(e.target.value))} className="w-full accent-primary h-1 bg-neutral-900 rounded-lg appearance-none cursor-pointer" />
              </div>

              <button onClick={updateKinematics} disabled={isUpdating} className="w-full py-4 bg-primary/20 hover:bg-primary/30 text-primary border border-primary/40 rounded-2xl font-space-grotesk font-bold uppercase text-[11px] flex items-center justify-center gap-2 transition-all">
                {lastSaved ? <CheckCircle2 className="w-4 h-4" /> : <Save className="w-4 h-4" />}
                {isUpdating ? 'SYNCING...' : lastSaved ? 'CORE UPDATED' : 'APPLY HEURISTICS'}
              </button>
            </div>
          </div>

          <div className="p-5 bg-black/20 rounded-3xl border border-outline-variant/10">
            <h3 className="text-[9px] font-jetbrains-mono text-neutral-500 uppercase mb-3 tracking-widest">Replay Telemetry</h3>
            <div className="space-y-2">
              <div className="flex justify-between text-[10px] font-jetbrains-mono">
                <span className="text-neutral-600">Frame</span>
                <span className="text-white">{playbackFrames.length ? playbackIndex + 1 : 0} / {playbackFrames.length}</span>
              </div>
              <div className="flex justify-between text-[10px] font-jetbrains-mono">
                <span className="text-neutral-600">Mode</span>
                <span className="text-white">{playbackEnabled ? 'ARCHIVE' : 'LIVE'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
