import { useState } from "react";
import { AnswerData } from "../types";

interface AnswerBlockProps {
  answer: AnswerData;
  onCopy: (message: string, type: "success" | "error") => void;
}

export function AnswerBlock({ answer, onCopy }: AnswerBlockProps) {
  const [showSources, setShowSources] = useState(false);

  const handleCopy = async () => {
    const text = `Q: ${answer.question}\n\nA: ${answer.answer}`;
    try {
      await navigator.clipboard.writeText(text);
      onCopy("📋 Copied to clipboard!", "success");
    } catch (error) {
      onCopy("❌ Failed to copy", "error");
    }
  };

  return (
    <div className="bg-white border-2 border-[#B89F88] border-l-[3px] border-l-[#8B5E3C] rounded-[3px] p-7 mb-6 transition-all relative overflow-hidden shadow-[0_6px_16px_-2px_rgba(31,25,18,0.15)] hover:bg-[#EAE4DC] hover:border-[#9B8472] hover:border-l-[#6B4423] hover:translate-x-1.5 hover:shadow-[0_12px_24px_-4px_rgba(31,25,18,0.2)]">
      {/* Left accent border glow */}
      <div className="absolute top-0 left-0 w-[3px] h-full bg-gradient-to-b from-[#8B5E3C] to-[#6B4423] shadow-[0_0_10px_rgba(139,94,60,0.5)]" />

      <div className="flex items-start justify-between gap-4 mb-4 relative z-10">
        <h3 className="text-lg font-semibold text-[#1F1912] leading-snug flex-1">
          {answer.question}
        </h3>
        <div className="flex gap-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleCopy}
            className="inline-flex items-center justify-center w-9 h-9 p-0 bg-[rgba(139,94,60,0.2)] text-white/90 border border-[rgba(139,94,60,0.3)] rounded-[3px] cursor-pointer transition-all scale-90 hover:bg-[rgba(139,94,60,0.4)] hover:border-[rgba(139,94,60,0.5)] hover:scale-110 active:scale-95"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M6 2C5.44772 2 5 2.44772 5 3V4H4C2.89543 4 2 4.89543 2 6V13C2 14.1046 2.89543 15 4 15H10C11.1046 15 12 14.1046 12 13V6C12 4.89543 11.1046 4 10 4H9V3C9 2.44772 8.55228 2 8 2H6Z"/>
            </svg>
          </button>
        </div>
      </div>

      <div className="text-[#3D3228] leading-relaxed text-[0.9375rem] relative z-10 whitespace-pre-line">
        {answer.answer}
      </div>

      {answer.sources && answer.sources.length > 0 && (
        <div className="mt-6 pt-4 border-t border-[rgba(139,94,60,0.2)] relative z-10">
          <button
            onClick={() => setShowSources(!showSources)}
            className="flex items-center gap-2 w-full px-4 py-2 bg-[rgba(139,94,60,0.1)] border border-[rgba(139,94,60,0.2)] rounded-[3px] text-[#3D3228] text-sm font-medium cursor-pointer transition-all text-left hover:bg-[rgba(139,94,60,0.15)] hover:border-[rgba(139,94,60,0.3)] hover:-translate-y-0.5"
          >
            <svg className="w-4 h-4 flex-shrink-0 opacity-80" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
            </svg>
            <span className="flex-1 font-medium">View Sources</span>
            <span className="bg-[rgba(139,94,60,0.2)] text-[#6B4423] px-2 py-0.5 rounded-sm text-xs font-semibold min-w-[1.5rem] text-center">
              {answer.sources.length}
            </span>
            <svg 
              className={`w-4 h-4 flex-shrink-0 transition-transform opacity-70 ${showSources ? 'rotate-180' : ''}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showSources && (
            <div className="mt-4 p-4 bg-[rgba(0,0,0,0.05)] border border-[rgba(139,94,60,0.15)] rounded-[4px]">
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-white/10">
                <span className="text-sm font-semibold text-[#3D2817] flex items-center gap-1">
                  <span>📚</span>
                  Knowledge Base Sources
                </span>
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-[rgba(16,185,129,0.2)] text-[#10B981] border border-[rgba(16,185,129,0.3)] rounded-sm text-[0.7rem] font-semibold uppercase tracking-wider">
                  <span>✓</span>
                  Verified
                </span>
              </div>
              <ul className="list-none p-0 m-0 flex flex-col gap-2">
                {answer.sources.map((source, idx) => (
                  <li 
                    key={idx}
                    className="flex items-start gap-2 p-2 bg-white/5 rounded-[3px] transition-all hover:bg-white/10 hover:translate-x-1"
                  >
                    <span className="flex-shrink-0 mt-0.5 text-[#8B5E3C] opacity-80">•</span>
                    <span className="text-[0.8125rem] text-[#3D3228]/90 leading-relaxed flex-1">
                      {source}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
