import { useState, FormEvent } from "react";

interface InputSectionProps {
  onGenerate: (questions: string, context: string) => void;
  onClear: () => void;
  isLoading: boolean;
}

export function InputSection({ onGenerate, onClear, isLoading }: InputSectionProps) {
  const [questions, setQuestions] = useState("");
  const [context, setContext] = useState("");

  const questionCount = questions.trim() ? questions.trim().split('\n').filter(q => q.trim()).length : 0;

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (questions.trim()) {
      onGenerate(questions, context);
    }
  };

  const handleClear = () => {
    setQuestions("");
    setContext("");
    onClear();
  };

  return (
    <section className="phc-gradient-input border-r-[3px] border-r-[rgba(139,94,60,0.2)] border-l border-l-[rgba(245,215,184,0.4)] p-8 lg:p-12 relative overflow-visible shadow-[inset_0_1px_0_rgba(255,255,255,0.6),inset_-2px_0_20px_rgba(139,94,60,0.05),0_4px_30px_rgba(139,94,60,0.1)]">
      {/* Animated Top Border */}
      <div 
        className="absolute top-0 left-0 right-0 h-[5px] shadow-[0_2px_15px_rgba(139,94,60,0.5),inset_0_1px_0_rgba(255,255,255,0.3)]"
        style={{
          background: 'linear-gradient(90deg, #8B5E3C 0%, #A87548 25%, #C4996B 50%, #A87548 75%, #8B5E3C 100%)',
          backgroundSize: '300% 100%',
          animation: 'gradient-shift 4s ease infinite'
        }}
      />

      <div className="mb-8 pb-4 border-b-2 border-[rgba(139,94,60,0.15)] relative">
        <div className="flex items-baseline justify-start mb-2 flex-wrap gap-4">
          <h2 className="text-2xl font-semibold text-[#3D2817] tracking-tight">Grant Questions</h2>
          <span className="inline-flex items-center gap-1.5 px-4 py-2 bg-gradient-to-br from-[rgba(139,94,60,0.12)] to-[rgba(168,117,72,0.08)] text-[#6B4423] border-[1.5px] border-[rgba(139,94,60,0.25)] rounded-[3px] text-xs font-bold uppercase tracking-wider shadow-[0_2px_8px_rgba(139,94,60,0.15),inset_0_1px_0_rgba(255,255,255,0.4)] relative overflow-hidden">
            Input
          </span>
        </div>
        <p className="text-[0.9375rem] text-[#6B4E3D] leading-relaxed mt-2">
          Paste your grant application questions below. Our AI will generate comprehensive, data-driven responses tailored to your specific sponsor when you provide context.
        </p>
        <div className="absolute bottom-[-2px] left-0 w-20 h-[2px] bg-gradient-to-r from-[#8B5E3C] to-[#A87548]" />
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-8">
        <div className="flex flex-col gap-2">
          <label htmlFor="grant-questions" className="flex flex-col gap-1 font-semibold text-[#3D2817] mb-1">
            <span>Grant Application Questions</span>
            <span className="font-normal text-[0.8125rem] text-[#6B4E3D] mt-0.5">
              One question per line • Questions will be analyzed by AI
            </span>
          </label>
          <div className="relative">
            <textarea
              id="grant-questions"
              rows={12}
              value={questions}
              onChange={(e) => setQuestions(e.target.value)}
              placeholder="What is your organization's name and mission?&#10;What is the purpose of your request?&#10;Who will this event serve and how many people will be reached?&#10;&#10;Paste questions here, one per line..."
              className="w-full p-5 font-['Inter'] text-[0.9375rem] leading-relaxed text-[#3D2817] bg-gradient-to-br from-[#FAF7F2] to-[#F8F5EF] border-2 border-[rgba(139,94,60,0.2)] rounded-[3px] resize-y transition-all focus:outline-none focus:border-[#A87548] focus:bg-white focus:shadow-[0_0_0_4px_rgba(168,117,72,0.15),0_6px_20px_rgba(139,94,60,0.12),inset_0_1px_2px_rgba(139,94,60,0.05)] focus:-translate-y-0.5 placeholder:text-[#9B8472] shadow-[0_4px_12px_rgba(139,94,60,0.08),inset_0_1px_0_rgba(255,255,255,0.8)] relative z-10"
              required
            />
          </div>
          <div className="flex items-center justify-between mt-1 flex-wrap gap-2">
            <span className="flex items-center gap-1 text-[0.8125rem] text-[#6D5D4F] font-medium">
              <span className="text-base">📝</span>
              <span className="transition-colors">{questionCount} questions</span>
            </span>
            <span className="flex items-center gap-1 text-xs text-[#6D5D4F] font-medium">
              <span className="text-sm" style={{ animation: 'pulse-glow 2s ease-in-out infinite' }}>✨</span>
              AI will analyze each question
            </span>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="grant-context" className="flex flex-col gap-1 font-semibold text-[#3D2817] mb-1">
            <span>Sponsor/Grant Context (Optional)</span>
            <span className="font-normal text-[0.8125rem] text-[#6B4E3D] mt-0.5">
              ✨ AI will use this to tailor responses to the specific sponsor and grant requirements
            </span>
          </label>
          <textarea
            id="grant-context"
            rows={8}
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="Example: This grant is from Kaiser Permanente, which focuses on health equity, community health programs, and addressing social determinants of health. They prioritize programs that serve underserved populations and have measurable health outcomes. The grant amount is $50,000 for community health initiatives.&#10;&#10;You can paste extensive information here: sponsor background, funding priorities, mission statement, specific requirements, geographic focus, population served, program types, grant amounts, deadlines, evaluation criteria, partnership preferences, or any other relevant details. The AI will analyze ALL of this information to tailor responses."
            className="w-full p-5 font-['Inter'] text-[0.9375rem] leading-relaxed text-[#3D2817] bg-gradient-to-br from-[#FAF7F2] to-[#F8F5EF] border-2 border-[rgba(139,94,60,0.2)] rounded-[3px] min-h-[150px] resize-y transition-all focus:outline-none focus:border-[#A87548] focus:bg-white focus:shadow-[0_0_0_4px_rgba(168,117,72,0.15),0_6px_20px_rgba(139,94,60,0.12),inset_0_1px_2px_rgba(139,94,60,0.05)] focus:-translate-y-0.5 placeholder:text-[#9B8472] shadow-[0_4px_12px_rgba(139,94,60,0.08),inset_0_1px_0_rgba(255,255,255,0.8)]"
          />
          <span className="flex items-center gap-1 text-xs text-[#6D5D4F] font-medium mt-2">
            <span className="text-sm">🎯</span>
            This context helps AI align PHC's work with the sponsor's priorities
          </span>
        </div>

        <div className="flex gap-4 flex-wrap pt-4 border-t-2 border-[rgba(234,228,220,1)]">
          <button
            type="submit"
            disabled={isLoading || !questions.trim()}
            className="phc-btn-primary inline-flex items-center justify-center gap-2 px-7 py-3.5 text-[0.9375rem] font-semibold leading-none text-white rounded-[4px] cursor-pointer transition-all relative overflow-hidden whitespace-nowrap select-none disabled:opacity-60 disabled:cursor-not-allowed hover:-translate-y-0.5"
          >
            {isLoading ? (
              <>
                <svg className="w-5 h-5" style={{ animation: 'spin 1s linear infinite' }} viewBox="0 0 20 20">
                  <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="2" fill="none" strokeDasharray="50" strokeDashoffset="25"/>
                </svg>
                <span>Generating...</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5 flex-shrink-0" width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M3 10L17 10M10 3L17 10L10 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                <span>Generate Answers</span>
              </>
            )}
          </button>
          <button
            type="button"
            onClick={handleClear}
            className="inline-flex items-center justify-center gap-2 px-7 py-3.5 text-[0.9375rem] font-semibold leading-none bg-gradient-to-br from-[rgba(245,237,228,0.8)] to-[rgba(240,230,217,0.8)] text-[#6B4E3D] border-2 border-[rgba(139,94,60,0.3)] rounded-[4px] shadow-[0_4px_10px_rgba(139,94,60,0.1)] cursor-pointer transition-all whitespace-nowrap select-none hover:bg-gradient-to-br hover:from-[rgba(250,245,238,0.95)] hover:to-[rgba(248,242,232,0.95)] hover:border-[rgba(139,94,60,0.5)] hover:text-[#3D2817] hover:-translate-y-0.5 hover:shadow-[0_6px_15px_rgba(139,94,60,0.15)]"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M4.5 4.5L13.5 13.5M4.5 13.5L13.5 4.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            Clear
          </button>
        </div>
      </form>
    </section>
  );
}
