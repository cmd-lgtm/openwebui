import React, { useState } from 'react';
import { Sparkles, Send, Paperclip, Bot, User, Copy, Check, RefreshCw, X } from 'lucide-react';

export function AIPanel() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Array<{
    id: string; role: 'user' | 'assistant'; content: string; timestamp: Date;
  }>>([]);

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages((prev) => [...prev, {
      id: crypto.randomUUID(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }]);
    // Simulated AI response
    setTimeout(() => {
      setMessages((prev) => [...prev, {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `I'm the NEXUS AI Assistant. I can help you with:\n\n- **Code generation** — describe what you need\n- **Bug fixing** — paste your error\n- **Code review** — share your code\n- **Refactoring** — improve code quality\n- **Documentation** — auto-generate docs\n\nConnect an AI provider (OpenAI, Anthropic, Ollama, etc.) in Settings to get started!`,
        timestamp: new Date(),
      }]);
    }, 500);
    setInput('');
  };

  return (
    <div className="h-full flex flex-col bg-[#0d1117]">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-[#21262d]">
        <div className="flex items-center gap-2">
          <Sparkles size={15} className="text-[#bc8cff]" />
          <span className="text-xs font-semibold text-[#e6edf3]">AI Assistant</span>
        </div>
        <div className="flex items-center gap-1">
          <button className="text-[10px] px-2 py-0.5 rounded bg-[#161b22] text-[#8b949e] border border-[#21262d]
                            hover:text-[#e6edf3] transition-colors">
            Claude Sonnet 4
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <div className="text-3xl mb-3">🤖</div>
            <h3 className="text-sm font-semibold text-[#e6edf3] mb-1">How can I help?</h3>
            <p className="text-xs text-[#6e7681] mb-4">Ask me anything about your code</p>
            <div className="space-y-1.5">
              {['💡 Explain this code', '🐛 Fix bugs', '✨ Refactor', '🧪 Write tests', '📝 Add docs'].map((s) => (
                <button
                  key={s}
                  onClick={() => setInput(s.substring(2))}
                  className="block w-full text-left px-3 py-1.5 rounded text-xs text-[#8b949e]
                            bg-[#161b22] border border-[#21262d] hover:text-[#e6edf3] hover:border-[#30363d]
                            transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'assistant' && (
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#bc8cff] to-[#58a6ff] flex items-center justify-center flex-shrink-0 mt-0.5">
                <Bot size={13} className="text-white" />
              </div>
            )}
            <div className={`max-w-[85%] rounded-lg px-3 py-2 text-xs leading-relaxed
              ${msg.role === 'user'
                ? 'bg-[#1f6feb] text-white'
                : 'bg-[#161b22] text-[#e6edf3] border border-[#21262d]'
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>
            </div>
            {msg.role === 'user' && (
              <div className="w-6 h-6 rounded-full bg-[#30363d] flex items-center justify-center flex-shrink-0 mt-0.5">
                <User size={13} className="text-[#e6edf3]" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="px-3 py-2 border-t border-[#21262d]">
        <div className="flex items-end gap-2 bg-[#161b22] rounded-lg border border-[#30363d] p-2
                       focus-within:border-[#58a6ff] transition-colors">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
            }}
            placeholder="Ask anything..."
            rows={1}
            className="flex-1 bg-transparent text-xs text-[#e6edf3] outline-none resize-none
                       placeholder:text-[#484f58] min-h-[24px] max-h-[100px]"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            title="Send message"
            className="p-1.5 rounded-md bg-[#238636] text-white hover:bg-[#2ea043]
                       disabled:opacity-30 disabled:pointer-events-none transition-colors flex-shrink-0"
          >
            <Send size={13} />
          </button>
        </div>
      </div>
    </div>
  );
}
