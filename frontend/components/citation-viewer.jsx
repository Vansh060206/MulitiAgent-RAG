'use client';

import React from 'react';
import { BookOpen, FileText, ExternalLink } from 'lucide-react';

export default function CitationViewer({ sources }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="space-y-3 pt-4 border-t border-zinc-800/80">
      <h4 className="text-[9px] font-bold uppercase tracking-widest text-zinc-500 flex items-center gap-1.5 font-mono">
        <BookOpen className="h-3 w-3" />
        Retrieved Source Passages ({sources.length})
      </h4>
      <div className="grid grid-cols-1 gap-3">
        {sources.map((src, idx) => (
          <div 
            key={idx} 
            className="p-3 bg-zinc-900/10 rounded-xl border border-zinc-800/60 hover:border-zinc-700/60 hover:bg-zinc-900/25 transition-all duration-300 backdrop-blur-sm shadow-sm hover:shadow-purple-500/[0.02]"
          >
            <div className="flex items-center justify-between text-[9px] font-bold font-mono text-zinc-400 mb-2">
              <span className="flex items-center gap-1.5 text-zinc-300 truncate max-w-[80%]">
                <FileText className="h-3.5 w-3.5 text-purple-400 flex-shrink-0" />
                <span className="truncate" title={src.doc_name}>{src.doc_name}</span>
              </span>
              {src.url ? (
                <a 
                  href={src.url} 
                  target="_blank" 
                  rel="noreferrer" 
                  className="flex items-center gap-0.5 text-purple-400 hover:text-purple-300 transition-colors"
                >
                  Visit Link
                  <ExternalLink className="h-2 w-2" />
                </a>
              ) : (
                <span className="text-[8px] bg-zinc-900 border border-zinc-850 text-zinc-400 px-1.5 py-0.5 rounded font-semibold font-mono">
                  Page {src.page || src.page_number || 'N/A'}
                </span>
              )}
            </div>
            <p className="text-[11px] text-zinc-450 italic leading-relaxed pl-2.5 border-l-2 border-purple-500/20 whitespace-pre-wrap font-sans">
              "{src.content}"
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
