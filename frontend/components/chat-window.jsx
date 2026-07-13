'use client';

import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, Send, Sparkles, RefreshCw, Layers, ShieldAlert, Cpu } from 'lucide-react';
import MessageBubble from './message-bubble';
import AgentStatusStepper from './agent-status-stepper';

export default function ChatWindow({ streamState, selectedMsg, setSelectedMsg }) {
  const { messages, isLoading, activeNode, askQuestion, clearMessages } = streamState;
  const [query, setQuery] = useState('');
  const messagesEndRef = useRef(null);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, activeNode]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    
    const submittedQuery = query;
    setQuery('');
    askQuestion(submittedQuery);
  };

  const handleSuggestionClick = (text) => {
    setQuery(text);
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-zinc-950 relative">
      
      {/* Dynamic Ambient Background Glows */}
      <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-purple-900/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-pink-900/5 blur-[120px] pointer-events-none" />
      
      {/* Chat Header */}
      <header className="h-16 px-6 border-b border-zinc-800/40 flex items-center justify-between bg-zinc-900/20 backdrop-blur-xl z-10">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 bg-purple-500/10 border border-purple-500/20 rounded-xl flex items-center justify-center">
            <Cpu className="h-4 w-4 text-purple-400 animate-pulse" />
          </div>
          <div>
            <h2 className="text-xs font-bold tracking-tight text-white flex items-center gap-1.5 uppercase font-mono">
              Multi-Agent Gateway
              <span className="h-1.5 w-1.5 rounded-full bg-purple-500 animate-ping" />
            </h2>
            <span className="text-[10px] text-zinc-500 font-medium">FastAPI & LangGraph Streaming Workspace</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <button 
              onClick={clearMessages} 
              className="text-[10px] uppercase font-mono tracking-wider font-semibold text-zinc-400 hover:text-zinc-200 px-3 py-1.5 rounded-lg border border-zinc-800/60 bg-zinc-900/30 hover:bg-zinc-900/70 transition-all duration-300 flex items-center gap-1.5 focus:outline-none cursor-pointer"
            >
              <RefreshCw className="h-3 w-3" />
              Reset Session
            </button>
          )}
        </div>
      </header>

      {/* Message Logs Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 z-10 scrollbar-thin">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center max-w-lg mx-auto text-center space-y-6">
            <div className="relative">
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-purple-600 to-pink-500 blur-xl opacity-20 animate-pulse" />
              <div className="relative h-14 w-14 bg-zinc-900 border border-zinc-800 rounded-3xl flex items-center justify-center shadow-2xl">
                <Sparkles className="h-6 w-6 text-purple-400" />
              </div>
            </div>
            
            <div className="space-y-2">
              <h3 className="text-sm font-bold text-zinc-200 tracking-tight">Enterprise Agent Workspace</h3>
              <p className="text-xs text-zinc-400 leading-relaxed max-w-sm">
                Ask questions about indexed company documents or real-time web context. The multi-agent gateway manages intent-routing, RRF retrieval, and verification.
              </p>
            </div>

            <div className="w-full space-y-2 pt-2">
              <span className="text-[10px] uppercase font-mono text-zinc-500 font-bold tracking-wider block mb-1">Recommended Prompts</span>
              <div className="grid grid-cols-1 gap-2.5 max-w-md mx-auto">
                <button
                  onClick={() => handleSuggestionClick("Summarize the main details and qualifications of the candidate from the resume.")}
                  className="p-3 text-left bg-zinc-900/35 border border-zinc-850 hover:border-purple-500/40 rounded-xl text-xs text-zinc-400 hover:text-zinc-200 transition-all duration-300 backdrop-blur-sm cursor-pointer shadow-sm hover:shadow-purple-500/5 hover:-translate-y-0.5"
                >
                  "Summarize the candidate's qualifications from the resume."
                </button>
                <button
                  onClick={() => handleSuggestionClick("Compare local semantic vector database indexing vs RRF retrieval.")}
                  className="p-3 text-left bg-zinc-900/35 border border-zinc-850 hover:border-purple-500/40 rounded-xl text-xs text-zinc-400 hover:text-zinc-200 transition-all duration-300 backdrop-blur-sm cursor-pointer shadow-sm hover:shadow-purple-500/5 hover:-translate-y-0.5"
                >
                  "Compare local semantic vector indexing vs RRF retrieval."
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6 max-w-3xl mx-auto w-full">
            {messages.map((msg, i) => (
              <MessageBubble 
                key={i} 
                msg={msg} 
                onInspect={() => setSelectedMsg(msg)}
                isActive={selectedMsg === msg}
              />
            ))}
          </div>
        )}

        {/* Active Processing Indicator */}
        {isLoading && (
          <div className="max-w-3xl mx-auto w-full pt-2">
            <AgentStatusStepper activeNode={activeNode} />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Floating Glassmorphic Input Text Form */}
      <div className="p-6 border-t border-zinc-800/40 bg-zinc-950/80 backdrop-blur-xl z-10">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto relative flex items-center group">
          
          {/* Neon Border Glow */}
          <div className="absolute inset-0 -m-[1px] rounded-2xl bg-gradient-to-r from-purple-500/10 via-pink-500/5 to-purple-500/10 opacity-0 group-focus-within:opacity-100 transition-all duration-500 blur-sm pointer-events-none" />
          
          <input
            type="text"
            placeholder="Query details or search indexed knowledge workspace..."
            className="w-full bg-zinc-900/50 border border-zinc-800/80 focus:border-purple-500/60 rounded-2xl pl-5 pr-14 py-4 text-xs focus:outline-none text-zinc-200 placeholder-zinc-500 transition-all duration-300 shadow-inner backdrop-blur-sm font-sans"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isLoading}
          />
          <button
            type="submit"
            className={`absolute right-3 p-2 rounded-xl transition-all duration-300 cursor-pointer focus:outline-none ${
              query.trim() && !isLoading
                ? 'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-500/20 hover:scale-105'
                : 'bg-zinc-800/40 text-zinc-600 cursor-not-allowed border border-zinc-850'
            }`}
            disabled={!query.trim() || isLoading}
          >
            <Send className="h-3.5 w-3.5" />
          </button>
        </form>
        <div className="max-w-3xl mx-auto flex items-center justify-between mt-3 px-1.5 text-[9px] text-zinc-500 font-mono">
          <span className="flex items-center gap-1">
            <Layers className="h-3 w-3 text-purple-400" />
            RAG context: Reciprocal Rank Fusion (RRF) & Reranking
          </span>
          <span className="flex items-center gap-1">
            <ShieldAlert className="h-3 w-3 text-pink-400" />
            Faithfulness Audit Guardrail Active
          </span>
        </div>
      </div>

    </div>
  );
}
