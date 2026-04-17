"use client";
import React, { useEffect } from 'react';
import RobotViewer3D from '../components/RobotViewer3D';
import { useStore } from '../store/useStore';
import { Activity, ShieldCheck, Database, Sliders, Play, Square, Video } from 'lucide-react';

export default function ControlTower() {
  const telemetry = useStore((state) => state);
  const updateTelemetry = useStore((state) => state.updateTelemetry);

  useEffect(() => {
    // Initialize High-Frequency Telemetry WebSocket
    const socket = new WebSocket('ws://localhost:8000/ws/telemetry');
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      updateTelemetry(data);
    };
    return () => socket.close();
  }, [updateTelemetry]);

  return (
    <div className="min-h-screen bg-black text-slate-100 font-sans p-6 selection:bg-cyan-500 selection:text-white">
      {/* Header HUD */}
      <header className="flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-black tracking-tighter text-cyan-400">SIGN-VERSE <span className="text-slate-500 font-light">CONTROL TOWER</span></h1>
          <div className="flex items-center gap-4 mt-1 text-xs text-slate-400">
            <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" /> SYSTEM: OPTIMAL</span>
            <span className="flex items-center gap-1"><Video size={12} /> FEED: SAMPLED (10FPS)</span>
            <span className="flex items-center gap-1"><Activity size={12} /> TELEMETRY: LIVE (30FPS)</span>
          </div>
        </div>
        <div className="flex gap-4">
          <button className="px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg hover:bg-slate-800 transition-all flex items-center gap-2 text-sm">
            <Database size={16} /> DATASET EXPORT
          </button>
          <button className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-black font-bold rounded-lg transition-all flex items-center gap-2 text-sm">
            <Play size={16} /> START SIMULATION
          </button>
        </div>
      </header>

      {/* Main Cockpit Grid */}
      <div className="grid grid-cols-12 gap-6 h-[75vh]">
        {/* Left Stats Column */}
        <div className="col-span-3 space-y-6">
          <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 p-6 rounded-2xl">
            <h3 className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-4 flex items-center gap-2">
              <Activity className="text-cyan-400" size={14} /> Intelligence Core
            </h3>
            <div className="space-y-4">
              <div>
                <label className="text-[10px] text-slate-500 uppercase">Current Intent</label>
                <p className="text-2xl font-bold text-white">{telemetry.intent}</p>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 uppercase">Confidence Score</label>
                <div className="h-2 bg-slate-800 rounded-full mt-1 overflow-hidden">
                  <div className="h-full bg-cyan-500 transition-all duration-500" style={{ width: `${telemetry.confidence * 100}%` }} />
                </div>
              </div>
            </div>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 p-6 rounded-2xl">
            <h3 className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-4 flex items-center gap-2">
              <ShieldCheck className="text-emerald-400" size={14} /> Physical Stability
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-sm text-slate-400">ZMP Stability Health</span>
                <span className="text-sm font-mono text-emerald-400">{(telemetry.stabilityHealth * 100).toFixed(1)}%</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 transition-all duration-300" style={{ width: `${telemetry.stabilityHealth * 100}%` }} />
              </div>
            </div>
          </div>
        </div>

        {/* Center 3D Viewer */}
        <div className="col-span-6">
          <RobotViewer3D />
        </div>

        {/* Right Control Column */}
        <div className="col-span-3 space-y-4">
           <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 p-6 rounded-2xl h-full">
            <h3 className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-4 flex items-center gap-2">
              <Sliders className="text-purple-400" size={14} /> Control Presets
            </h3>
            <div className="space-y-2">
              <button className="w-full text-left p-3 rounded-xl bg-slate-800/50 border border-slate-700 hover:border-cyan-500 transition-colors text-sm font-medium">
                Switch to Static Walking
              </button>
              <button className="w-full text-left p-3 rounded-xl bg-slate-800/50 border border-slate-700 hover:border-cyan-500 transition-colors text-sm font-medium">
                Override: Safe Posture
              </button>
              <button className="w-full text-left p-3 rounded-xl bg-red-900/20 border border-red-900/50 hover:bg-red-900/30 transition-colors text-sm font-bold text-red-400 mt-8 flex items-center justify-center gap-2">
                <Square size={14} /> EMERGENCY KILL SWITCH
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
