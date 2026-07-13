'use client';

import React from 'react';
import { Clock, ShieldCheck, ShieldAlert, BookOpen, FileText, ExternalLink, Cpu } from 'lucide-react';
import AgentStatusStepper from './agent-status-stepper';

export default function TelemetryPanel({ activeNode, isLoading, selectedMsg }) {
  const getScoreStyle = (score) => {
    if (score >= 0.8) return { text: 'text-emerald-400', border: 'border-emerald-500/20', bg: 'bg-emerald-500/5', label: 'Faithful Context' };
    if (score >= 0.6) return { text: 'text-amber-400', border: 'border-amber-500/20', bg: 'bg-amber-500/5', label: 'Possible Hallucination' };
    return { text: 'text-rose-400', border: 'border-rose-500/20', bg: 'bg-rose-500/5', label: 'Unfaithful Output' };
  };

  const getNodeColor = (node) => {
    switch (node) {
      case 'router': return 'text-purple-400 border-purple-500/20 bg-purple-500/5';
      case 'retrieve': return 'text-blue-400 border-blue-500/20 bg-blue-500/5';
      case 'research': return 'text-cyan-400 border-cyan-500/20 bg-cyan-500/5';
      case 'generate': return 'text-pink-400 border-pink-500/20 bg-pink-500/5';
      case 'verify': return 'text-emerald-400 border-emerald-500/20 bg-emerald-500/5';
      default: return 'text-zinc-400 border-zinc-500/20 bg-zinc-500/5';
    }
  };

  return (
    <aside className="w-80 flex flex-col border-l border-zinc-800/60 bg-zinc-900/10 backdrop-blur-xl h-full overflow-hidden flex-shrink-0">
      
      {/* Panel Header */}
      <div className="h-16 border-b border-zinc-800/60 px-5 flex items-center justify-between flex-shrink-0 bg-zinc-900/20">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-purple-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-300">Live AI Telemetry</h3>
        </div>
        {isLoading && (
          <span className="text-[9px] bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded-full font-semibold animate-pulse">
            Active Run
          </span>
        )}
      </div>

      {/* Panel Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6 scrollbar-thin">
        
        {/* 1. Live Flow Pipeline (always shown if loading or if we have an active node) */}
        {(isLoading || activeNode) ? (
          <div className="space-y-3">
            <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Active Stepper</h4>
            <AgentStatusStepper activeNode={activeNode} />
          </div>
        ) : null}

        {/* If no message is selected and we aren't loading, show empty helper */}
        {!selectedMsg && !isLoading ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-3 opacity-60">
            <Clock className="h-6 w-6 text-zinc-650" />
            <div>
              <p className="text-xs font-semibold text-zinc-400">Telemetry Monitor Idle</p>
              <p className="text-[10px] text-zinc-500 mt-1 leading-normal">
                Submit an inquiry or click "Inspect Details" on an assistant reply to view execution timelines and sources.
              </p>
            </div>
          </div>
        ) : null}

        {/* Selected Message Telemetry Details */}
        {selectedMsg && !isLoading && (
          <div className="space-y-6 animate-fadeIn">
            
            {/* 2. Hallucination Guardrail Gauge */}
            {selectedMsg.verificationScore !== undefined && selectedMsg.verificationScore !== null && (
              <div className="space-y-3">
                <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Faithfulness Audit</h4>
                
                <div className={`p-4 rounded-xl border ${getScoreStyle(selectedMsg.verificationScore).bg} ${getScoreStyle(selectedMsg.verificationScore).border} space-y-3`}>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-zinc-200">
                      {getScoreStyle(selectedMsg.verificationScore).label}
                    </span>
                    <span className={`text-sm font-black font-mono ${getScoreStyle(selectedMsg.verificationScore).text}`}>
                      {(selectedMsg.verificationScore * 100).toFixed(0)}%
                    </span>
                  </div>
                  
                  {/* Gauge Bar */}
                  <div className="h-1.5 w-full bg-zinc-950 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all duration-1000 ${
                        selectedMsg.verificationScore >= 0.8 ? 'bg-emerald-500' : selectedMsg.verificationScore >= 0.6 ? 'bg-amber-500' : 'bg-rose-500'
                      }`}
                      style={{ width: `${selectedMsg.verificationScore * 100}%` }}
                    />
                  </div>
                  
                  <p className="text-[10px] text-zinc-400 leading-relaxed font-sans">
                    {selectedMsg.verificationReasoning || 'Faithfulness evaluated correctly against referenced context.'}
                  </p>
                </div>
              </div>
            )}

            {/* 3. Execution Node Timeline */}
            {selectedMsg.trace && selectedMsg.trace.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Execution Path</h4>
                <div className="relative border-l border-zinc-800 pl-4 space-y-4 ml-1.5 py-1">
                  {selectedMsg.trace.map((step, idx) => (
                    <div key={idx} className="relative group">
                      <div className="absolute -left-[20.5px] top-1.5 h-1.5 w-1.5 rounded-full bg-zinc-800 border border-zinc-950 group-hover:bg-purple-500 group-hover:scale-125 transition-all duration-300" />
                      <div className="space-y-1">
                        <div>
                          <span className={`text-[8px] px-1.5 py-0.5 rounded border font-bold font-mono uppercase ${getNodeColor(step.node)}`}>
                            {step.node}
                          </span>
                        </div>
                        <p className="text-[10px] text-zinc-400 leading-normal">
                          {step.details}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 4. Retrieved Passages */}
            {selectedMsg.sources && selectedMsg.sources.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Retrieved Passages</h4>
                <div className="space-y-3">
                  {selectedMsg.sources.map((src, idx) => (
                    <div key={idx} className="p-3 bg-zinc-900/25 border border-zinc-850 rounded-xl space-y-2 shadow-sm">
                      <div className="flex items-center justify-between text-[9px] font-bold text-zinc-450">
                        <span className="flex items-center gap-1.5 truncate max-w-[80%] text-zinc-350">
                          <FileText className="h-3 w-3 text-purple-400 flex-shrink-0" />
                          <span className="truncate" title={src.doc_name}>{src.doc_name}</span>
                        </span>
                        {src.url ? (
                          <a 
                            href={src.url} 
                            target="_blank" 
                            rel="noreferrer" 
                            className="flex items-center gap-0.5 text-purple-400 hover:text-purple-300 transition-colors"
                          >
                            Link
                            <ExternalLink className="h-2 w-2" />
                          </a>
                        ) : (
                          <span className="bg-zinc-900 border border-zinc-850 text-zinc-500 px-1 rounded text-[7px] font-mono">
                            Pg {src.page || src.page_number || 'N/A'}
                          </span>
                        )}
                      </div>
                      <p className="text-[10px] text-zinc-450 italic leading-relaxed pl-2 border-l-2 border-purple-500/10 font-sans">
                        "{src.content}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        )}
        
      </div>
    </aside>
  );
}
