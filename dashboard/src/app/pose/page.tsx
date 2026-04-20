"use client";

import React, { useState } from 'react';
import { Focus, Fingerprint, Box, Cpu, ChevronRight, Layers, RefreshCcw } from 'lucide-react';
import { useStore } from '@/store/useStore';
import HandRenderer from '@/components/HandRenderer';
import LatentSpaceViewer from '@/components/LatentSpaceViewer';
import { apiUrl } from '@/lib/api';

export default function PoseLab() {
  const { handJoints, handEmbedding, confidence, trainingMetrics } = useStore();
  const [viewMode, setViewMode] = useState<'heatmap' | 'cluster'>('heatmap');
  const [isLaunching, setIsLaunching] = useState(false);
  const [trainingMessage, setTrainingMessage] = useState<string | null>(null);

  const launchTraining = async () => {
    setIsLaunching(true);
    setTrainingMessage(null);
    try {
      const res = await fetch(apiUrl('/training/launch?epochs=20'), { method: 'POST' });
      const data = await res.json();
      setTrainingMessage(data.message || (res.ok ? 'Training launched.' : 'Training launch failed.'));
    } catch (e) {
      setTrainingMessage("Training launch failed.");
      console.error(e);
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
            Pose & Gesture <span className="text-primary font-bold">Lab</span>
          </h1>
          <p className="font-jetbrains-mono text-[10px] text-neutral-500 mt-2 flex items-center gap-2">
            <Cpu className="w-3 h-3" /> NEURAL EMBEDDING PIPELINE // V.2.0-ALFA
          </p>
          {trainingMessage && (
            <p className="font-jetbrains-mono text-[10px] text-neutral-400 mt-2">{trainingMessage}</p>
          )}
        </div>
        
        <div className="flex gap-4">
           <div className="bg-surface-container-high px-4 py-2 rounded-xl border border-outline-variant/10 text-right">
              <span className="block text-[9px] text-neutral-500 uppercase font-jetbrains-mono">Inference Confidence</span>
              <span className="text-[18px] font-jetbrains-mono text-primary font-bold">{(confidence * 100).toFixed(1)}%</span>
           </div>
        </div>
      </div>
      
      <div className="flex-grow grid grid-cols-12 gap-8 overflow-hidden">
        {/* Left: 3D Visualization */}
        <div className="col-span-12 lg:col-span-5 flex flex-col gap-4 overflow-hidden">
           <div className="flex items-center justify-between px-2">
             <div className="flex items-center gap-2">
               <Box className="w-4 h-4 text-primary" />
               <h3 className="font-jetbrains-mono text-[11px] uppercase tracking-[0.2em] text-neutral-400">Kinematic Hand Mesh</h3>
             </div>
             <span className="text-[10px] text-primary font-jetbrains-mono bg-primary/10 px-2 py-0.5 rounded">LIVE_STREAM</span>
           </div>
           
           <div className="flex-grow bg-black rounded-3xl border border-outline-variant/10 relative overflow-hidden flex items-center justify-center p-12 group shadow-2xl shadow-primary/5">
              {handJoints.length > 0 ? (
                <HandRenderer joints={handJoints} color="#00f2ff" />
              ) : (
                <div className="flex flex-col items-center gap-4 opacity-20">
                   <Focus className="w-16 h-16 text-neutral-500" />
                   <span className="font-jetbrains-mono text-neutral-500 text-[10px] uppercase">Awaiting Hand Discovery</span>
                </div>
              )}
              
              {/* Overlay HUD */}
              <div className="absolute top-6 left-6 flex flex-col gap-2">
                 <div className="w-24 h-1 bg-neutral-900 rounded-full overflow-hidden">
                    <div className="h-full bg-primary animate-pulse w-2/3"></div>
                 </div>
                 <span className="text-[8px] font-jetbrains-mono text-primary/50 uppercase">Synaptic_Link_Active</span>
              </div>
           </div>
        </div>

        {/* Center: Latent Space Engine */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-4">
           <div className="flex items-center justify-between px-2">
             <div className="flex items-center gap-2">
               <Layers className="w-4 h-4 text-primary" />
               <h3 className="font-jetbrains-mono text-[11px] uppercase tracking-[0.2em] text-neutral-400">Latent Space Viewer</h3>
             </div>
             <div className="flex gap-1">
                <button 
                  onClick={() => setViewMode('heatmap')}
                  className={`px-2 py-1 rounded text-[9px] font-bold uppercase ${viewMode === 'heatmap' ? 'bg-primary text-black' : 'text-neutral-500 hover:text-neutral-300'}`}
                >
                  Heatmap
                </button>
                <button 
                  onClick={() => setViewMode('cluster')}
                  className={`px-2 py-1 rounded text-[9px] font-bold uppercase ${viewMode === 'cluster' ? 'bg-primary text-black' : 'text-neutral-500 hover:text-neutral-300'}`}
                >
                  Cluster
                </button>
             </div>
           </div>
           
           <div className="flex-grow bg-surface-container rounded-3xl border border-outline-variant/10 p-6 shadow-xl">
              <LatentSpaceViewer embedding={handEmbedding} viewMode={viewMode} />
           </div>
        </div>

        {/* Right: Gesture Intelligence */}
        <div className="col-span-12 lg:col-span-3 flex flex-col gap-4">
           <h3 className="font-jetbrains-mono text-[11px] uppercase tracking-[0.2em] text-neutral-400 px-2">Gesture Intelligence</h3>
           
           <div className="flex-grow space-y-4">
              <div className="bg-surface-container rounded-2xl p-5 border border-outline-variant/10 hover:border-primary/30 transition-all cursor-crosshair group">
                 <div className="flex items-center justify-between mb-4">
                    <Fingerprint className="w-5 h-5 text-primary group-hover:scale-110 transition-transform" />
                    <span className="text-[10px] font-jetbrains-mono text-neutral-500 uppercase">Top Match</span>
                 </div>
                 <div className="text-2xl font-space-grotesk font-bold uppercase tracking-tight text-white mb-1">
                    {handJoints.length > 0 ? 'Fist_Pinch' : 'NO_SIGNAL'}
                 </div>
                 <div className="flex items-center justify-between">
                    <span className="text-[10px] font-jetbrains-mono text-primary uppercase">Similarity</span>
                    <span className="text-[10px] font-jetbrains-mono text-neutral-400">0.942</span>
                 </div>
              </div>

              {/* Library Preview */}
              <div className="bg-surface-container rounded-2xl p-5 border border-outline-variant/10 flex-grow">
                 <h4 className="text-[10px] font-jetbrains-mono text-neutral-500 uppercase mb-4">Discovery Stream</h4>
                 <div className="space-y-3">
                   {[
                     { name: 'Grip_Closed', conf: 0.92, active: true },
                     { name: 'Index_Point', conf: 0.41, active: false },
                     { name: 'Palm_Open', conf: 0.12, active: false },
                   ].map((item, i) => (
                     <div key={i} className={`flex items-center justify-between p-2 rounded-lg border ${item.active ? 'bg-primary/5 border-primary/20' : 'border-transparent'}`}>
                        <div className="flex items-center gap-2">
                           <div className={`w-1.5 h-1.5 rounded-full ${item.active ? 'bg-primary' : 'bg-neutral-800'}`}></div>
                           <span className={`text-[11px] font-jetbrains-mono ${item.active ? 'text-white' : 'text-neutral-600'}`}>{item.name}</span>
                        </div>
                        <span className="text-[10px] font-jetbrains-mono text-neutral-500">{item.conf}</span>
                     </div>
                   ))}
                 </div>
                 
                 <button 
                    onClick={launchTraining}
                    disabled={isLaunching || trainingMetrics.is_training}
                    className={`w-full mt-6 flex items-center justify-center gap-2 py-3 border rounded-xl text-[10px] font-jetbrains-mono uppercase transition-all ${trainingMetrics.is_training ? 'bg-primary/20 border-primary/40 text-primary' : 'bg-neutral-900 border-outline-variant/20 hover:bg-neutral-800'}`}
                 >
                    {isLaunching || trainingMetrics.is_training ? <RefreshCcw className="w-3 h-3 animate-spin" /> : <ChevronRight className="w-3 h-3" />}
                    {trainingMetrics.is_training ? 'Training...' : 'Initialize Training'}
                 </button>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
