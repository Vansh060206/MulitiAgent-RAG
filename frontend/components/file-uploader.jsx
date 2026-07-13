'use client';

import React, { useState, useEffect } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

export default function FileUploader({ onUploadSuccess, backendOnline }) {
  const [dragActive, setDragActive] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle, uploading, parsing, chunking, indexing, success, error
  const [uploadError, setUploadError] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);

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
  }, []);

  const saveFilesToHistory = (newList) => {
    setUploadedFiles(newList);
    localStorage.setItem('multiagent_rag_files', JSON.stringify(newList));
    if (onUploadSuccess) {
      onUploadSuccess(newList);
    }
  };

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

  const triggerUpload = async (file) => {
    setUploadFile(file);
    setUploadStatus('uploading');
    setUploadError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Step-by-step simulated UI status updates for indexing pipeline
      const p1 = setTimeout(() => setUploadStatus('parsing'), 800);
      const p2 = setTimeout(() => setUploadStatus('chunking'), 2000);
      const p3 = setTimeout(() => setUploadStatus('indexing'), 3500);

      const response = await fetch('http://127.0.0.1:8000/api/ingest/upload', {
        method: 'POST',
        body: formData,
      });

      clearTimeout(p1);
      clearTimeout(p2);
      clearTimeout(p3);

      if (!response.ok) {
        let errMessage = 'Failed to ingest file.';
        try {
          const errDetail = await response.json();
          errMessage = errDetail.detail || errMessage;
        } catch (e) {
          try {
            errMessage = await response.text();
          } catch (_) {}
        }
        throw new Error(errMessage);
      }

      const result = await response.json();
      setUploadStatus('success');

      const newFile = {
        name: file.name,
        size: (file.size / (1024 * 1024)).toFixed(2) + ' MB',
        pages: result.pages_extracted,
        chunks: result.chunks_created,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      const updatedHistory = [newFile, ...uploadedFiles];
      saveFilesToHistory(updatedHistory);

      setTimeout(() => {
        setUploadStatus('idle');
        setUploadFile(null);
      }, 4000);

    } catch (error) {
      setUploadStatus('error');
      setUploadError(error.message || 'Server connection failed.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Drag & Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`relative group border rounded-2xl p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-500 ${
          dragActive 
            ? 'border-purple-500/80 bg-purple-500/5 shadow-[0_0_20px_rgba(168,85,247,0.1)]' 
            : 'border-zinc-800/80 hover:border-zinc-700/80 bg-zinc-900/10 hover:bg-zinc-900/30'
        }`}
      >
        <input
          type="file"
          id="file-upload"
          accept=".pdf"
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
          onChange={handleFileChange}
          disabled={uploadStatus !== 'idle' && uploadStatus !== 'error'}
        />
        
        {uploadStatus === 'idle' && (
          <>
            <div className="p-3.5 bg-zinc-900 border border-zinc-800/80 rounded-xl text-zinc-400 group-hover:text-purple-400 group-hover:border-purple-500/20 transition-all duration-300 mb-3 shadow-inner">
              <Upload className="h-4 w-4" />
            </div>
            <span className="text-[11px] font-bold text-zinc-200 group-hover:text-white transition-colors">Drag & drop your PDF here</span>
            <span className="text-[9px] text-zinc-500 mt-1">or click to browse local files</span>
          </>
        )}

        {uploadStatus !== 'idle' && uploadStatus !== 'success' && uploadStatus !== 'error' && (
          <div className="flex flex-col items-center py-2">
            <Loader2 className="h-6 w-6 text-purple-400 animate-spin mb-3" />
            <span className="text-[11px] font-bold text-zinc-200 tracking-tight">
              {uploadStatus === 'uploading' && 'Uploading document...'}
              {uploadStatus === 'parsing' && 'Extracting contents...'}
              {uploadStatus === 'chunking' && 'Building overlaps...'}
              {uploadStatus === 'indexing' && 'Writing vectors to Qdrant...'}
            </span>
            <span className="text-[9px] text-zinc-500 mt-1 font-mono">Wait, resolving pipeline</span>
          </div>
        )}

        {uploadStatus === 'success' && (
          <div className="flex flex-col items-center py-2 text-emerald-400 animate-fadeIn">
            <CheckCircle2 className="h-7 w-7 mb-2.5" />
            <span className="text-[11px] font-bold text-zinc-250">Ingestion Succeeded!</span>
            <span className="text-[9px] text-zinc-500 mt-1 truncate max-w-[200px] font-mono">{uploadFile?.name}</span>
          </div>
        )}

        {uploadStatus === 'error' && (
          <div className="flex flex-col items-center py-2 text-rose-400 animate-fadeIn">
            <AlertCircle className="h-7 w-7 mb-2.5" />
            <span className="text-[11px] font-bold text-zinc-250">Ingestion Failed</span>
            <p className="text-[9px] text-zinc-500 mt-2 px-3 text-center leading-normal line-clamp-2 max-w-[220px]">
              {uploadError}
            </p>
            <span className="text-[9px] underline mt-3 text-purple-400 font-bold uppercase tracking-wider group-hover:text-purple-300 font-mono">Dismiss & Retry</span>
          </div>
        )}
      </div>

      {/* Ingested Files List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-[9px] font-bold uppercase tracking-widest text-zinc-500 font-mono">Active Index</h2>
          <span className="text-[9px] bg-zinc-900 border border-zinc-800 text-zinc-400 px-2 py-0.5 rounded-full font-mono font-bold">
            {uploadedFiles.length}
          </span>
        </div>
        
        {uploadedFiles.length === 0 ? (
          <div className="rounded-xl border border-zinc-800/40 p-4 text-center bg-zinc-900/5">
            <p className="text-[10px] text-zinc-500 leading-normal font-medium">
              No files currently indexed. Gateway will fall back to web search or general chat.
            </p>
          </div>
        ) : (
          <div className="space-y-2 max-h-60 overflow-y-auto pr-1 scrollbar-thin">
            {uploadedFiles.map((file, i) => (
              <div key={i} className="flex gap-3 p-3 bg-zinc-900/20 rounded-xl border border-zinc-850 hover:border-zinc-800 hover:bg-zinc-900/35 transition-all duration-300 shadow-sm">
                <FileText className="h-4 w-4 text-purple-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] font-semibold text-zinc-200 truncate" title={file.name}>{file.name}</p>
                  <div className="flex items-center gap-1.5 mt-1 text-[8px] text-zinc-500 font-mono font-bold">
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
  );
}
