import { useState } from 'react';

export function useChatStream() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeNode, setActiveNode] = useState(null);

  const askQuestion = async (queryText) => {
    setIsLoading(true);
    setActiveNode('router');

    // Add user message
    const userMessage = {
      role: 'user',
      text: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessage]);
    
    let assistantText = '';
    let trace = [];
    let sources = [];
    let verificationScore = null;
    let verificationReasoning = '';

    // Append Assistant placeholder message
    setMessages(prev => [
      ...prev,
      {
        role: 'assistant',
        text: '',
        trace: [],
        sources: [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText, limit: 5 })
      });

      if (!response.ok) {
        throw new Error('Failed to establish streaming connection.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Parse SSE lines (separated by double linebreaks)
        const lines = buffer.split('\n\n');
        
        // Keep the last incomplete block in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim().startsWith('data:')) {
            const dataStr = line.replace(/^data:\s*/, '').trim();
            if (!dataStr) continue;

            try {
              const parsed = JSON.parse(dataStr);
              
              if (parsed.event === 'token') {
                assistantText += parsed.data;
                // Update assistant response text in state
                setMessages(prev => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  if (last && last.role === 'assistant') {
                    last.text = assistantText;
                  }
                  return updated;
                });
              } else if (parsed.event === 'status') {
                setActiveNode(parsed.node);
                if (parsed.details) {
                  trace = [...trace, { node: parsed.node, details: parsed.details }];
                  
                  if (parsed.sources) {
                    // Dedup and merge sources
                    const existingContent = new Set(sources.map(s => s.content));
                    const newSources = parsed.sources.filter(s => !existingContent.has(s.content));
                    sources = [...sources, ...newSources];
                  }
                  if (parsed.verification) {
                    verificationScore = parsed.verification.score;
                    verificationReasoning = parsed.verification.reasoning;
                  }
                  if (parsed.draft_response && !assistantText) {
                    assistantText = parsed.draft_response;
                  }
                  
                  // Update assistant message trace, sources, text, and verification score in state
                  setMessages(prev => {
                    const updated = [...prev];
                    const last = updated[updated.length - 1];
                    if (last && last.role === 'assistant') {
                      last.trace = trace;
                      last.sources = sources;
                      last.text = assistantText;
                      if (verificationScore !== null) {
                        last.verificationScore = verificationScore;
                        last.verificationReasoning = verificationReasoning;
                      }
                    }
                    return updated;
                  });
                }
              } else if (parsed.event === 'error') {
                throw new Error(parsed.data);
              } else if (parsed.event === 'done') {
                setIsLoading(false);
                setActiveNode(null);
              }
            } catch (e) {
              console.error('Error parsing SSE packet:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      setMessages(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last && last.role === 'assistant') {
          last.text = `Error: ${error.message}. Make sure your backend server is running and the Gemini API key is configured correctly.`;
          last.error = true;
        }
        return updated;
      });
      setIsLoading(false);
      setActiveNode(null);
    }
  };

  const clearMessages = () => {
    setMessages([]);
    setIsLoading(false);
    setActiveNode(null);
  };

  return {
    messages,
    setMessages,
    isLoading,
    activeNode,
    askQuestion,
    clearMessages
  };
}
