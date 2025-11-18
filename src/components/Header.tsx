export function Header() {
  return (
    <header className="phc-gradient-header border-b-[3px] border-[#A87548] px-6 lg:px-10 py-6 sticky top-0 z-50 shadow-2xl relative overflow-hidden">
      {/* Animated Grid Background */}
      <div className="absolute inset-0 opacity-50 pointer-events-none">
        <div 
          className="absolute inset-0"
          style={{
            backgroundImage: `
              linear-gradient(rgba(168, 117, 72, 0.06) 1px, transparent 1px),
              linear-gradient(90deg, rgba(168, 117, 72, 0.06) 1px, transparent 1px)
            `,
            backgroundSize: '50px 50px',
            animation: 'grid-flow 20s linear infinite'
          }}
        />
      </div>

      <div className="max-w-full mx-0 flex items-center justify-between gap-8 relative z-10">
        <div className="flex items-center gap-6">
          <img 
            src="/assets/PHC Logo.png" 
            alt="Project Homeless Connect" 
            className="h-12 w-auto object-contain brightness-[1.2] drop-shadow-[0_2px_8px_rgba(255,255,255,0.3)] transition-all hover:brightness-[1.4] hover:drop-shadow-[0_4px_12px_rgba(255,255,255,0.5)] hover:-translate-y-0.5" 
          />
          <div className="flex flex-col gap-1">
            <h1 className="text-2xl font-semibold text-white tracking-wide flex items-center gap-2.5 drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)]">
              GrantMate <span className="text-[#F5D7B8] font-normal text-[1.625rem] mx-[-0.125rem] drop-shadow-[0_0_8px_rgba(245,215,184,0.6)]">×</span> PHC
            </h1>
            <p className="text-xs text-white/85 tracking-[0.12em] uppercase drop-shadow-[0_1px_2px_rgba(0,0,0,0.3)]">
              Professional Grant Writing Platform
            </p>
          </div>
        </div>

        <div className="hidden md:flex items-center gap-4">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/15 border border-white/30 rounded-sm text-white text-xs font-semibold tracking-wider uppercase backdrop-blur-[10px] shadow-md hover:bg-white/20 hover:border-white/50 hover:-translate-y-0.5 transition-all relative overflow-hidden">
            <div 
              className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-white/30 to-transparent"
              style={{ animation: 'shimmer 4s infinite', left: '-100%' }}
            />
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="drop-shadow-[0_0_4px_rgba(245,215,184,0.8)]" style={{ animation: 'pulse-glow 2s ease-in-out infinite' }}>
              <path d="M8 2L2 5.5L8 9L14 5.5L8 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 10.5L8 14L14 10.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>AI-Powered</span>
          </div>
        </div>
      </div>
    </header>
  );
}
