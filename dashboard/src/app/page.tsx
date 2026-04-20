"use client";

import Image from 'next/image';
import React, { useEffect, useState } from 'react';
import { useStore } from '@/store/useStore';
import { apiUrl } from '@/lib/api';
import { 
  CloudUpload, 
  RefreshCw, 
  ShieldAlert, 
  Cpu, 
  Zap, 
  Activity, 
  Database,
  Play
} from 'lucide-react';

/**
 * High-Precision System Clock Hook
 * Returns HH:MM:SS.mmm
 */
function useClock() {
  const [time, setTime] = useState("");

  useEffect(() => {
    const update = () => {
      const now = new Date();
      const h = now.getHours().toString().padStart(2, '0');
      const m = now.getMinutes().toString().padStart(2, '0');
      const s = now.getSeconds().toString().padStart(2, '0');
      const ms = now.getMilliseconds().toString().padStart(3, '0');
      setTime(`${h}:${m}:${s}.${ms}`);
    };
    update();
    const interval = setInterval(update, 100);
    return () => clearInterval(interval);
  }, []);

  return time;
}

export default function CommandCenter() {
  const clock = useClock();
  const { 
    intent, 
    confidence, 
    stabilityHealth, 
    rlLatency, 
    controlLatency, 
    cpuUsage,
    robotVelocity,
    totalPowerDrain,
    isConnected
  } = useStore();

  const [isCalibrating, setIsCalibrating] = useState(false);
  const [activeModel, setActiveModel] = useState("v2.4.1 (Stable)");
  const [systemMessage, setSystemMessage] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleCalibrate = async () => {
    setIsCalibrating(true);
    try {
      const res = await fetch(apiUrl('/control/calibrate'), { method: 'POST' });
      const data = await res.json();
      setSystemMessage(data.message || "Global system calibrated.");
    } catch (e) {
      setSystemMessage("Calibration failed. Verify backend status.");
      console.error("Calibration error:", e);
    } finally {
      setIsCalibrating(false);
    }
  };

  const loadExperimentModel = async (version: string) => {
    const weightsMap: Record<string, string> = {
      "v2.4.1": "models/tie_v2/checkpoints/latest.pt",
      "v2.5.0": "models/tie_v2/checkpoints/experimental.pt"
    };
    
    if (weightsMap[version]) {
        try {
            const res = await fetch(apiUrl(`/intelligence/load_model?path=${weightsMap[version]}`), { method: 'POST' });
            if (!res.ok) {
              throw new Error(version);
            }
            setActiveModel(`${version} (Active)`);
            setSystemMessage(`Loaded model ${version}.`);
        } catch (e) {
            setSystemMessage(`Failed to load model ${version}.`);
            console.error("Model load error:", e);
        }
    }
  };

  return (
    <div className="p-8 max-w-[1700px] mx-auto text-on-surface h-[calc(100vh-64px)] flex flex-col gap-8 overflow-hidden">
      {/* Page Header */}
      <div className="flex justify-between items-end flex-shrink-0">
        <div>
          <h1 className="text-4xl font-space-grotesk font-light uppercase tracking-tighter">
            Command <span className="text-primary font-bold">Center</span>
          </h1>
          <p className="font-jetbrains-mono text-[10px] text-neutral-500 mt-2 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
            {`SYSTEM_CLOCK: ${clock} | SYNC_STATUS: ${isConnected ? 'OPTIMAL' : 'OFFLINE'}`}
          </p>
          {systemMessage && (
            <p className="font-jetbrains-mono text-[10px] text-neutral-400 mt-2">{systemMessage}</p>
          )}
        </div>
        
        <div className="flex gap-4">
          <div className="bg-surface-container-high px-6 py-3 rounded-2xl border border-primary/20 shadow-lg shadow-primary/5">
            <p className="text-[9px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest mb-1">RL Latency</p>
            <p className="text-2xl font-jetbrains-mono text-primary font-bold">{rlLatency.toFixed(1)}<span className="text-xs ml-1 opacity-50">ms</span></p>
          </div>
          <div className="bg-surface-container-high px-6 py-3 rounded-2xl border border-tertiary/20 shadow-lg shadow-tertiary/5">
            <p className="text-[9px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest mb-1">Stability</p>
            <p className="text-2xl font-jetbrains-mono text-tertiary font-bold">{(stabilityHealth * 100).toFixed(2)}<span className="text-xs ml-1 opacity-50">%</span></p>
          </div>
        </div>
      </div>

      <div className="flex-grow grid grid-cols-12 gap-8 overflow-hidden">
        
        {/* Left Area: Main Telemetry & Experiments */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-8 overflow-hidden">
           
           {/* Hardware Cluster Telemetry */}
           <div className="bg-surface-container rounded-[2rem] overflow-hidden border border-outline-variant/10 shadow-2xl flex flex-col h-1/2">
              <div className="flex items-center justify-between px-8 py-6 border-b border-outline-variant/5 bg-black/20">
                <div className="flex items-center gap-3">
                   <Zap className="w-4 h-4 text-primary" />
                   <h3 className="font-space-grotesk font-bold text-xs uppercase tracking-[0.2em] text-neutral-400">Hardware Cluster Telemetry</h3>
                </div>
                <div className="flex gap-8">
                  <div className="flex flex-col items-end">
                    <span className="text-[8px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest">CPU Saturation</span>
                    <span className="text-sm font-jetbrains-mono text-primary font-bold">{cpuUsage.toFixed(1)}%</span>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-[8px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest">Power Drain</span>
                    <span className="text-sm font-jetbrains-mono text-error font-bold">{totalPowerDrain.toFixed(1)}W</span>
                  </div>
                </div>
              </div>
              
              <div className="flex-grow p-8 flex items-end gap-1.5 relative overflow-hidden bg-[radial-gradient(circle_at_50%_120%,_rgba(0,242,255,0.05),_transparent)]">
                 {Array.from({length: 40}).map((_, i) => (
                    <div key={i} className="flex-1 bg-primary/10 rounded-full relative group overflow-hidden transition-all duration-300" 
                         style={{ height: mounted ? `${Math.max(15, Math.min(100, cpuUsage + (Math.sin(i * 0.4 + cpuUsage * 0.1) * 30)))}%` : '15%' }}>
                      <div className="absolute bottom-0 w-full bg-primary h-[60%] blur-[1px] group-hover:h-full transition-all duration-300"></div>
                    </div>
                 ))}
                 <div className="absolute inset-x-8 bottom-16 h-[1px] bg-primary/20 shadow-[0_0_20px_cyan]"></div>
              </div>
           </div>

           {/* Recent Experiments (Interactive) */}
           <div className="flex flex-col gap-4 overflow-hidden">
              <div className="flex items-center gap-2 px-2">
                 <Database className="w-4 h-4 text-primary" />
                 <h3 className="font-space-grotesk font-bold text-xs uppercase tracking-[0.2em] text-neutral-400">Live Experiment Deployment</h3>
              </div>
              
              <div className="grid grid-cols-2 gap-6 overflow-hidden">
                 <div 
                   onClick={() => loadExperimentModel("v2.4.1")}
                   className="group relative cursor-pointer aspect-video rounded-3xl overflow-hidden border border-outline-variant/10 hover:border-primary/40 transition-all shadow-xl"
                 >
                    <Image alt="Gesture Analysis" className="object-cover grayscale opacity-50 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-700 scale-105 group-hover:scale-110" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCUiqJYgPnUHIqBuMVY3MejnLq-pIO8mrf5vWJJlPdzYC2ox8Equ7akSyhSVPq_q5fGCgjZhchw40Oiq7V3icVKSVXhBbAPcuBE2U3b8JtNDvZv1MVTrpuIRcf5RJXe1iptQIOy15FCRpZbsr-c8yOVtMNkNcpvoszwsXuIj6KudE7AdS-izZzZlvz-pG57pt8I-jVUZnCoJK7DQR7_O_bX_elCruUHGhfdcua5ji18aitbtjr9MIu9K51rUOE1rp8WwKyh_aXEFWs" fill sizes="(max-width: 1024px) 100vw, 50vw" />
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent"></div>
                    <div className="absolute bottom-6 left-6 flex items-center gap-4">
                       <div className="p-3 bg-primary rounded-2xl shadow-lg group-hover:scale-110 transition-transform">
                          <Play className="w-4 h-4 text-black fill-current" />
                       </div>
                       <div>
                          <p className="text-[10px] font-jetbrains-mono text-primary uppercase font-bold tracking-widest">{activeModel === "v2.4.1 (Active)" ? "DEPLOYED" : "v2.4.1"}</p>
                          <h4 className="text-lg font-space-grotesk font-bold text-white leading-tight">Gesture_Sovereign_Alpha</h4>
                       </div>
                    </div>
                 </div>

                 <div 
                   onClick={() => loadExperimentModel("v2.5.0")}
                   className="group relative cursor-pointer aspect-video rounded-3xl overflow-hidden border border-outline-variant/10 hover:border-tertiary/40 transition-all shadow-xl"
                 >
                    <Image alt="Kinematic Analysis" className="object-cover grayscale opacity-50 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-700 scale-105 group-hover:scale-110" src="https://lh3.googleusercontent.com/aida-public/AB6AXuA0Z3V6I1L9qQzM2Hk7C3_C_f_N2vX0P_k6X_g6h_W8Z_z6Q_vV_I_f_W_x_w_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_u_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v_v" fill sizes="(max-width: 1024px) 100vw, 50vw" />
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent"></div>
                    <div className="absolute bottom-6 left-6 flex items-center gap-4">
                       <div className="p-3 bg-tertiary rounded-2xl shadow-lg group-hover:scale-110 transition-transform">
                          <Activity className="w-4 h-4 text-black" />
                       </div>
                       <div>
                          <p className="text-[10px] font-jetbrains-mono text-tertiary uppercase font-bold tracking-widest">v2.5.0</p>
                          <h4 className="text-lg font-space-grotesk font-bold text-white leading-tight">Complex_Terrain_Adaptation</h4>
                       </div>
                    </div>
                 </div>
              </div>
           </div>
        </div>

        {/* Right Area: Encodings & System Actions */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-8 overflow-hidden">
           
           {/* Live Encodings Status */}
           <div className="bg-surface-container rounded-[2rem] border border-outline-variant/10 p-8 flex flex-col gap-6 shadow-xl">
              <h3 className="font-space-grotesk font-bold text-xs uppercase tracking-widest text-neutral-500 mb-2">Live Encodings</h3>
              
              <div className="p-6 bg-black/40 rounded-3xl border-l-[6px] border-primary group transition-all cursor-pointer">
                <div className="flex justify-between items-start mb-4">
                  <span className="text-[10px] font-jetbrains-mono text-primary font-bold tracking-widest">HUMAN_INTENT</span>
                  <span className={`text-[9px] font-jetbrains-mono px-3 py-1 rounded-full ${confidence > 0.1 ? 'bg-primary/20 text-primary animate-pulse' : 'bg-neutral-800 text-neutral-500'}`}>
                    {confidence > 0.1 ? 'ACTIVE' : 'IDLE'}
                  </span>
                </div>
                <h4 className="text-2xl font-space-grotesk font-bold uppercase mb-2 group-hover:text-primary transition-colors">{intent}</h4>
                <div className="w-full bg-neutral-900 h-2 rounded-full overflow-hidden mt-4">
                  <div className="bg-primary h-full transition-all duration-500 shadow-[0_0_12px_cyan]" style={{width: `${confidence * 100}%`}}></div>
                </div>
                <div className="flex justify-between mt-3 text-neutral-500">
                  <span className="text-[9px] font-jetbrains-mono uppercase">CONFIDENCE_VECTOR</span>
                  <span className="text-[11px] font-jetbrains-mono text-white">{(confidence * 100).toFixed(1)}%</span>
                </div>
              </div>

              <div className="p-6 bg-black/40 rounded-3xl border-l-[6px] border-tertiary group transition-all">
                <div className="flex justify-between items-start mb-4">
                  <span className="text-[10px] font-jetbrains-mono text-tertiary font-bold tracking-widest">KINEMATIC_CTRL</span>
                  <span className="text-[9px] font-jetbrains-mono px-3 py-1 bg-tertiary/20 text-tertiary rounded-full uppercase">STABLE</span>
                </div>
                <h4 className="text-lg font-space-grotesk font-bold uppercase mb-4">WBC_Balance_Loop</h4>
                <div className="flex justify-between items-end">
                   <div>
                      <span className="block text-[8px] text-neutral-500 uppercase font-jetbrains-mono tracking-widest">Latency</span>
                      <span className="text-[14px] font-jetbrains-mono text-white font-bold">{controlLatency.toFixed(2)}ms</span>
                   </div>
                   <div className="text-right">
                      <span className="block text-[8px] text-neutral-500 uppercase font-jetbrains-mono tracking-widest">Hz</span>
                      <span className="text-[14px] font-jetbrains-mono text-white font-bold">400.0</span>
                   </div>
                </div>
              </div>
           </div>

           {/* Quick Actions Card */}
           <div className="bg-surface-container rounded-[2rem] border border-outline-variant/10 p-8 flex flex-col gap-6 shadow-xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                 <Cpu className="w-24 h-24" />
              </div>

              <h3 className="font-space-grotesk font-bold text-xs uppercase tracking-widest text-neutral-500">System Quick-Actions</h3>
              <div className="grid grid-cols-2 gap-4">
                <button 
                  onClick={handleCalibrate}
                  disabled={isCalibrating}
                  className={`flex flex-col items-center justify-center gap-3 p-6 rounded-3xl border border-outline-variant/10 transition-all ${isCalibrating ? 'bg-primary/20 border-primary cursor-wait' : 'bg-surface-container-high hover:border-primary/50 hover:bg-primary/5 active:scale-95'}`}
                >
                  <RefreshCw className={`w-6 h-6 ${isCalibrating ? 'text-primary animate-spin' : 'text-neutral-500'}`} />
                  <span className={`text-[9px] font-jetbrains-mono uppercase font-bold ${isCalibrating ? 'text-primary' : 'text-neutral-400'}`}>Calibrate</span>
                </button>
                <button className="flex flex-col items-center justify-center gap-3 p-6 bg-surface-container-high rounded-3xl border border-outline-variant/10 hover:border-primary/50 hover:bg-primary/5 transition-all active:scale-95 group/btn">
                  <CloudUpload className="w-6 h-6 text-neutral-500 group-hover/btn:text-primary transition-colors" />
                  <span className="text-[9px] font-jetbrains-mono text-neutral-400 uppercase font-bold group-hover/btn:text-primary transition-colors">Push Logs</span>
                </button>
              </div>
              
              <div className="mt-4 p-5 bg-error-container/5 border border-error/20 rounded-3xl backdrop-blur-sm">
                <div className="flex items-center gap-3 mb-3">
                  <ShieldAlert className="w-4 h-4 text-error" />
                  <span className="text-[10px] font-bold text-error uppercase tracking-widest">Security Alert</span>
                </div>
                <p className="text-[9px] text-neutral-400 leading-relaxed font-jetbrains-mono">
                  Continuous tracking active. Velocity Vector [ {robotVelocity[0].toFixed(2)}, {robotVelocity[1].toFixed(2)}, {robotVelocity[2].toFixed(2)} ] requires continuous monitoring.
                </p>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
