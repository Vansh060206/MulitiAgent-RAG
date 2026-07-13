'use client';

import React from 'react';
import { Loader2, ArrowRight } from 'lucide-react';

export default function AgentStatusStepper({ activeNode }) {
  const steps = [
    { id: 'router', label: 'Router', color: 'text-purple-400 border-purple-500/30 bg-purple-500/10 shadow-purple-500/5' },
    { id: 'retrieve', label: 'Retrieve', color: 'text-blue-400 border-blue-500/30 bg-blue-500/10 shadow-blue-500/5' },
    { id: 'research', label: 'Research', color: 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10 shadow-cyan-500/5' },
    { id: 'generate', label: 'Generate', color: 'text-pink-400 border-pink-500/30 bg-pink-500/10 shadow-pink-500/5' },
    { id: 'verify', label: 'Verify', color: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10 shadow-emerald-500/5' }
  ];

  return (
    <div className="max-w-3xl mx-auto flex items-center gap-4 text-xs bg-zinc-900/20 border border-zinc-800/80 rounded-2xl p-4 shadow-xl backdrop-blur-sm animate-fadeIn">
      
      <div className="h-8 w-8 rounded-xl bg-purple-500/5 border border-purple-500/20 flex items-center justify-center flex-shrink-0">
        <Loader2 className="h-3.5 w-3.5 text-purple-400 animate-spin" />
      </div>
      
      <div className="flex-1 space-y-1.5 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-tight">Graph Pipeline Processing</span>
          <span className="h-1.5 w-1.5 rounded-full bg-purple-500 animate-ping" />
        </div>
        
        {/* Stepper Pipeline Flow */}
        <div className="flex flex-wrap items-center gap-1.5">
          {steps.map((step, idx) => {
            const isActive = activeNode === step.id;
            return (
              <React.Fragment key={step.id}>
                <span
                  className={`text-[8px] font-bold font-mono uppercase px-2 py-0.5 rounded border transition-all duration-500 shadow-sm ${
                    isActive 
                      ? `${step.color} scale-105 border-opacity-100` 
                      : 'text-zinc-650 border-zinc-900 bg-zinc-950/20 opacity-40'
                  }`}
                >
                  {step.label}
                </span>
                {idx < steps.length - 1 && (
                  <ArrowRight className={`h-3 w-3 ${isActive ? 'text-purple-500 animate-pulse' : 'text-zinc-800'} flex-shrink-0 opacity-40`} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
      
    </div>
  );
}
