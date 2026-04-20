"use client";

import React, { useMemo } from 'react';
import { Activity, LayoutGrid, ScatterChart } from 'lucide-react';

interface LatentSpaceViewerProps {
  embedding: number[]; // 64-dim vector
  viewMode?: 'heatmap' | 'cluster';
}

/**
 * Hybrid Latent Space Viewer.
 * Visualizes high-dimensional hand embeddings as a 2D Heatmap or a Simulated Cluster Map.
 */
export default function LatentSpaceViewer({ embedding, viewMode = 'heatmap' }: LatentSpaceViewerProps) {
  
  // Normalize embedding values for visualization (-1 to 1 range typically)
  const normalizedData = useMemo(() => {
    if (!embedding || embedding.length === 0) return Array(64).fill(0);
    return embedding.map(v => Math.max(0, Math.min(1, (v + 1) / 2)));
  }, [embedding]);

  return (
    <div className="w-full h-full flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
           <Activity className="w-4 h-4 text-primary" />
           <span className="font-jetbrains-mono text-[10px] uppercase tracking-wider text-neutral-400">Latent Signal Analysis</span>
        </div>
        <div className="bg-neutral-900 rounded-lg p-1 flex gap-1 border border-outline-variant/10">
           {/* Tab Logic handled by parent or internal state if needed */}
           <div className={`p-1.5 rounded transition-all ${viewMode === 'heatmap' ? 'bg-primary/20 text-primary' : 'text-neutral-500'}`}>
              <LayoutGrid className="w-3.5 h-3.5" />
           </div>
           <div className={`p-1.5 rounded transition-all ${viewMode === 'cluster' ? 'bg-primary/20 text-primary' : 'text-neutral-500'}`}>
              <ScatterChart className="w-3.5 h-3.5" />
           </div>
        </div>
      </div>

      <div className="flex-grow bg-neutral-950 rounded-xl border border-outline-variant/10 p-4 flex items-center justify-center relative overflow-hidden">
        {viewMode === 'heatmap' ? (
          <div className="grid grid-cols-8 grid-rows-8 gap-1 w-full aspect-square max-w-[400px]">
            {normalizedData.map((val, i) => (
              <div 
                key={i} 
                className="rounded-sm transition-all duration-300"
                style={{ 
                  backgroundColor: `rgba(0, 242, 255, ${0.1 + val * 0.9})`,
                  boxShadow: val > 0.8 ? '0 0 8px rgba(0, 242, 255, 0.4)' : 'none'
                }}
              />
            ))}
          </div>
        ) : (
          <div className="relative w-full h-full max-w-[400px] aspect-square">
             {/* Simulated Cluster Map - Projects 64D to 2D using simple sum/diff for animation */}
             <div 
               className="absolute w-4 h-4 rounded-full bg-primary shadow-[0_0_20px_rgba(0,242,255,0.8)] transition-all duration-500 ease-out"
               style={{ 
                 left: `${20 + (normalizedData.slice(0, 32).reduce((a, b) => a + b, 0) / 32) * 60}%`,
                 top: `${20 + (normalizedData.slice(32).reduce((a, b) => a + b, 0) / 32) * 60}%`
               }}
             />
             {/* Dynamic Cluster Labels */}
             <div className="absolute top-4 left-4 text-[8px] font-jetbrains-mono text-neutral-600 uppercase">Cluster_ASL_Alpha</div>
             <div className="absolute bottom-4 right-4 text-[8px] font-jetbrains-mono text-neutral-600 uppercase">Cluster_Robotic_Grip</div>
             
             {/* Reference grid */}
             <div className="absolute inset-0 border border-primary/5 grid grid-cols-4 grid-rows-4 pointer-events-none">
                {Array(16).fill(0).map((_, i) => <div key={i} className="border border-primary/5" />)}
             </div>
          </div>
        )}

        {/* HUD Overlay */}
        <div className="absolute bottom-2 right-4 flex gap-4">
           <div className="text-right">
              <span className="block text-[8px] text-neutral-500 uppercase">Dimensions</span>
              <span className="text-[10px] font-jetbrains-mono text-primary font-bold">64xFLOAT32</span>
           </div>
           <div className="text-right">
              <span className="block text-[8px] text-neutral-500 uppercase">Model_Ref</span>
              <span className="text-[10px] font-jetbrains-mono text-tertiary font-bold">TIE_V2_LATENT</span>
           </div>
        </div>
      </div>
    </div>
  );
}
