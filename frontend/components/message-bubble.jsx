'use client';

import React from 'react';
import { Activity } from 'lucide-react';

export default function MessageBubble({ msg, onInspect, isActive }) {
  const isUser = msg.role === 'user';
  
  return (
    <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} w-full animate-fadeIn`}>
      {/* Text Bubble */}
      <div className={`max-w-xl rounded-2xl px-5 py-3.5 text-xs leading-relaxed shadow-sm whitespace-pre-wrap font-sans ${
        isUser
          ? 'bg-zinc-800 border border-zinc-700/55 text-zinc-100 rounded-br-none'
          : msg.error
            ? 'bg-rose-950/20 border border-rose-500/20 text-rose-250 rounded-bl-none'
            : 'bg-zinc-900/60 border border-zinc-800/80 text-zinc-200 rounded-bl-none backdrop-blur-sm'
      }`}>
        {msg.text}
      </div>

      {/* Message Metadata & Inspection trigger */}
      <div className="flex items-center gap-2.5 mt-1.5 px-1.5 text-[9px] text-zinc-500 font-mono">
        <span>{msg.timestamp}</span>
        {!isUser && !msg.error && (
          <>
            <span>•</span>
            <button 
              onClick={onInspect} 
              className={`flex items-center gap-1 font-bold cursor-pointer focus:outline-none transition-all duration-200 ${
                isActive 
                  ? 'text-purple-400' 
                  : 'text-zinc-500 hover:text-purple-400'
              }`}
            >
              <Activity className="h-3 w-3" />
              {isActive ? 'Inspecting Telemetry' : 'Inspect Telemetry'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
