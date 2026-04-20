"use client";

import React, { useState } from 'react';
import { 
  ActivitySquare, 
  Database, 
  Play, 
  Cpu, 
  LayoutGrid, 
  LineChart as LineChartIcon,
  ChevronRight,
  RefreshCcw,
  BarChart3
} from 'lucide-react';
import { useStore } from '@/store/useStore';
import TrainingChart from '@/components/TrainingChart';
import { apiUrl } from '@/lib/api';

export default function TrainingMonitor() {
  const { trainingMetrics, trainingHistory } = useStore();
  const [detailMode, setDetailMode] = useState(true);
  const [isLaunching, setIsLaunching] = useState(false);
  const [launchMessage, setLaunchMessage] = useState<string | null>(null);

  const launchTraining = async () => {
    setIsLaunching(true);
    setLaunchMessage(null);
    try {
      const res = await fetch(apiUrl('/training/launch?epochs=20'), {
        method: 'POST'
      });
      const data = await res.json();
      setLaunchMessage(data.message || (res.ok ? 'Training launched.' : 'Training launch failed.'));
    } catch (e) {
      setLaunchMessage("Training launch failed.");
      console.error("Training launch failed:", e);
    } finally {
      setIsLaunching(false);
    }
  };

  return (
    <div className="p-8 max-w-[1700px] mx-auto text-on-surface h-[calc(100vh-64px)] flex flex-col gap-8 overflow-hidden">
      {/* Header */}
      <div className="flex justify-between items-start flex-shrink-0">
        <div>
          <h1 className="text-4xl font-space-grotesk font-light uppercase tracking-tighter">
            Training <span className="text-primary font-bold">Monitor</span>
          </h1>
          <p className="font-jetbrains-mono text-[10px] text-neutral-500 mt-2 flex items-center gap-2">
            <Cpu className="w-3 h-3" /> ML PIPELINE TELEMETRY // ACTIVE_LEARNING_RUN_09
          </p>
          {launchMessage && (
            <p className="font-jetbrains-mono text-[10px] text-neutral-400 mt-2">{launchMessage}</p>
          )}
        </div>
        
        <div className="flex gap-4">
           {/* Active Learning Status Indicator */}
           <div className={`px-4 py-2 rounded-xl border flex items-center gap-3 transition-colors ${trainingMetrics.is_training ? 'bg-primary/10 border-primary/30' : 'bg-surface-container-high border-outline-variant/10'}`}>
              <div className={`w-2 h-2 rounded-full ${trainingMetrics.is_training ? 'bg-primary animate-pulse' : 'bg-neutral-600'}`}></div>
              <div>
                <span className="block text-[8px] text-neutral-500 uppercase font-jetbrains-mono tracking-widest">Pipeline State</span>
                <span className={`text-[12px] font-jetbrains-mono font-bold uppercase ${trainingMetrics.is_training ? 'text-primary' : 'text-neutral-400'}`}>
                  {trainingMetrics.is_training ? 'Optimizing Kernel' : 'Awaiting Trigger'}
                </span>
              </div>
           </div>
           
           <div className="bg-surface-container-high px-4 py-2 rounded-xl border border-outline-variant/10 text-right">
              <span className="block text-[9px] text-neutral-500 uppercase font-jetbrains-mono">Current Epoch</span>
              <span className="text-[18px] font-jetbrains-mono text-primary font-bold">{trainingMetrics.epoch}</span>
           </div>
        </div>
      </div>

      <div className="flex-grow grid grid-cols-12 gap-8 overflow-hidden">
        {/* Left Area: Training Curves */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-6 overflow-hidden">
           <div className="flex items-center justify-between px-2">
             <div className="flex items-center gap-2">
               <ActivitySquare className="w-4 h-4 text-primary" />
               <h3 className="font-jetbrains-mono text-[11px] uppercase tracking-[0.2em] text-neutral-400">ML Optimization Curves</h3>
             </div>
             <div className="flex bg-neutral-900 rounded-lg p-1 border border-outline-variant/10">
                <button 
                   onClick={() => setDetailMode(false)}
                   className={`p-1.5 rounded transition-all ${!detailMode ? 'bg-primary/20 text-primary' : 'text-neutral-500'}`}
                >
                   <LayoutGrid className="w-3.5 h-3.5" />
                </button>
                <button 
                   onClick={() => setDetailMode(true)}
                   className={`p-1.5 rounded transition-all ${detailMode ? 'bg-primary/20 text-primary' : 'text-neutral-500'}`}
                >
                   <LineChartIcon className="w-3.5 h-3.5" />
                </button>
             </div>
           </div>
           
           <div className="flex-grow grid grid-rows-2 gap-6 overflow-hidden">
              {/* Training Loss Area */}
              <div className="bg-black/40 rounded-3xl border border-outline-variant/10 p-6 flex flex-col gap-4 shadow-xl shadow-primary/5">
                 <div className="flex justify-between items-center">
                    <span className="text-[10px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest">Cross-Entropy Loss</span>
                    <span className="text-[14px] font-jetbrains-mono text-primary font-bold">{trainingMetrics.loss.toFixed(6)}</span>
                 </div>
                 <div className="flex-grow">
                    <TrainingChart 
                      data={trainingHistory} 
                      dataKey="loss" 
                      color="#00f2ff" 
                      name="Loss" 
                      detailMode={detailMode} 
                    />
                 </div>
              </div>

              {/* Accuracy Area */}
              <div className="bg-black/40 rounded-3xl border border-outline-variant/10 p-6 flex flex-col gap-4 shadow-xl shadow-primary/5">
                 <div className="flex justify-between items-center">
                    <span className="text-[10px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest">Classification Accuracy</span>
                    <span className="text-[14px] font-jetbrains-mono text-tertiary font-bold">{(trainingMetrics.accuracy * 100).toFixed(2)}%</span>
                 </div>
                 <div className="flex-grow">
                    <TrainingChart 
                      data={trainingHistory} 
                      dataKey="accuracy" 
                      color="#ffffff" 
                      name="Accuracy" 
                      detailMode={detailMode} 
                    />
                 </div>
              </div>
           </div>
        </div>

        {/* Right Area: Sidebar Controls */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-6 overflow-hidden">
           
           <div className="flex items-center gap-2 px-2">
              <BarChart3 className="w-4 h-4 text-primary" />
              <h3 className="font-jetbrains-mono text-[11px] uppercase tracking-[0.2em] text-neutral-400">Pipeline Control</h3>
           </div>

           <div className="flex-grow bg-surface-container rounded-[2rem] border border-outline-variant/10 p-8 flex flex-col gap-8 shadow-2xl overflow-y-auto custom-scrollbar">
              
              {/* Manual Control */}
              <div className="bg-black/20 p-6 rounded-3xl border border-outline-variant/5">
                 <h4 className="text-[10px] font-jetbrains-mono text-neutral-500 uppercase mb-4 tracking-widest">Manual active Learning</h4>
                 <button 
                   onClick={launchTraining}
                   disabled={isLaunching || trainingMetrics.is_training}
                   className={`w-full py-5 rounded-2xl font-space-grotesk font-bold uppercase text-[12px] flex items-center justify-center gap-3 transition-all ${trainingMetrics.is_training ? 'bg-neutral-800 text-neutral-500 cursor-not-allowed' : 'bg-primary text-black hover:bg-primary-light shadow-lg shadow-primary/20 hover:scale-[1.02]'}`}
                 >
                   {isLaunching || trainingMetrics.is_training ? (
                      <RefreshCcw className="w-4 h-4 animate-spin" />
                   ) : (
                      <Play className="w-4 h-4 fill-current" />
                   )}
                   {trainingMetrics.is_training ? 'Training Hot...' : 'Trigger Learning Sweep'}
                 </button>
                 <p className="text-[9px] font-jetbrains-mono text-neutral-600 mt-4 leading-relaxed">
                    Triggers a 20-epoch optimization pass on the current Demonstration Buffer.
                 </p>
              </div>

              {/* Dataset Status */}
              <div className="space-y-6">
                 <div>
                    <div className="flex justify-between items-center mb-3">
                       <div className="flex items-center gap-2">
                          <Database className="w-3.5 h-3.5 text-primary" />
                          <span className="text-[10px] font-jetbrains-mono text-neutral-300 uppercase">Buffer Saturation</span>
                       </div>
                       <span className="text-[10px] font-jetbrains-mono text-white">{trainingMetrics.dataset_size} / 5000</span>
                    </div>
                    <div className="w-full h-1.5 bg-neutral-900 rounded-full overflow-hidden">
                       <div 
                         className="h-full bg-primary shadow-[0_0_8px_cyan] transition-all duration-500" 
                         style={{ width: `${Math.min(100, (trainingMetrics.dataset_size / 5000) * 100)}%` }}
                       />
                    </div>
                 </div>

                 <div className="grid grid-cols-2 gap-4">
                    <div className="bg-black/30 p-4 rounded-2xl border border-outline-variant/5">
                       <span className="block text-[8px] text-neutral-500 uppercase mb-1">Architecture</span>
                       <span className="text-[12px] font-bold font-jetbrains-mono">IntentTransformer_v2</span>
                    </div>
                    <div className="bg-black/30 p-4 rounded-2xl border border-outline-variant/5">
                       <span className="block text-[8px] text-neutral-500 uppercase mb-1">Optimizer</span>
                       <span className="text-[12px] font-bold font-jetbrains-mono">AdamW_Adaptive</span>
                    </div>
                 </div>
              </div>

              <div className="flex-grow"></div>

              {/* Status Log */}
              <div className="space-y-3">
                 <h4 className="text-[9px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest border-b border-outline-variant/10 pb-2">Status Log</h4>
                 <div className="h-40 overflow-y-auto space-y-2 pr-2 text-[10px] font-jetbrains-mono">
                    <div className="flex gap-3 text-neutral-500">
                       <span className="text-primary">[17:15:02]</span> SYSTEM_READY: Waiting for signal.
                    </div>
                    <div className="flex gap-3 text-neutral-500">
                       <span className="text-primary">[17:15:10]</span> BUFFER_UPDATE: Recieved 42 samples.
                    </div>
                    {trainingMetrics.is_training && (
                       <div className="flex gap-3 text-primary animate-pulse">
                          <span>[{new Date().toLocaleTimeString()}]</span> KERNEL_OPTI: Running epoch {trainingMetrics.epoch}...
                       </div>
                    )}
                 </div>
              </div>
              
              <button className="w-full mt-auto flex items-center justify-between px-6 py-4 bg-neutral-900 border border-outline-variant/20 rounded-2xl text-[10px] font-jetbrains-mono uppercase hover:bg-white/5 transition-all">
                 Full Hyperparameter Suite <ChevronRight className="w-3.5 h-3.5" />
              </button>
           </div>
        </div>
      </div>
    </div>
  );
}
