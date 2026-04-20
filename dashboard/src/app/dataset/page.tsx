"use client";

import Image from 'next/image';
import Link from 'next/link';
import React, { useCallback, useState, useEffect } from 'react';
import { Database, Download, UploadCloud, Search, PlayCircle, StopCircle, HardDrive, Clock, ChevronRight, LayoutGrid, FolderTree, FileText, CheckCircle2, Sparkles, MonitorPlay } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { apiUrl } from '@/lib/api';
import type { AutoYouTubePipelineJob, BatchSummary } from '@/types/telemetry';

export default function DatasetManager() {
  const { isRecording, bridgeStatus } = useStore();
  const [sessionName, setSessionName] = useState('mission_alpha');
  const [isLoading, setIsLoading] = useState(false);
  const [sessions, setSessions] = useState<string[]>([]);
  const [batches, setBatches] = useState<BatchSummary[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [autoCategories, setAutoCategories] = useState('workout, dance, sports, arts, cooking');
  const [resultsPerCategory, setResultsPerCategory] = useState(1);
  const [sampleFps, setSampleFps] = useState('3');
  const [chunkFrames, setChunkFrames] = useState(90);
  const [autoJob, setAutoJob] = useState<AutoYouTubePipelineJob | null>(null);
  const [autoJobs, setAutoJobs] = useState<AutoYouTubePipelineJob[]>([]);
  const [thumbnailFallbacks, setThumbnailFallbacks] = useState<Record<string, string>>({});
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(apiUrl("/dataset/sessions"));
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch (e) {
      console.error("Fetch sessions error:", e);
    }
  }, []);

  const fetchBatches = useCallback(async () => {
    try {
      const res = await fetch(apiUrl("/dataset/batches"));
      const data = await res.json();
      const nextBatches = (data.batches || []) as BatchSummary[];
      setBatches(nextBatches);
      if (!selectedBatchId && nextBatches.length > 0) {
        setSelectedBatchId(nextBatches[0].batch_id);
      }
    } catch (e) {
      console.error("Fetch batches error:", e);
    }
  }, [selectedBatchId]);

  const fetchAutoPipelineStatus = useCallback(async () => {
    try {
      const res = await fetch(apiUrl("/pipeline/youtube/auto/status"));
      const data = await res.json();
      setAutoJob(data.job || null);
      if (!selectedBatchId && data.job?.batch_id) {
        setSelectedBatchId(data.job.batch_id);
      }
    } catch (e) {
      console.error("Fetch auto pipeline status error:", e);
    }
  }, [selectedBatchId]);

  const fetchAutoPipelineJobs = useCallback(async () => {
    try {
      const res = await fetch(apiUrl("/pipeline/youtube/auto/jobs?limit=6"));
      const data = await res.json();
      setAutoJobs((data.jobs || []) as AutoYouTubePipelineJob[]);
    } catch (e) {
      console.error("Fetch auto pipeline jobs error:", e);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
    fetchBatches();
    fetchAutoPipelineStatus();
    fetchAutoPipelineJobs();
    const interval = setInterval(() => {
      fetchSessions();
      fetchBatches();
      fetchAutoPipelineStatus();
      fetchAutoPipelineJobs();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchAutoPipelineJobs, fetchAutoPipelineStatus, fetchBatches, fetchSessions]);

  const toggleRecording = async () => {
    setIsLoading(true);
    setStatusMessage(null);
    try {
      if (isRecording) {
        const res = await fetch(apiUrl("/dataset/stop"), { method: "POST" });
        if (!res.ok) throw new Error("stop");
        await fetchSessions();
        setStatusMessage("Dataset session stopped.");
      } else {
        const res = await fetch(apiUrl(`/dataset/start?name=${encodeURIComponent(sessionName)}`), { method: "POST" });
        if (!res.ok) throw new Error("start");
        setStatusMessage(`Dataset session "${sessionName}" started.`);
      }
    } catch (e) {
      setStatusMessage("Recording request failed.");
      console.error("Recording error:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const runExport = async (name: string) => {
    setIsLoading(true);
    setStatusMessage(null);
    try {
      const res = await fetch(apiUrl(`/dataset/export?name=${encodeURIComponent(name)}`), { method: "POST" });
      if (res.ok) {
        setStatusMessage(`Export complete for ${name}.`);
      } else {
        setStatusMessage(`Export failed for ${name}.`);
      }
    } catch (e) {
      setStatusMessage(`Export failed for ${name}.`);
      console.error("Export error:", e);
    } finally {
      setIsLoading(false);
    }
  };
  const liveLinkActive = bridgeStatus.blender && bridgeStatus.isaac;
  const selectedBatch = batches.find((batch) => batch.batch_id === selectedBatchId) || null;

  const toggleLiveLink = async () => {
    const nextEnabled = !liveLinkActive;
    setStatusMessage(null);
    try {
      const blenderRes = await fetch(apiUrl(`/control/bridge/blender/toggle?enabled=${nextEnabled}`), { method: "POST" });
      const isaacRes = await fetch(apiUrl(`/control/bridge/isaac/toggle?enabled=${nextEnabled}`), { method: "POST" });
      if (!blenderRes.ok || !isaacRes.ok) {
        throw new Error("bridge-toggle");
      }
      setStatusMessage(nextEnabled ? "Simulator bridges enabled." : "Simulator bridges disabled.");
    } catch (e) {
      setStatusMessage("Simulator bridge toggle failed.");
      console.error("Simulator bridge error:", e);
    }
  };

  const startAutoPipeline = async () => {
    setIsLoading(true);
    setStatusMessage(null);
    try {
      const categories = autoCategories
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean);
      const parsedSampleFps = Number.parseFloat(sampleFps);
      const res = await fetch(apiUrl("/pipeline/youtube/auto/start"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          categories,
          results_per_category: resultsPerCategory,
          sample_fps: Number.isFinite(parsedSampleFps) && parsedSampleFps > 0 ? parsedSampleFps : null,
          chunk_frames: chunkFrames,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "auto-pipeline-start");
      }
      setAutoJob(data.job || null);
      setStatusMessage("Auto YouTube pipeline started.");
    } catch (e) {
      console.error("Auto pipeline error:", e);
      setStatusMessage(e instanceof Error ? e.message : "Failed to start auto YouTube pipeline.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-[1700px] mx-auto text-on-surface h-[calc(100vh-64px)] flex flex-col gap-8 overflow-hidden">
      <div className="flex justify-between items-end flex-shrink-0">
        <div>
          <h1 className="text-4xl font-space-grotesk font-light uppercase tracking-tighter">
            Dataset <span className="text-primary font-bold">Manager</span>
          </h1>
          <p className="font-jetbrains-mono text-[10px] text-neutral-500 mt-2 flex items-center gap-2 uppercase">
            <Database className="w-3 h-3" /> Synthetic Lab // Neural Repository Index
          </p>
          {statusMessage && (
            <p className="font-jetbrains-mono text-[10px] text-neutral-400 mt-2">{statusMessage}</p>
          )}
        </div>
        <div className="flex gap-4">
          <button className="bg-primary/10 text-primary px-4 py-2 rounded-xl border border-primary/20 flex items-center gap-2 hover:bg-primary/20 transition-all group">
            <UploadCloud className="w-4 h-4 group-hover:scale-110 transition-transform" />
            <span className="font-jetbrains-mono text-[10px] uppercase font-bold">Cloud Sync</span>
          </button>
        </div>
      </div>
      
      <div className="flex-grow grid grid-cols-12 gap-8 overflow-hidden">
        {/* Left Area: Ingestion Controller */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-6">
           
           {/* Active Session Controller */}
           <div className="bg-surface-container rounded-[2rem] p-8 border border-outline-variant/10 shadow-xl">
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                   <div className={`w-3 h-3 rounded-full ${isRecording ? 'bg-error animate-pulse shadow-[0_0_10px_red]' : 'bg-neutral-600'}`}></div>
                   <h3 className="font-jetbrains-mono text-[11px] uppercase tracking-widest text-neutral-400">Mission Recorder</h3>
                </div>
                <span className="text-[9px] font-bold text-primary px-2 py-0.5 bg-primary/10 rounded uppercase font-jetbrains-mono tracking-widest">Live_Input</span>
              </div>
              
              <div className="space-y-6">
                <div>
                  <label className="block font-jetbrains-mono text-[9px] text-neutral-500 mb-2 uppercase tracking-widest">Session Identifier</label>
                  <input 
                    type="text" 
                    value={sessionName}
                    onChange={(e) => setSessionName(e.target.value)}
                    disabled={isRecording}
                    className="w-full bg-black/40 border border-outline-variant/20 rounded-2xl px-4 py-3 text-[13px] font-jetbrains-mono text-primary outline-none focus:border-primary/50 transition-all disabled:opacity-40"
                    placeholder="ENTER_SESS_ID..."
                  />
                </div>
                
                <button 
                   onClick={toggleRecording}
                   disabled={isLoading}
                   className={`w-full flex flex-col items-center justify-center gap-2 py-6 rounded-[2rem] border transition-all duration-500 group relative overflow-hidden ${
                     isRecording 
                       ? 'bg-error/10 border-error/50 text-error hover:bg-error/20' 
                       : 'bg-primary/10 border-primary/50 text-primary hover:bg-primary/20 active:scale-95'
                   }`}
                >
                   {isRecording ? <StopCircle className="w-10 h-10 mb-1" /> : <PlayCircle className="w-10 h-10 mb-1" />}
                   <span className="font-space-grotesk font-black uppercase text-[12px] tracking-widest">
                      {isLoading ? 'SYNCING...' : isRecording ? 'STOP SESSION' : 'INITIALIZE CAPTURE'}
                   </span>
                   {isRecording && <div className="absolute top-0 left-0 w-full h-1 bg-error animate-progress"></div>}
                </button>
              </div>
           </div>

           {/* Simulator Logic */}
           <div className="bg-surface-container-high rounded-[2rem] p-8 border border-outline-variant/10 shadow-lg">
             <div className="flex items-center justify-between mb-6">
               <div className="flex items-center gap-3">
                 <HardDrive className="w-4 h-4 text-tertiary" />
                 <h3 className="font-jetbrains-mono text-[11px] uppercase tracking-widest text-neutral-400">Simulator Bridge</h3>
               </div>
               <button 
                 onClick={toggleLiveLink}
                 className={`w-12 h-6 rounded-full px-1 flex items-center transition-all duration-300 ${liveLinkActive ? 'bg-tertiary shadow-[0_0_15px_rgba(255,160,0,0.4)]' : 'bg-neutral-800'}`}
               >
                 <div className={`w-4 h-4 rounded-full bg-white transition-all transform ${liveLinkActive ? 'translate-x-6' : 'translate-x-0'}`}></div>
               </button>
             </div>
             <p className="text-[10px] font-jetbrains-mono text-neutral-500 leading-relaxed">
               Enables real-time UDP/WS telemetry broadcast for Blender & Isaac Sim hardware digital twins.
             </p>
           </div>

           <div className="bg-surface-container-high rounded-[2rem] p-8 border border-outline-variant/10 shadow-lg">
             <div className="flex items-center justify-between mb-6">
               <div className="flex items-center gap-3">
                 <MonitorPlay className="w-4 h-4 text-primary" />
                 <h3 className="font-jetbrains-mono text-[11px] uppercase tracking-widest text-neutral-400">Auto YouTube Pipeline</h3>
               </div>
               <Sparkles className={`w-4 h-4 ${autoJob?.status === 'running' ? 'text-primary animate-pulse' : 'text-neutral-500'}`} />
             </div>

             <div className="space-y-4">
               <div>
                 <label className="block font-jetbrains-mono text-[9px] text-neutral-500 mb-2 uppercase tracking-widest">Category Criteria</label>
                 <textarea
                   value={autoCategories}
                   onChange={(e) => setAutoCategories(e.target.value)}
                   rows={3}
                   className="w-full bg-black/40 border border-outline-variant/20 rounded-2xl px-4 py-3 text-[11px] font-jetbrains-mono text-primary outline-none focus:border-primary/50 transition-all resize-none"
                   placeholder="workout, dance, sports, arts, cooking"
                 />
               </div>

               <div>
                 <label className="block font-jetbrains-mono text-[9px] text-neutral-500 mb-2 uppercase tracking-widest">Videos Per Category</label>
                 <input
                   type="number"
                   min={1}
                   max={3}
                   value={resultsPerCategory}
                   onChange={(e) => setResultsPerCategory(parseInt(e.target.value || "1"))}
                   className="w-full bg-black/40 border border-outline-variant/20 rounded-2xl px-4 py-3 text-[11px] font-jetbrains-mono text-primary outline-none focus:border-primary/50 transition-all"
                 />
               </div>

               <div className="grid grid-cols-2 gap-3">
                 <div>
                   <label className="block font-jetbrains-mono text-[9px] text-neutral-500 mb-2 uppercase tracking-widest">Sample FPS</label>
                   <input
                     type="number"
                     min="0.5"
                     step="0.5"
                     value={sampleFps}
                     onChange={(e) => setSampleFps(e.target.value)}
                     className="w-full bg-black/40 border border-outline-variant/20 rounded-2xl px-4 py-3 text-[11px] font-jetbrains-mono text-primary outline-none focus:border-primary/50 transition-all"
                   />
                 </div>
                 <div>
                   <label className="block font-jetbrains-mono text-[9px] text-neutral-500 mb-2 uppercase tracking-widest">Chunk Frames</label>
                   <input
                     type="number"
                     min={30}
                     step={30}
                     value={chunkFrames}
                     onChange={(e) => setChunkFrames(Math.max(30, parseInt(e.target.value || "90", 10)))}
                     className="w-full bg-black/40 border border-outline-variant/20 rounded-2xl px-4 py-3 text-[11px] font-jetbrains-mono text-primary outline-none focus:border-primary/50 transition-all"
                   />
                 </div>
               </div>

               <button
                 onClick={startAutoPipeline}
                 disabled={isLoading || autoJob?.status === 'running'}
                 className="w-full flex items-center justify-center gap-2 py-4 rounded-2xl bg-primary/10 border border-primary/40 text-primary hover:bg-primary/20 disabled:opacity-50 transition-all text-[11px] font-space-grotesk font-bold uppercase"
               >
                 <PlayCircle className="w-4 h-4" />
                 {autoJob?.status === 'running' ? 'Pipeline Running' : 'Start Auto Collection'}
               </button>

               <div className="bg-black/20 rounded-2xl border border-outline-variant/10 px-4 py-3 space-y-2">
                 <div className="flex items-center justify-between text-[10px] font-jetbrains-mono">
                   <span className="text-neutral-500 uppercase">Phase</span>
                   <span className="text-primary uppercase">{autoJob?.phase || 'idle'}</span>
                 </div>
                 <p className="text-[10px] font-jetbrains-mono text-neutral-400 leading-relaxed">
                   {autoJob?.message || 'Search, download, batch-process, and report YouTube videos from the selected criteria.'}
                 </p>
                 <div className="flex items-center justify-between text-[10px] font-jetbrains-mono text-neutral-500">
                   <span>Downloaded: {autoJob?.downloaded_videos?.length || 0}</span>
                   <span>Status: {autoJob?.status || 'idle'}</span>
                 </div>
                 {autoJob?.error && (
                   <p className="text-[10px] font-jetbrains-mono text-error leading-relaxed">
                     {autoJob.error}
                   </p>
                 )}
                 {autoJob?.downloaded_videos?.slice(-3).map((video) => (
                   <div key={`${autoJob.job_id}-${video.video_id || video.local_path}`} className="rounded-xl border border-outline-variant/10 bg-black/20 px-3 py-2">
                     <p className="text-[10px] font-jetbrains-mono text-white truncate">{video.title || video.url || 'Downloaded video'}</p>
                     <p className="text-[9px] font-jetbrains-mono text-neutral-500 uppercase mt-1">
                       {video.category || 'Uncategorized'}
                     </p>
                   </div>
                 ))}
                 {autoJob?.batch_id && (
                   <button onClick={() => setSelectedBatchId(autoJob.batch_id || null)} className="inline-flex items-center gap-2 text-[10px] font-jetbrains-mono text-tertiary uppercase">
                     Open Batch {autoJob.batch_id}
                   </button>
                 )}
               </div>

               {autoJobs.length > 0 && (
                 <div className="space-y-2">
                   <p className="text-[9px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest">Recent Auto Jobs</p>
                   <div className="space-y-2 max-h-36 overflow-y-auto custom-scrollbar pr-1">
                     {autoJobs.map((job) => (
                       <button
                         key={job.job_id}
                         onClick={() => {
                           setAutoJob(job);
                           if (job.batch_id) {
                             setSelectedBatchId(job.batch_id);
                           }
                         }}
                         className={`w-full rounded-2xl border px-3 py-2 text-left transition-all ${
                           autoJob?.job_id === job.job_id
                             ? 'border-primary/40 bg-primary/10'
                             : 'border-outline-variant/10 bg-black/20 hover:border-primary/20'
                         }`}
                       >
                         <div className="flex items-center justify-between gap-3">
                           <span className="text-[10px] font-jetbrains-mono text-white truncate">{job.job_id}</span>
                           <span className="text-[9px] font-jetbrains-mono text-neutral-500 uppercase">{job.status}</span>
                         </div>
                         <p className="mt-1 text-[9px] font-jetbrains-mono text-neutral-500 truncate">{job.message}</p>
                       </button>
                     ))}
                   </div>
                 </div>
               )}
             </div>
           </div>
        </div>

        {/* Right Area: Session Archive Grid */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-4 overflow-hidden">
           <div className="bg-surface-container rounded-[2rem] border border-outline-variant/10 p-6 shadow-xl">
             <div className="flex items-center justify-between gap-4 mb-5">
               <div className="flex items-center gap-3">
                 <FolderTree className="w-4 h-4 text-primary" />
                 <div>
                   <h3 className="font-jetbrains-mono text-[11px] uppercase tracking-[0.2em] text-neutral-400">Batch Library</h3>
                   <p className="text-[10px] font-jetbrains-mono text-neutral-500 mt-1">Processed multi-video workflow batches and consolidated reports.</p>
                 </div>
               </div>
               <div className="flex items-center gap-3">
                 <select
                   value={selectedBatchId || ''}
                   onChange={(e) => setSelectedBatchId(e.target.value || null)}
                   className="bg-surface-container-high border border-outline-variant/10 rounded-full px-4 py-2 text-[10px] font-jetbrains-mono outline-none focus:border-primary/50"
                 >
                   {batches.map((batch) => (
                     <option key={batch.batch_id} value={batch.batch_id}>
                       {batch.batch_id}
                     </option>
                   ))}
                 </select>
                 {selectedBatch && (
                   <>
                     <a href={apiUrl(`/dataset/batch/${selectedBatch.batch_id}/artifact/report_csv`)} className="px-3 py-2 rounded-xl bg-primary/10 text-primary border border-primary/20 text-[10px] font-jetbrains-mono uppercase flex items-center gap-2">
                       <Download className="w-3 h-3" />
                       CSV
                     </a>
                     <a href={apiUrl(`/dataset/batch/${selectedBatch.batch_id}/artifact/report_json`)} className="px-3 py-2 rounded-xl bg-black/20 text-neutral-300 border border-outline-variant/10 text-[10px] font-jetbrains-mono uppercase flex items-center gap-2">
                       <FileText className="w-3 h-3" />
                       JSON
                     </a>
                   </>
                 )}
               </div>
             </div>

             {selectedBatch ? (
               <div className="space-y-5">
                 <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
                   <div className="bg-surface-container-high rounded-2xl border border-outline-variant/10 px-4 py-3">
                     <span className="block text-[9px] font-jetbrains-mono text-neutral-500 uppercase">Videos</span>
                     <span className="text-lg font-jetbrains-mono text-primary font-bold">{selectedBatch.completed_count} / {selectedBatch.video_count}</span>
                   </div>
                   <div className="bg-surface-container-high rounded-2xl border border-outline-variant/10 px-4 py-3">
                     <span className="block text-[9px] font-jetbrains-mono text-neutral-500 uppercase">Verified</span>
                     <span className="text-lg font-jetbrains-mono text-tertiary font-bold">{selectedBatch.verified_count}</span>
                   </div>
                   <div className="bg-surface-container-high rounded-2xl border border-outline-variant/10 px-4 py-3">
                     <span className="block text-[9px] font-jetbrains-mono text-neutral-500 uppercase">Processed Frames</span>
                     <span className="text-lg font-jetbrains-mono text-white font-bold">{selectedBatch.processed_frames_total}</span>
                   </div>
                   <div className="bg-surface-container-high rounded-2xl border border-outline-variant/10 px-4 py-3">
                     <span className="block text-[9px] font-jetbrains-mono text-neutral-500 uppercase">Tracked Frames</span>
                     <span className="text-lg font-jetbrains-mono text-white font-bold">{selectedBatch.tracked_frames_total}</span>
                   </div>
                 </div>

                 <div className="space-y-3 max-h-72 overflow-y-auto custom-scrollbar pr-2">
                   {selectedBatch.videos.map((video) => (
                     <div key={video.session_name} className="bg-black/20 rounded-2xl border border-outline-variant/10 p-4">
                       <div className="flex items-start justify-between gap-4">
                         <div>
                           <div className="flex items-center gap-2">
                             <h4 className="text-sm font-space-grotesk font-bold text-white">{video.inspection?.name || video.session_name}</h4>
                             {video.workflow?.verification_ok && <CheckCircle2 className="w-4 h-4 text-tertiary" />}
                           </div>
                           <p className="text-[9px] font-jetbrains-mono text-neutral-500 uppercase mt-1">
                             Session: {video.session_name}
                           </p>
                           <p className="text-[9px] font-jetbrains-mono text-neutral-600 mt-2">
                             {video.summary?.processed_frames || 0} processed / {video.summary?.tracked_frames || 0} tracked
                             {' • '}
                             sample {video.workflow?.sample_fps?.toFixed(2) || '0.00'} fps
                           </p>
                         </div>
                         <div className="grid grid-cols-3 gap-2 flex-shrink-0">
                           <Link href={`/timeline?session=${encodeURIComponent(video.session_name)}`} className="px-3 py-2 rounded-xl bg-primary/10 text-primary border border-primary/20 text-[9px] font-bold uppercase text-center">
                             View
                           </Link>
                           <Link href={`/retargeting?session=${encodeURIComponent(video.session_name)}`} className="px-3 py-2 rounded-xl bg-black/20 text-neutral-300 border border-outline-variant/10 text-[9px] font-bold uppercase text-center">
                             Retarget
                           </Link>
                           <Link href={`/simulation?session=${encodeURIComponent(video.session_name)}`} className="px-3 py-2 rounded-xl bg-black/20 text-neutral-300 border border-outline-variant/10 text-[9px] font-bold uppercase text-center">
                             Simulate
                           </Link>
                         </div>
                       </div>
                     </div>
                   ))}
                 </div>
               </div>
             ) : (
               <div className="h-40 flex items-center justify-center text-neutral-600 text-[11px] font-jetbrains-mono uppercase tracking-widest opacity-40">
                 No batch workflow detected
               </div>
             )}
           </div>

           <div className="flex items-center justify-between px-2">
             <div className="flex items-center gap-3">
               <LayoutGrid className="w-4 h-4 text-primary" />
               <h3 className="font-jetbrains-mono text-[11px] uppercase tracking-[0.2em] text-neutral-400">Mission Archive</h3>
             </div>
             <div className="relative">
               <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3 h-3 text-neutral-500" />
               <input type="text" placeholder="FILTER_LOGS..." className="bg-surface-container-high border border-outline-variant/10 rounded-full pl-9 pr-4 py-1.5 text-[10px] font-jetbrains-mono outline-none focus:border-primary/50" />
             </div>
           </div>

           <div className="flex-grow bg-surface-container rounded-[2rem] border border-outline-variant/10 overflow-y-auto custom-scrollbar p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {sessions.length === 0 ? (
                  <div className="col-span-full h-64 flex flex-col items-center justify-center text-neutral-600 gap-4 opacity-30">
                     <Database className="w-12 h-12" />
                     <p className="font-jetbrains-mono text-[11px] uppercase tracking-widest">No Sessions Found</p>
                  </div>
                ) : (
                  sessions.map((name) => (
                    <div key={name} className="group bg-black/40 rounded-3xl overflow-hidden border border-outline-variant/10 hover:border-primary/30 transition-all flex flex-col shadow-xl">
                       <div className="aspect-video relative overflow-hidden bg-neutral-900 flex items-center justify-center">
                          <Image 
                            alt={`${name} session thumbnail`}
                            src={thumbnailFallbacks[name] || apiUrl(`/dataset/session/${name}/thumbnail`)} 
                            className="object-cover opacity-60 group-hover:opacity-100 transition-opacity duration-500"
                            fill
                            sizes="(max-width: 768px) 100vw, (max-width: 1280px) 50vw, 33vw"
                            unoptimized
                            onError={() => {
                               setThumbnailFallbacks((current) => ({
                                 ...current,
                                 [name]: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&q=80&w=320&h=180",
                               }));
                            }}
                          />
                          <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent"></div>
                          <div className="absolute top-4 left-4 p-2 bg-black/60 backdrop-blur rounded-lg border border-white/5">
                             <Clock className="w-3 h-3 text-primary" />
                          </div>
                       </div>
                       
                       <div className="p-5 flex flex-col gap-4">
                          <div>
                            <h4 className="font-space-grotesk font-bold text-sm text-white truncate mb-1">{name}</h4>
                            <div className="flex justify-between items-center text-[9px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest">
                               <span>640p @ 30fps</span>
                               <span className="text-primary font-bold">Processed</span>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-2">
                             <button 
                               onClick={() => runExport(name)}
                               className="flex items-center justify-center gap-2 py-2 bg-primary/10 text-primary border border-primary/20 rounded-xl text-[9px] font-bold uppercase hover:bg-primary/20 transition-all"
                             >
                                <Download className="w-3 h-3" /> Export
                             </button>
                             <Link href={`/timeline?session=${encodeURIComponent(name)}`} className="flex items-center justify-center gap-2 py-2 bg-neutral-900 text-neutral-400 border border-outline-variant/10 rounded-xl text-[9px] font-bold uppercase hover:bg-neutral-800 transition-all">
                                View <ChevronRight className="w-3 h-3" />
                             </Link>
                          </div>
                          <div className="grid grid-cols-2 gap-2">
                             <Link href={`/retargeting?session=${encodeURIComponent(name)}`} className="flex items-center justify-center gap-2 py-2 bg-black/20 text-neutral-300 border border-outline-variant/10 rounded-xl text-[9px] font-bold uppercase hover:bg-black/30 transition-all">
                                Retarget
                             </Link>
                             <Link href={`/simulation?session=${encodeURIComponent(name)}`} className="flex items-center justify-center gap-2 py-2 bg-black/20 text-neutral-300 border border-outline-variant/10 rounded-xl text-[9px] font-bold uppercase hover:bg-black/30 transition-all">
                                Simulate
                             </Link>
                          </div>
                       </div>
                    </div>
                  ))
                )}
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
