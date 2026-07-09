'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  Upload, 
  MessageSquare, 
  Send, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  ChevronRight, 
  ChevronDown, 
  Clock, 
  Activity, 
  Compass, 
  ShieldAlert, 
  RefreshCw, 
  ExternalLink,
  BookOpen
} from 'lucide-react';

export default function Home() {
  // Input and Chat States
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeNode, setActiveNode] = useState(null); // router, retrieve, research, generate, verify

  // Ingestion States
  const [dragActive, setDragActive] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle, uploading, parsing, chunking, indexing, success, error
  const [uploadError, setUploadError] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);

  // Active Inspect Details
  const [expandedTrace, setExpandedTrace] = useState({}); // messageIndex -> boolean

  // Backend Status Banner
  const [backendOnline, setBackendOnline] = useState(true);

  // Scroll Anchor
  const messagesEndRef = useRef(null);

  // Load uploaded files list from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('multiagent_rag_files');
    if (saved) {
      try {
        setUploadedFiles(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to parse saved files history', e);
      }
    }
    
    // Check backend health
    checkBackendHealth();
  }, []);

  // Save uploaded files to localStorage when changed
  const saveFilesToHistory = (newList) => {
    setUploadedFiles(newList);
    localStorage.setItem('multiagent_rag_files', JSON.stringify(newList));
  };

  const checkBackendHealth = async () => {
    try {
      const res = await fetch('http://localhost:8000/');
      if (res.ok) {
        setBackendOnline(true);
      } else {
        setBackendOnline(false);
      }
    } catch (e) {
      setBackendOnline(false);
    }
  };

  // Scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, activeNode]);

  // Handle Drag & Drop events
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === "application/pdf") {
        triggerUpload(file);
      } else {
        setUploadStatus('error');
        setUploadError('Invalid file type. Only PDF documents are supported.');
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.name.endsWith('.pdf')) {
        triggerUpload(file);
      } else {
        setUploadStatus('error');
        setUploadError('Invalid file type. Only PDF documents are supported.');
      }
    }
  };

  // Upload file to backend
  const triggerUpload = async (file) => {
    setUploadFile(file);
    setUploadStatus('uploading');
    setUploadError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Step-by-step simulated UI status updates for indexing pipeline
      setTimeout(() => setUploadStatus('parsing'), 800);
      setTimeout(() => setUploadStatus('chunking'), 2000);
      setTimeout(() => setUploadStatus('indexing'), 3500);

      const response = await fetch('http://localhost:8000/api/ingest/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errDetail = await response.json();
        throw new Error(errDetail.detail || 'Failed to ingest file.');
      }

      const result = await response.json();
      setUploadStatus('success');
      setBackendOnline(true);

      // Add to uploaded history
      const newFile = {
        name: file.name,
        size: (file.size / (1024 * 1024)).toFixed(2) + ' MB',
        pages: result.pages_extracted,
        chunks: result.chunks_created,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      saveFilesToHistory([newFile, ...uploadedFiles]);

      // Reset upload state after 3s
      setTimeout(() => {
        setUploadStatus('idle');
        setUploadFile(null);
      }, 4000);

    } catch (error) {
      setUploadStatus('error');
      setUploadError(error.message || 'Server connection failed.');
    }
  };

  // Submit Query to Multi-Agent RAG
  const handleQuerySubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userText = query;
    setQuery('');
    
    // Add user message to state
    const updatedMessages = [
      ...messages,
      { role: 'user', text: userText, timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
    ];
    setMessages(updatedMessages);
    setIsLoading(true);
    setActiveNode('router');

    try {
      // Direct call to the /api/chat/ask endpoint
      const response = await fetch('http://localhost:8000/api/chat/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userText, limit: 5 })
      });

      if (!response.ok) {
        const errDetail = await response.json();
        throw new Error(errDetail.detail || 'Agent graph execution encountered an error.');
      }

      const data = await response.json();
      setBackendOnline(true);

      // Add assistant response to state
      setMessages([
        ...updatedMessages,
        {
          role: 'assistant',
          text: data.answer || "No response generated.",
          trace: data.trace || [],
          sources: data.sources || [],
          verificationScore: data.verification_score,
          verificationReasoning: data.verification_reasoning,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);

    } catch (error) {
      setMessages([
        ...updatedMessages,
        {
          role: 'assistant',
          text: `Error: ${error.message}. Make sure your backend server is running and the Gemini API key is configured correctly.`,
          error: true,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsLoading(false);
      setActiveNode(null);
    }
  };

  const toggleTrace = (index) => {
    setExpandedTrace(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  // Helper to color-code verification scores
  const getVerificationScoreStyle = (score) => {
    if (score >= 0.8) return { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400', label: 'Highly Faithful' };
    if (score >= 0.6) return { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400', label: 'Marginal Hallucinations' };
    return { bg: 'bg-rose-500/10', border: 'border-rose-500/30', text: 'text-rose-400', label: 'Unfaithful / Hallucinated' };
  };

  // Helper to style nodes in the trace
  const getNodeColor = (node) => {
    switch (node) {
      case 'router': return 'text-purple-400 border-purple-500/30 bg-purple-500/10';
      case 'retrieve': return 'text-blue-400 border-blue-500/30 bg-blue-500/10';
      case 'research': return 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10';
      case 'generate': return 'text-pink-400 border-pink-500/30 bg-pink-500/10';
      case 'verify': return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
      default: return 'text-zinc-400 border-zinc-500/30 bg-zinc-500/10';
    }
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-zinc-950 text-zinc-100 font-sans antialiased">
      
      {/* 1. SIDEBAR (Ingestion Panel) */}
      <aside className="w-80 flex flex-col border-r border-zinc-800 bg-zinc-900/60 backdrop-blur-md">
        
        {/* Logo and Brand */}
        <div className="p-5 border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-tr from-purple-600 to-pink-500 rounded-xl shadow-lg shadow-purple-500/20">
              <Activity className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-sm tracking-tight text-white">Agentic RAG</h1>
              <span className="text-[10px] text-zinc-400 uppercase tracking-widest font-mono">Enterprise v1.0</span>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <span className={`h-2.5 w-2.5 rounded-full ${backendOnline ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            <span className="text-[10px] text-zinc-500 font-medium">{backendOnline ? 'Online' : 'Offline'}</span>
          </div>
        </div>

        {/* Upload Container */}
        <div className="p-5 flex-1 overflow-y-auto space-y-6">
          
          <div className="space-y-2">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Ingest Document</h2>
            <p className="text-xs text-zinc-500 leading-relaxed">
              Upload local PDF guidelines, policies, or financial reports to build the shared vector index.
            </p>
          </div>

          {/* Drag & Drop Zone */}
          <div
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            className={`relative group border-2 border-dashed rounded-xl p-5 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 ${
              dragActive 
                ? 'border-purple-500 bg-purple-500/5' 
                : 'border-zinc-800 hover:border-zinc-700 bg-zinc-950/40 hover:bg-zinc-950/60'
            }`}
          >
            <input
              type="file"
              id="file-upload"
              accept=".pdf"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              onChange={handleFileChange}
              disabled={uploadStatus !== 'idle' && uploadStatus !== 'error'}
            />
            
            {uploadStatus === 'idle' && (
              <>
                <div className="p-3 bg-zinc-900 rounded-lg border border-zinc-800 text-zinc-400 group-hover:text-zinc-300 transition-colors mb-3">
                  <Upload className="h-5 w-5" />
                </div>
                <span className="text-xs font-medium text-zinc-300 group-hover:text-zinc-200">Drag & drop your PDF here</span>
                <span className="text-[10px] text-zinc-500 mt-1">or click to browse local files</span>
              </>
            )}

            {uploadStatus !== 'idle' && uploadStatus !== 'success' && uploadStatus !== 'error' && (
              <div className="flex flex-col items-center py-2">
                <Loader2 className="h-7 w-7 text-purple-500 animate-spin mb-3" />
                <span className="text-xs font-semibold text-zinc-300">
                  {uploadStatus === 'uploading' && 'Uploading document streams...'}
                  {uploadStatus === 'parsing' && 'Extracting text with PyPDF...'}
                  {uploadStatus === 'chunking' && 'Structuring overlap chunks...'}
                  {uploadStatus === 'indexing' && 'Writing vectors to Qdrant...'}
                </span>
                <span className="text-[10px] text-zinc-500 mt-1.5">Please wait, compiling pipeline</span>
              </div>
            )}

            {uploadStatus === 'success' && (
              <div className="flex flex-col items-center py-2 text-emerald-400">
                <CheckCircle2 className="h-8 w-8 mb-2" />
                <span className="text-xs font-semibold text-zinc-200">Ingestion Succeeded!</span>
                <span className="text-[9px] text-zinc-400 mt-1">{uploadFile?.name}</span>
              </div>
            )}

            {uploadStatus === 'error' && (
              <div className="flex flex-col items-center py-2 text-rose-400">
                <AlertCircle className="h-8 w-8 mb-2" />
                <span className="text-xs font-semibold text-zinc-200">Ingestion Failed</span>
                <p className="text-[10px] text-zinc-500 mt-2 px-3 text-center line-clamp-2 leading-relaxed">
                  {uploadError}
                </p>
                <span className="text-[10px] underline mt-3 text-purple-400 font-semibold group-hover:text-purple-300">Try again</span>
              </div>
            )}
          </div>

          {/* Ingested Files List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Active Knowledge Index</h2>
              <span className="text-[10px] bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded-full font-mono font-semibold">
                {uploadedFiles.length}
              </span>
            </div>
            
            {uploadedFiles.length === 0 ? (
              <div className="rounded-xl border border-zinc-800/60 p-4 text-center bg-zinc-950/20">
                <p className="text-[11px] text-zinc-500 leading-normal">
                  No documents index found. The assistant will fall back to general conversation or web search.
                </p>
              </div>
            ) : (
              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {uploadedFiles.map((file, i) => (
                  <div key={i} className="flex gap-3 p-3 bg-zinc-950/40 rounded-xl border border-zinc-800/80 hover:border-zinc-800 hover:bg-zinc-950/60 transition-all duration-200">
                    <FileText className="h-4 w-4 text-purple-400 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-zinc-200 truncate" title={file.name}>{file.name}</p>
                      <div className="flex items-center gap-1.5 mt-1 text-[9px] text-zinc-500 font-mono">
                        <span>{file.size}</span>
                        <span>•</span>
                        <span>{file.chunks} chunks</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          
        </div>

        {/* Bottom Banner */}
        {!backendOnline && (
          <div className="p-3 bg-rose-500/10 border-t border-rose-500/20 text-rose-400 text-center flex items-center justify-center gap-2">
            <ShieldAlert className="h-4 w-4" />
            <span className="text-[10px] font-semibold">Backend Unreachable (Port 8000)</span>
          </div>
        )}
      </aside>

      {/* 2. MAIN CHAT & INSPECTION VIEW */}
      <section className="flex-1 flex flex-col overflow-hidden bg-zinc-950">
        
        {/* Chat Header */}
        <header className="h-16 px-6 border-b border-zinc-800/60 flex items-center justify-between bg-zinc-900/10 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <MessageSquare className="h-5 w-5 text-purple-400" />
            <div>
              <h2 className="text-xs font-semibold tracking-tight text-white">Multi-Agent Gateway</h2>
              <span className="text-[10px] text-zinc-500">FastAPI & LangGraph Orchestration Workspace</span>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button 
              onClick={() => {
                setMessages([]);
                setQuery('');
              }} 
              className="text-xs text-zinc-400 hover:text-zinc-200 px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900/80 transition-all flex items-center gap-1.5"
            >
              <RefreshCw className="h-3 w-3" />
              Clear Conversation
            </button>
          </div>
        </header>

        {/* Message Logs Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center max-w-lg mx-auto text-center space-y-5">
              <div className="h-12 w-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg shadow-purple-500/20">
                <Compass className="h-6 w-6 text-white" />
              </div>
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-zinc-200">Start an Enterprise Inquiry</h3>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Ask questions about proprietary documents (financial reports, operations manuals) or real-world events. The multi-agent coordinator will decide whether to look up vectors in Qdrant, crawl the web, or reply directly.
                </p>
              </div>
              <div className="w-full grid grid-cols-2 gap-3 max-w-md pt-2">
                <button
                  onClick={() => setQuery("How much money did we make in total Q3 2025?")}
                  className="p-3 text-left bg-zinc-900/40 border border-zinc-800/80 hover:border-zinc-700/80 rounded-xl text-xs text-zinc-400 hover:text-zinc-200 transition-all"
                >
                  "How much money did we make in Q3 2025?"
                </button>
                <button
                  onClick={() => setQuery("What are the main features of LangGraph?")}
                  className="p-3 text-left bg-zinc-900/40 border border-zinc-800/80 hover:border-zinc-700/80 rounded-xl text-xs text-zinc-400 hover:text-zinc-200 transition-all"
                >
                  "What are the main features of LangGraph?"
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-6 max-w-4xl mx-auto">
              {messages.map((msg, i) => (
                <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  
                  {/* Bubble content */}
                  <div className={`max-w-3xl rounded-2xl px-5 py-4 text-sm leading-relaxed shadow-md ${
                    msg.role === 'user'
                      ? 'bg-zinc-800 border border-zinc-700/60 text-zinc-100 rounded-br-none'
                      : msg.error
                        ? 'bg-rose-500/10 border border-rose-500/20 text-rose-200 rounded-bl-none'
                        : 'bg-zinc-900/80 border border-zinc-800 text-zinc-200 rounded-bl-none'
                  }`}>
                    {msg.text}
                  </div>

                  {/* Bubble timestamp & metadata toggles */}
                  <div className="flex items-center gap-3 mt-1.5 px-1 text-[10px] text-zinc-500">
                    <span>{msg.timestamp}</span>
                    {msg.role === 'assistant' && !msg.error && (
                      <>
                        <span>•</span>
                        <button 
                          onClick={() => toggleTrace(i)} 
                          className="flex items-center gap-1 text-purple-400 hover:text-purple-300 font-semibold cursor-pointer"
                        >
                          <Activity className="h-3 w-3" />
                          {expandedTrace[i] ? 'Hide Thought Trace' : 'Inspect Thought Trace'}
                          {expandedTrace[i] ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3 animate-pulse" />}
                        </button>
                      </>
                    )}
                  </div>

                  {/* Extended Inspection Panel (Trace & Sources) */}
                  {msg.role === 'assistant' && expandedTrace[i] && (
                    <div className="w-full max-w-3xl mt-3 p-5 rounded-2xl border border-zinc-800/80 bg-zinc-950/60 backdrop-blur-sm shadow-inner space-y-5 animate-fadeIn">
                      
                      {/* Faithfulness Score Banner */}
                      {msg.verificationScore !== undefined && (
                        <div className={`p-3 rounded-xl border flex items-center justify-between gap-4 ${getVerificationScoreStyle(msg.verificationScore).bg} ${getVerificationScoreStyle(msg.verificationScore).border}`}>
                          <div className="flex items-center gap-2">
                            <ShieldAlert className={`h-4.5 w-4.5 ${getVerificationScoreStyle(msg.verificationScore).text}`} />
                            <div>
                              <span className="text-xs font-semibold text-zinc-200">Verifier Hallucination Guardrail</span>
                              <p className="text-[10px] text-zinc-500 mt-0.5 leading-normal">
                                {msg.verificationReasoning || 'Faithfulness evaluated correctly against referenced context.'}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <span className={`text-xs font-bold font-mono ${getVerificationScoreStyle(msg.verificationScore).text}`}>
                              {(msg.verificationScore * 100).toFixed(0)}%
                            </span>
                            <span className="block text-[8px] text-zinc-400 uppercase tracking-wider font-semibold">
                              {getVerificationScoreStyle(msg.verificationScore).label}
                            </span>
                          </div>
                        </div>
                      )}

                      {/* Stepper Timeline Trace */}
                      {msg.trace && msg.trace.length > 0 && (
                        <div className="space-y-3">
                          <h4 className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1.5">
                            <Clock className="h-3.5 w-3.5" />
                            Agent Workflow Nodes Trace
                          </h4>
                          
                          <div className="relative border-l border-zinc-800 pl-4 space-y-4 ml-1.5 py-1">
                            {msg.trace.map((step, idx) => (
                              <div key={idx} className="relative">
                                {/* Bullet indicator */}
                                <div className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-zinc-800 border-2 border-zinc-950 shadow-sm" />
                                
                                <div className="space-y-1">
                                  <div className="flex items-center gap-2">
                                    <span className={`text-[9px] px-2 py-0.5 rounded-md border font-semibold font-mono tracking-tight uppercase ${getNodeColor(step.node)}`}>
                                      {step.node}
                                    </span>
                                  </div>
                                  <p className="text-[11px] text-zinc-400 font-medium leading-relaxed">
                                    {step.details}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Sources Panel */}
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="space-y-2 pt-2 border-t border-zinc-900">
                          <h4 className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1.5">
                            <BookOpen className="h-3.5 w-3.5" />
                            Context Passages Retrieved ({msg.sources.length})
                          </h4>
                          <div className="grid grid-cols-1 gap-2.5">
                            {msg.sources.map((src, idx) => (
                              <div key={idx} className="p-3 bg-zinc-900/30 rounded-xl border border-zinc-800/50 hover:border-zinc-800 transition-colors">
                                <div className="flex items-center justify-between text-[10px] font-semibold text-zinc-400 mb-1.5">
                                  <span className="flex items-center gap-1 text-zinc-300">
                                    <FileText className="h-3.5 w-3.5 text-zinc-500" />
                                    {src.doc_name}
                                  </span>
                                  {src.url ? (
                                    <a 
                                      href={src.url} 
                                      target="_blank" 
                                      rel="noreferrer" 
                                      className="flex items-center gap-0.5 text-purple-400 hover:underline"
                                    >
                                      Visit Source
                                      <ExternalLink className="h-2.5 w-2.5" />
                                    </a>
                                  ) : (
                                    <span className="font-mono text-[9px] bg-zinc-800 text-zinc-500 px-1.5 py-0.5 rounded">
                                      Page {src.page}
                                    </span>
                                  )}
                                </div>
                                <p className="text-xs text-zinc-500 italic leading-relaxed pl-1.5 border-l border-purple-500/20">
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
              ))}
            </div>
          )}

          {/* Active Processing Indicator */}
          {isLoading && (
            <div className="max-w-4xl mx-auto flex items-start gap-4 text-sm bg-zinc-900/30 border border-zinc-800/40 rounded-2xl p-5 shadow-inner">
              <Loader2 className="h-5 w-5 text-purple-500 animate-spin flex-shrink-0 mt-0.5" />
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-zinc-200">Workflow execution running...</span>
                  <span className="text-[10px] text-zinc-500 font-mono">Active Node: {activeNode || 'planning'}</span>
                </div>
                <div className="flex gap-2">
                  <span className={`text-[8px] font-semibold font-mono uppercase px-1.5 py-0.5 rounded border ${
                    activeNode === 'router' ? 'text-purple-400 border-purple-500 bg-purple-500/10' : 'text-zinc-600 border-zinc-800 bg-transparent'
                  }`}>
                    Router
                  </span>
                  <span className={`text-[8px] font-semibold font-mono uppercase px-1.5 py-0.5 rounded border ${
                    activeNode === 'retrieve' ? 'text-blue-400 border-blue-500 bg-blue-500/10' : 'text-zinc-600 border-zinc-800 bg-transparent'
                  }`}>
                    Retrieve
                  </span>
                  <span className={`text-[8px] font-semibold font-mono uppercase px-1.5 py-0.5 rounded border ${
                    activeNode === 'research' ? 'text-cyan-400 border-cyan-500 bg-cyan-500/10' : 'text-zinc-600 border-zinc-800 bg-transparent'
                  }`}>
                    Research
                  </span>
                  <span className={`text-[8px] font-semibold font-mono uppercase px-1.5 py-0.5 rounded border ${
                    activeNode === 'generate' ? 'text-pink-400 border-pink-500 bg-pink-500/10' : 'text-zinc-600 border-zinc-800 bg-transparent'
                  }`}>
                    Generate
                  </span>
                  <span className={`text-[8px] font-semibold font-mono uppercase px-1.5 py-0.5 rounded border ${
                    activeNode === 'verify' ? 'text-emerald-400 border-emerald-500 bg-emerald-500/10' : 'text-zinc-600 border-zinc-800 bg-transparent'
                  }`}>
                    Verify
                  </span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Text Form */}
        <div className="p-6 border-t border-zinc-800/60 bg-zinc-900/10 backdrop-blur-md">
          <form onSubmit={handleQuerySubmit} className="max-w-4xl mx-auto relative flex items-center">
            <input
              type="text"
              placeholder="Ask a question about the indexed workspace..."
              className="w-full bg-zinc-900 border border-zinc-800/80 focus:border-purple-500/80 hover:border-zinc-700/80 rounded-2xl pl-5 pr-14 py-4 text-sm focus:outline-none text-zinc-100 placeholder-zinc-500 transition-all shadow-inner"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isLoading}
            />
            <button
              type="submit"
              className={`absolute right-3.5 p-2 rounded-xl transition-all cursor-pointer ${
                query.trim() && !isLoading
                  ? 'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-500/20'
                  : 'bg-zinc-800 text-zinc-500 cursor-not-allowed'
              }`}
              disabled={!query.trim() || isLoading}
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
          <div className="max-w-4xl mx-auto flex items-center justify-between mt-2.5 px-1.5 text-[9px] text-zinc-600 font-mono font-medium">
            <span>Powered by LangGraph & Google Gemini API</span>
            <span>RAG context: Reciprocal Rank Fusion (RRF)</span>
          </div>
        </div>

      </section>

      {/* Style Animations injecting */}
      <style jsx global>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(4px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
      `}</style>

    </div>
  );
}
