import { useState } from "react";
import { AnswerData } from "../types";
import { AnswerBlock } from "./AnswerBlock";

interface OutputSectionProps {
  answers: AnswerData[];
  isLoading: boolean;
  onCopy: (message: string, type: "success" | "error") => void;
}

export function OutputSection({ answers, isLoading, onCopy }: OutputSectionProps) {
  const handleCopyAll = async () => {
    const allText = answers
      .map(a => `Q: ${a.question}\n\nA: ${a.answer}\n\n${'-'.repeat(80)}`)
      .join('\n\n');
    
    try {
      await navigator.clipboard.writeText(allText);
      onCopy("📋 All answers copied to clipboard!", "success");
    } catch (error) {
      onCopy("❌ Failed to copy", "error");
    }
  };

  return (
    <section className="phc-gradient-output border-l border-l-[rgba(139,94,60,0.15)] p-8 lg:p-12 min-h-full relative flex flex-col shadow-[inset_0_1px_0_rgba(255,255,255,0.7),inset_2px_0_20px_rgba(139,94,60,0.04),inset_0_-1px_3px_rgba(139,94,60,0.05)]">
      {/* Particle Effect Background */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-60"
        style={{
          background: `
            radial-gradient(circle at 20% 30%, rgba(139, 94, 60, 0.08) 0%, transparent 30%),
            radial-gradient(circle at 80% 70%, rgba(168, 117, 72, 0.1) 0%, transparent 30%),
            radial-gradient(circle at 50% 50%, rgba(184, 159, 136, 0.06) 0%, transparent 45%)
          `,
          animation: 'float 18s ease-in-out infinite'
        }}
      />

      <div className="flex items-start justify-between gap-6 mb-8 pb-4 border-b-2 border-[rgba(139,94,60,0.15)] relative z-10">
        <div>
          <div className="flex items-baseline gap-2 mb-1">
            <h2 className="text-2xl font-semibold text-[#3D2817] tracking-tight">Generated Answers</h2>
            {answers.length > 0 && (
              <span className="inline-flex items-center px-2.5 py-1 bg-[rgba(139,94,60,0.2)] text-[#6B4423] border border-[rgba(139,94,60,0.3)] rounded-sm text-xs font-semibold uppercase tracking-wider ml-2" style={{ animation: 'pulse-glow 2s ease-in-out infinite' }}>
                {answers.length} Ready
              </span>
            )}
          </div>
          <p className="text-sm text-[#6B4E3D]">
            {answers.length > 0 
              ? "Review your AI-generated grant responses below" 
              : "Your AI-generated grant responses will appear here"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {answers.length > 0 && (
            <button
              onClick={handleCopyAll}
              className="inline-flex items-center justify-center w-10 h-10 p-0 bg-transparent text-[#3D3228] border border-[#B89F88] rounded-[3px] cursor-pointer transition-all hover:bg-[#EAE4DC] hover:border-[#9B8472] hover:text-[#1F1912] hover:-translate-y-0.5"
              title="Copy all answers"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M8 2C7.44772 2 7 2.44772 7 3V4H5C3.89543 4 3 4.89543 3 6V16C3 17.1046 3.89543 18 5 18H13C14.1046 18 15 17.1046 15 16V6C15 4.89543 14.1046 4 13 4H11V3C11 2.44772 10.5523 2 10 2H8Z"/>
                <path d="M8 4H10V6H8V4Z" fill="currentColor"/>
              </svg>
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 relative z-10">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-24 text-[#6B4E3D] text-center">
            <div className="w-20 h-20 relative mb-6">
              <div 
                className="absolute inset-0 border-4 border-[rgba(139,94,60,0.15)] border-t-[#8B5E3C] rounded-full"
                style={{ animation: 'spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite' }}
              />
              <div 
                className="absolute inset-2 border-[3px] border-[rgba(168,117,72,0.2)] border-b-[#A87548] rounded-full"
                style={{ animation: 'spin 0.8s cubic-bezier(0.5, 0, 0.5, 1) infinite reverse' }}
              />
            </div>
            <p className="text-lg font-semibold text-[#3D2817] mb-2">Generating Answers...</p>
            <p className="text-sm text-[#6B4E3D]">AI is analyzing your questions and context</p>
          </div>
        ) : answers.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="text-6xl mb-4 opacity-30">📝</div>
            <p className="text-lg font-medium text-[#6B4E3D] mb-2">No answers yet</p>
            <p className="text-sm text-[#9B8472]">
              Enter your grant questions and click "Generate Answers" to get started
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {answers.map((answer, index) => (
              <AnswerBlock key={index} answer={answer} onCopy={onCopy} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
