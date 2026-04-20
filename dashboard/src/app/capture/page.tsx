"use client";

import Image from 'next/image';
import React, { useState, useEffect } from 'react';
import { 
  Camera, 
  Settings, 
  Database,
  Sliders, 
  PlusCircle, 
  Crosshair, 
  BarChart, 
  ShieldAlert, 
  Search, 
  Image as ImageIcon,
  Upload,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Monitor
} from 'lucide-react';
import { useStore } from '@/store/useStore';
import { apiUrl } from '@/lib/api';

interface YouTubeResult {
  title: string;
  url: string;
  thumbnail: string;
  duration?: number;
}

interface HardwareCamera {
  index: number;
  name: string;
}

export default function CaptureStudio() {
  const { fps, skeletonVersion, isConnected } = useStore();
  
  // State: Search
  const [youtubeQuery, setYoutubeQuery] = useState('');
  const [searchResults, setSearchResults] = useState<YouTubeResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [captureError, setCaptureError] = useState<string | null>(null);
  
  // State: Hardware
  const [hardwareCameras, setHardwareCameras] = useState<HardwareCamera[]>([]);
  const [customIndex, setCustomIndex] = useState('0');
  const [isScanning, setIsScanning] = useState(false);

  // State: Global Ingestion
  const [activeSource, setActiveSource] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [showOverlay, setShowOverlay] = useState(true);

  const scanHardware = async () => {
    setIsScanning(true);
    setCaptureError(null);
    try {
      const res = await fetch(apiUrl("/hardware/cameras"));
      const data = await res.json();
      setHardwareCameras(data.cameras || []);
    } catch (e) {
      setCaptureError("Hardware scan failed. Check camera permissions and backend connectivity.");
      console.error("Hardware scan error:", e);
    }
    setIsScanning(false);
  };

  useEffect(() => {
    scanHardware();
  }, []);

  const startIngestion = async (uri: string, type: string) => {
    if (!uri && type !== "camera") return;
    setCaptureError(null);
    try {
      const res = await fetch(apiUrl("/ingest/start"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            source_uri: uri || customIndex, 
            source_type: type 
        })
      });
      const data = await res.json();
      if (res.ok) {
        setActiveSource(`${type.toUpperCase()}: ${uri || customIndex}`);
        setSearchError(null);
      } else {
        setActiveSource(null);
        setCaptureError(data.detail || `Unable to start ${type} ingestion.`);
      }
    } catch (e) {
      setActiveSource(null);
      setCaptureError(`Unable to start ${type} ingestion. Verify backend and source availability.`);
      console.error(e);
    }
  };

  const handleSearch = async () => {
    if (!youtubeQuery) return;
    setIsSearching(true);
    setSearchError(null);
    try {
      const res = await fetch(apiUrl(`/ingest/search?query=${encodeURIComponent(youtubeQuery)}`), { method: "GET" });
      const data = await res.json();
      if (data.status === "error") {
          setSearchError(data.message);
          setSearchResults([]);
      } else {
          setSearchResults(data.results || []);
      }
    } catch (e) {
      setSearchError("Backend Connectivity Lost. Verify port 8000.");
      console.error(e);
    }
    setIsSearching(false);
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const res = await fetch(apiUrl("/ingest/upload"), { method: "POST", body: formData });
      const data = await res.json();
      if (data.local_path) {
        await startIngestion(data.local_path, "image");
      } else {
        setCaptureError(data.detail || "Image upload failed.");
      }
    } catch (e) {
      setCaptureError("Image upload failed. Verify backend storage access.");
      console.error(e);
    }
  };

  const toggleRecording = async () => {
    try {
      const res = await fetch(apiUrl("/api/v1/control/capture/toggle"), { method: "POST" });
      const data = await res.json();
      setIsRecording(data.is_recording);
    } catch (e) { console.error(e); }
  };

  const toggleOverlay = async () => {
    try {
      const res = await fetch(apiUrl("/api/v1/control/annotations/toggle"), { method: "POST" });
      const data = await res.json();
      setShowOverlay(data.show_annotations);
    } catch (e) { console.error(e); }
  };

  return (
    <div className="h-[calc(100vh-64px)] w-full flex bg-surface-container-lowest text-on-surface overflow-hidden">
      
      {/* Sidebar: Universal Hardware Hub */}
      <div className="w-[380px] flex-shrink-0 bg-surface-container-low border-r border-outline-variant/10 p-8 flex flex-col gap-8 overflow-y-auto custom-scrollbar">
        
        {/* Hardware Discovery Section */}
        <div>
          <div className="flex items-center justify-between mb-6">
             <h3 className="font-space-grotesk text-[10px] font-bold text-neutral-500 uppercase tracking-[0.3em]">Hardware Discovery</h3>
             <button 
               onClick={scanHardware}
               disabled={isScanning}
               className="p-2 hover:bg-primary/10 rounded-lg transition-all group"
             >
                <RefreshCw className={`w-3.5 h-3.5 ${isScanning ? 'animate-spin text-primary' : 'text-neutral-500Group-hover:text-primary'}`} />
             </button>
          </div>
          
          <div className="space-y-4">
             {hardwareCameras.map((cam) => (
                <div key={cam.index} className="flex items-center justify-between p-4 bg-surface-container-high rounded-2xl border border-outline-variant/10 group hover:border-primary/40 transition-all">
                   <div className="flex items-center gap-3">
                      <Camera className="w-4 h-4 text-primary" />
                      <div>
                         <p className="text-[11px] font-space-grotesk font-bold">{cam.name}</p>
                         <p className="text-[9px] font-jetbrains-mono text-neutral-500">{`INDEX_${cam.index} | READY`}</p>
                      </div>
                   </div>
                   <button 
                     onClick={() => startIngestion(cam.index.toString(), "camera")}
                     className="px-3 py-1.5 bg-primary/20 hover:bg-primary text-primary hover:text-black text-[9px] font-bold uppercase rounded-lg transition-all"
                   >
                      MOUNT
                   </button>
                </div>
             ))}

             {/* Manual index fallback (Bluetooth, etc) */}
             <div className="p-4 bg-black/20 rounded-2xl border border-outline-variant/10">
                <div className="flex items-center gap-2 mb-3">
                   <Settings className="w-3 h-3 text-neutral-500" />
                   <span className="text-[9px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest">Manual Hardware Index</span>
                </div>
                <div className="flex gap-2">
                   <input 
                     type="number" 
                     value={customIndex}
                     onChange={(e) => setCustomIndex(e.target.value)}
                     className="flex-grow bg-neutral-900 border border-outline-variant/20 rounded-xl px-4 py-2 text-xs font-jetbrains-mono outline-none focus:border-primary/50"
                     placeholder="ID (e.g. 1)"
                   />
                   <button 
                     onClick={() => startIngestion(customIndex, "camera")}
                     className="px-4 bg-surface-container-highest hover:bg-primary/20 text-[9px] font-bold uppercase rounded-xl border border-outline-variant/10 whitespace-nowrap"
                   >
                     Connect Index
                   </button>
                </div>
                <p className="mt-3 text-[8px] text-neutral-600 font-jetbrains-mono leading-relaxed">
                   Bluetooth cams and USB-Hub devices often mount on indices 1, 2, or 3.
                </p>
             </div>
          </div>
        </div>

        <div className="w-full h-[1px] bg-outline-variant/10"></div>

        {/* Neural Ingestion Sources */}
        <div>
          <h3 className="font-space-grotesk text-[10px] font-bold text-neutral-500 uppercase tracking-[0.3em] mb-6">Neural Ingestion</h3>
          
          <div className="space-y-4">
            {/* YouTube Search Engine */}
            <div className="p-5 bg-surface-container rounded-3xl border border-outline-variant/10 shadow-lg">
              <div className="flex justify-between items-start mb-4">
                <div className="p-2 bg-blue-500/10 rounded-xl">
                  <Monitor className="w-4 h-4 text-blue-400" />
                </div>
                <span className="font-jetbrains-mono text-[9px] text-neutral-500">YT_SEARCH</span>
              </div>
              <h4 className="font-space-grotesk text-sm font-bold mb-4">YouTube Search Engine</h4>
              <div className="relative mb-3">
                <input 
                  type="text" 
                  value={youtubeQuery}
                  onChange={(e) => setYoutubeQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  className="w-full bg-black/40 border border-outline-variant/20 rounded-2xl py-3 px-10 text-[11px] font-jetbrains-mono focus:border-blue-400/50 outline-none transition-all"
                  placeholder="e.g. Robot Hands"
                />
                <Search className="absolute left-4 top-3.5 w-4 h-4 text-neutral-500" />
              </div>
              
              {searchError && (
                 <div className="mb-3 p-3 bg-error/10 border border-error/20 rounded-xl flex items-start gap-2">
                    <AlertCircle className="w-3.5 h-3.5 text-error shrink-0 mt-0.5" />
                    <p className="text-[9px] text-error font-jetbrains-mono leading-tight">{searchError}</p>
                 </div>
              )}

              <button 
                onClick={handleSearch}
                disabled={isSearching}
                className="w-full py-3 bg-blue-500/10 hover:bg-blue-500 text-blue-400 hover:text-black text-[10px] font-bold uppercase rounded-2xl transition-all shadow-lg"
              >
                {isSearching ? "SEARCHING..." : "QUERY YOUTUBE"}
              </button>
            </div>

            {/* Static Image Ingestor */}
            <div className={`p-5 rounded-3xl border transition-all ${activeSource?.includes("IMAGE") ? 'bg-tertiary/10 border-tertiary/40' : 'bg-surface-container border-outline-variant/10'}`}>
              <div className="flex justify-between items-start mb-4">
                <div className="p-2 bg-black/20 rounded-xl">
                  <ImageIcon className={`w-4 h-4 ${activeSource?.includes("IMAGE") ? 'text-tertiary' : 'text-neutral-500'}`} />
                </div>
                <span className="font-jetbrains-mono text-[9px] text-neutral-500">LOCAL_IO</span>
              </div>
              <h4 className="font-space-grotesk text-sm font-bold mb-4">Static Analysis</h4>
              <label className="w-full py-2.5 bg-tertiary/10 hover:bg-tertiary text-tertiary hover:text-black text-[10px] font-bold uppercase rounded-2xl transition-all cursor-pointer flex items-center justify-center gap-2 border border-tertiary/20">
                <Upload className="w-3.5 h-3.5" />
                Upload Image
                <input type="file" className="hidden" accept="image/*" onChange={handleImageUpload} />
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content: High-Fidelity Viewport */}
      <div className="flex-grow flex flex-col p-8 gap-8 overflow-hidden">
        
        {/* Header HUD */}
        <div className="flex items-center justify-between flex-shrink-0">
           <div>
             <h1 className="text-4xl font-space-grotesk font-light uppercase tracking-tighter">Capture <span className="font-bold text-primary">Studio</span></h1>
             <p className="font-jetbrains-mono text-[10px] text-neutral-500 mt-2 flex items-center gap-2">
               {activeSource ? (
                 <><CheckCircle2 className="w-3 h-3 text-primary" /> PIPELINE_ATTACHED: {activeSource}</>
               ) : (
                 <><AlertCircle className="w-3 h-3 text-neutral-600" /> SOURCE_AWAITING_SIGNAL</>
               )}
             </p>
             {captureError && (
               <p className="font-jetbrains-mono text-[10px] text-error mt-2 flex items-center gap-2">
                 <AlertCircle className="w-3 h-3" /> {captureError}
               </p>
             )}
           </div>
           
           <div className="flex gap-8 items-center">
              <div className="text-right">
                <span className="block text-[8px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest mb-1">Inference Latency</span>
                <span className="text-2xl font-jetbrains-mono text-primary font-bold">{fps.toFixed(1)}<span className="text-xs ml-1 opacity-50">FPS</span></span>
              </div>
              <div className="w-[1px] h-10 bg-outline-variant/10"></div>
              <div className="text-right">
                <span className="block text-[8px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest mb-1">Neural Model</span>
                <span className="text-2xl font-jetbrains-mono text-white font-bold">{skeletonVersion}</span>
              </div>
           </div>
        </div>

        {/* Center: Viewport + Results Heatmap */}
        <div className="flex-grow flex gap-8 overflow-hidden">
           
           {/* Primary Viewport */}
           <div className="flex-grow bg-black rounded-[3rem] border border-outline-variant/10 shadow-[0_0_50px_rgba(0,0,0,0.5)] relative overflow-hidden flex items-center justify-center ring-1 ring-white/5">
              {isConnected ? (
                <>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    alt="Live annotated inference feed"
                    className="w-full h-full object-contain"
                    src={`${apiUrl("/video_feed")}?stream=${encodeURIComponent(activeSource || "live")}`}
                  />
                  <div className="absolute top-10 left-10 bg-black/60 backdrop-blur-xl border border-primary/40 px-6 py-3 rounded-2xl shadow-2xl">
                     <div className="flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-primary animate-pulse shadow-[0_0_10px_cyan]"></div>
                        <span className="font-jetbrains-mono text-[10px] font-bold text-primary uppercase tracking-[0.2em]">Live_Holographic_Inference</span>
                     </div>
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center gap-6 opacity-30">
                   <div className="relative">
                      <Crosshair className="w-20 h-20 text-primary stroke-[0.5] animate-spin-slow" />
                      <PlusCircle className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 text-primary/50" />
                   </div>
                   <p className="font-jetbrains-mono text-[11px] tracking-[0.3em] text-primary uppercase animate-pulse">Awaiting_Source_Engagement</p>
                </div>
              )}
           </div>

           {/* Results Overlay (If active) */}
           {searchResults.length > 0 && (
             <div className="w-[320px] flex-shrink-0 flex flex-col gap-6 animate-in fade-in slide-in-from-right-12 duration-700">
                <div className="flex justify-between items-center px-2">
                   <div className="flex items-center gap-2">
                      <BarChart className="w-4 h-4 text-blue-400" />
                      <h3 className="font-space-grotesk font-bold text-[10px] text-neutral-400 uppercase tracking-widest">Motion Match</h3>
                   </div>
                   <button onClick={() => setSearchResults([])} className="text-neutral-600 hover:text-white transition-colors uppercase font-bold text-[9px]">Dismiss</button>
                </div>
                <div className="space-y-6 overflow-y-auto custom-scrollbar pr-2">
                   {searchResults.map((res, i) => (
                     <div 
                        key={i} 
                        onClick={() => startIngestion(res.url, "youtube")}
                        className="group relative cursor-pointer aspect-video rounded-3xl overflow-hidden border border-outline-variant/10 hover:border-blue-400/50 transition-all bg-surface-container-high shadow-xl"
                     >
                        <Image alt={res.title} src={res.thumbnail} className="object-cover grayscale opacity-40 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-700 scale-105 group-hover:scale-110" fill sizes="320px" />
                        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent"></div>
                        <div className="absolute bottom-4 left-4 right-4 translate-y-2 group-hover:translate-y-0 transition-transform">
                           <p className="text-[10px] font-space-grotesk font-bold text-white line-clamp-2 leading-tight drop-shadow-lg">{res.title}</p>
                           <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              <span className="text-[8px] font-jetbrains-mono text-blue-400 px-2 py-0.5 bg-blue-400/10 rounded-full border border-blue-400/20">ATTACH_STREAM</span>
                           </div>
                        </div>
                     </div>
                   ))}
                </div>
             </div>
           )}
        </div>

        {/* Bottom Tactical Bar */}
        <div className="h-28 flex-shrink-0 flex gap-10 items-center bg-surface-container p-8 rounded-[2.5rem] border border-outline-variant/10 shadow-2xl relative overflow-hidden group">
           <div className="flex gap-4 border-r border-outline-variant/20 pr-10">
              <button 
                onClick={toggleOverlay}
                className={`p-5 rounded-3xl transition-all duration-500 scale-100 active:scale-90 ${showOverlay ? 'bg-primary/20 text-primary border border-primary/40 shadow-[0_0_20px_rgba(0,242,255,0.2)]' : 'bg-surface-container-highest text-neutral-500 hover:text-white'}`}
                title="Toggle Neural Overlay"
              >
                <Sliders className="w-6 h-6" />
              </button>
              <button 
                onClick={toggleRecording}
                className={`p-5 rounded-3xl transition-all duration-500 scale-100 active:scale-90 ${isRecording ? 'bg-tertiary/20 text-tertiary border border-tertiary/40 shadow-[0_0_20px_rgba(255,160,0,0.2)]' : 'bg-surface-container-highest text-neutral-500 hover:text-white'}`}
                title="Toggle Dataset Recording"
              >
                <Database className="w-6 h-6" />
              </button>
           </div>

           <div className="flex-grow flex items-center gap-12">
              <div className="flex flex-col">
                 <span className="text-[9px] font-jetbrains-mono text-neutral-500 uppercase tracking-[0.2em] mb-3">System Persistence</span>
                 <div className="flex gap-1.5 grayscale group-hover:grayscale-0 transition-all duration-700">
                    {Array.from({length: 12}).map((_, i) => (
                       <div key={i} className={`w-3.5 h-1.5 rounded-full ${i < 9 ? 'bg-primary shadow-[0_0_8px_cyan]' : 'bg-neutral-800'}`}></div>
                    ))}
                 </div>
              </div>
              
              <div className="flex items-center gap-4 ml-auto">
                 <div className="text-right">
                    <p className="text-[8px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest">Protocol Status</p>
                    <p className="text-[10px] font-space-grotesk font-black text-white uppercase tracking-widest">Safe_Operation</p>
                 </div>
                 <button 
                   onClick={() => fetch(apiUrl("/api/v1/control/emergency/stop"), { method: "POST" })}
                   className="flex items-center gap-4 px-10 py-5 bg-error/10 hover:bg-error border border-error/40 hover:border-error text-error hover:text-white rounded-[1.5rem] transition-all duration-500 group/btn shadow-lg"
                 >
                    <ShieldAlert className="w-6 h-6 transform group-hover/btn:rotate-12 transition-transform" />
                    <span className="font-space-grotesk font-black text-xs uppercase tracking-[0.2em]">Emergency Halt</span>
                 </button>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
