"use client";

import React, { useEffect, useState, useCallback } from 'react';
import { 
  History, 
  Search, 
  Filter, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  AlertCircle, 
  ChevronRight, 
  ExternalLink,
  Download,
  Database,
  ArrowRight
} from 'lucide-react';
import { apiUrl } from '@/lib/api';
import type { AutoYouTubePipelineJob } from '@/types/telemetry';
import Link from 'next/link';

type StatusFilter = 'all' | 'completed' | 'failed' | 'running' | 'interrupted';

export default function JobHistory() {
  const [jobs, setJobs] = useState<AutoYouTubePipelineJob[]>([]);
  const [filteredJobs, setFilteredJobs] = useState<AutoYouTubePipelineJob[]>([]);
  const [filter, setFilter] = useState<StatusFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const fetchJobs = useCallback(async () => {
    try {
      const res = await fetch(apiUrl("/pipeline/youtube/auto/jobs?limit=50"));
      const data = await res.json();
      const jobList = (data.jobs || []) as AutoYouTubePipelineJob[];
      setJobs(jobList);
      setIsLoading(false);
    } catch (e) {
      console.error("Fetch jobs error:", e);
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 10000);
    return () => clearInterval(interval);
  }, [fetchJobs]);

  useEffect(() => {
    let result = [...jobs];
    
    if (filter !== 'all') {
      result = result.filter(job => job.status === filter);
    }
    
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(job => 
        job.job_id.toLowerCase().includes(query) || 
        job.message.toLowerCase().includes(query) ||
        job.categories?.some(cat => cat.toLowerCase().includes(query))
      );
    }
    
    setFilteredJobs(result);
  }, [jobs, filter, searchQuery]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="w-4 h-4 text-tertiary" />;
      case 'running': return <Clock className="w-4 h-4 text-primary animate-pulse" />;
      case 'failed': return <XCircle className="w-4 h-4 text-error" />;
      case 'interrupted': return <AlertCircle className="w-4 h-4 text-error/60" />;
      default: return <Clock className="w-4 h-4 text-neutral-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-tertiary bg-tertiary/10 border-tertiary/20';
      case 'running': return 'text-primary bg-primary/10 border-primary/20';
      case 'failed': return 'text-error bg-error/10 border-error/20';
      case 'interrupted': return 'text-error/60 bg-error/5 border-error/10';
      default: return 'text-neutral-500 bg-neutral-500/10 border-neutral-500/20';
    }
  };

  return (
    <div className="p-8 max-w-[1700px] mx-auto text-on-surface h-[calc(100vh-64px)] flex flex-col gap-8 overflow-hidden">
      {/* Header */}
      <div className="flex justify-between items-end flex-shrink-0">
        <div>
          <h1 className="text-4xl font-space-grotesk font-light uppercase tracking-tighter">
            Job <span className="text-primary font-bold">History</span>
          </h1>
          <p className="font-jetbrains-mono text-[10px] text-neutral-500 mt-2 flex items-center gap-2 uppercase tracking-widest">
            <History className="w-3 h-3" /> Synthesis Pipeline Audit // Archive 
          </p>
        </div>
        
        <div className="flex gap-4">
           {/* Summary Stats */}
           <div className="flex gap-8 px-6 py-3 bg-surface-container rounded-2xl border border-outline-variant/10">
              <div className="flex flex-col">
                <span className="text-[8px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest">Total Jobs</span>
                <span className="text-sm font-jetbrains-mono text-white font-bold">{jobs.length}</span>
              </div>
              <div className="flex flex-col border-l border-outline-variant/10 pl-8">
                <span className="text-[8px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest">Success Rate</span>
                <span className="text-sm font-jetbrains-mono text-tertiary font-bold">
                  {jobs.length > 0 ? ((jobs.filter(j => j.status === 'completed').length / jobs.length) * 100).toFixed(1) : 0}%
                </span>
              </div>
           </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between gap-6 px-6 py-4 bg-surface-container rounded-3xl border border-outline-variant/10 shadow-lg">
         <div className="flex items-center gap-6 flex-grow max-w-2xl">
            <div className="relative flex-grow">
               <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
               <input 
                 type="text" 
                 placeholder="SEARCH_BY_JOB_ID_OR_CATEGORY..." 
                 value={searchQuery}
                 onChange={(e) => setSearchQuery(e.target.value)}
                 className="w-full bg-black/40 border border-outline-variant/10 rounded-2xl pl-11 pr-4 py-3 text-[11px] font-jetbrains-mono text-primary outline-none focus:border-primary/40 transition-all font-bold placeholder:opacity-30"
               />
            </div>
            
            <div className="flex items-center gap-2">
               <Filter className="w-3 h-3 text-neutral-500" />
               <select 
                 value={filter}
                 onChange={(e) => setFilter(e.target.value as StatusFilter)}
                 className="bg-black/40 border border-outline-variant/10 rounded-2xl px-4 py-3 text-[11px] font-jetbrains-mono text-neutral-300 outline-none focus:border-primary/40 transition-all uppercase"
               >
                  <option value="all">Status: ALL</option>
                  <option value="completed">Status: COMPLETED</option>
                  <option value="running">Status: RUNNING</option>
                  <option value="failed">Status: FAILED</option>
                  <option value="interrupted">Status: INTERRUPTED</option>
               </select>
            </div>
         </div>

         <button 
           onClick={() => fetchJobs()}
           className="p-3 bg-primary/10 text-primary border border-primary/20 rounded-2xl hover:bg-primary/20 transition-all active:scale-95"
         >
            <History className="w-5 h-5" />
         </button>
      </div>

      {/* Job Grid */}
      <div className="flex-grow overflow-y-auto custom-scrollbar pr-2">
         {isLoading ? (
           <div className="h-full flex items-center justify-center">
              <div className="flex flex-col items-center gap-4 opacity-40">
                 <History className="w-12 h-12 text-primary animate-spin-slow" />
                 <p className="font-jetbrains-mono text-[11px] uppercase tracking-[0.2em]">Synchronizing Archive...</p>
              </div>
           </div>
         ) : filteredJobs.length === 0 ? (
           <div className="h-full flex flex-col items-center justify-center text-neutral-600 gap-4 opacity-40">
              <Database className="w-16 h-16" />
              <p className="font-jetbrains-mono text-[12px] uppercase tracking-[0.3em]">No Matching Records Found</p>
           </div>
         ) : (
           <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 pb-8">
              {filteredJobs.map((job) => (
                <div key={job.job_id} className="bg-surface-container rounded-[2rem] border border-outline-variant/10 overflow-hidden flex transition-all hover:bg-surface-container-high group">
                   <div className={`w-2 flex-shrink-0 ${job.status === 'completed' ? 'bg-tertiary' : job.status === 'running' ? 'bg-primary' : 'bg-error'}`}></div>
                   
                   <div className="flex-grow p-8 flex flex-col gap-6">
                      <div className="flex justify-between items-start">
                         <div>
                            <p className="text-[10px] font-jetbrains-mono text-neutral-500 uppercase tracking-widest mb-1">JOB_ID_IDENTIFIER</p>
                            <h3 className="text-lg font-space-grotesk font-black text-white group-hover:text-primary transition-colors">{job.job_id}</h3>
                         </div>
                         <div className={`px-4 py-1.5 rounded-full border text-[10px] font-jetbrains-mono font-bold uppercase tracking-widest flex items-center gap-2 ${getStatusColor(job.status)}`}>
                            {getStatusIcon(job.status)}
                            {job.status}
                         </div>
                      </div>

                      <div className="grid grid-cols-3 gap-6 py-4 border-y border-outline-variant/5">
                         <div>
                            <span className="block text-[8px] font-jetbrains-mono text-neutral-600 uppercase tracking-widest mb-1">Categories</span>
                            <div className="flex flex-wrap gap-1">
                               {job.categories?.map(cat => (
                                 <span key={cat} className="text-[9px] font-jetbrains-mono text-neutral-400 bg-neutral-900 border border-outline-variant/10 px-2 py-0.5 rounded-md uppercase">
                                    {cat}
                                 </span>
                               ))}
                            </div>
                         </div>
                         <div>
                            <span className="block text-[8px] font-jetbrains-mono text-neutral-600 uppercase tracking-widest mb-1">Downloads</span>
                            <span className="text-xl font-jetbrains-mono text-white font-bold">{job.downloaded_videos?.length || 0}</span>
                         </div>
                         <div>
                            <span className="block text-[8px] font-jetbrains-mono text-neutral-600 uppercase tracking-widest mb-1">Job Pulse</span>
                            <span className="text-[10px] font-jetbrains-mono text-neutral-400 capitalize">{job.phase}</span>
                         </div>
                      </div>

                      <div className="flex flex-col gap-2">
                         <p className="text-[11px] font-jetbrains-mono text-neutral-300 leading-relaxed italic">
                            &gt; {job.message}
                         </p>
                         {job.error && (
                            <p className="text-[10px] font-jetbrains-mono text-error/80 bg-error/10 p-3 rounded-xl border border-error/20">
                               [FAULT] {job.error}
                            </p>
                         )}
                      </div>

                      <div className="mt-auto pt-4 flex items-center justify-between">
                         <div className="flex flex-col">
                            <span className="text-[8px] font-jetbrains-mono text-neutral-600 uppercase tracking-widest">Initialization</span>
                            <span className="text-[10px] font-jetbrains-mono text-neutral-500">
                               {job.started_at ? new Date(job.started_at * 1000).toLocaleString() : 'PENDING'}
                            </span>
                         </div>
                         
                         <div className="flex gap-3">
                            {job.batch_id && (
                               <Link href={`/dataset`} className="px-5 py-2.5 bg-tertiary text-black rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-2 hover:opacity-90 transition-opacity">
                                  <Database className="w-3 h-3" /> Explore Batch
                               </Link>
                            )}
                            {job.status === 'completed' && job.report_paths?.consolidated_csv && (
                               <a href={apiUrl(`/dataset/batch/${job.batch_id}/artifact/report_csv`)} className="p-2.5 bg-surface-container-high border border-outline-variant/10 rounded-xl hover:border-primary/40 transition-all group/btn">
                                  <Download className="w-4 h-4 text-neutral-400 group-hover/btn:text-primary" />
                               </a>
                            )}
                            <button className="p-2.5 bg-surface-container-high border border-outline-variant/10 rounded-xl hover:border-primary/40 transition-all group/btn">
                               <ArrowRight className="w-4 h-4 text-neutral-400 group-hover/btn:text-primary" />
                            </button>
                         </div>
                      </div>
                   </div>
                </div>
              ))}
           </div>
         )}
      </div>
    </div>
  );
}
