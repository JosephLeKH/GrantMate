export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-[#3D3228] text-white/80 py-8 px-6 lg:px-10 border-t-[3px] border-t-[#8B5E3C]">
      <div className="max-w-full mx-0 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <img 
            src="/assets/PHC Logo.png" 
            alt="Project Homeless Connect" 
            className="h-10 w-auto object-contain brightness-[1.2] opacity-90" 
          />
          <div>
            <p className="font-semibold text-white">GrantMate × PHC</p>
            <p className="text-sm text-white/60">
              © {currentYear} Project Homeless Connect • Professional Grant Writing Platform
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="inline-flex items-center px-3 py-1.5 bg-white/10 text-white/80 border border-white/20 rounded-sm text-xs font-medium">
            Powered by Gemini AI
          </span>
          <span className="inline-flex items-center px-3 py-1.5 bg-white/10 text-white/80 border border-white/20 rounded-sm text-xs font-medium">
            RAG Technology
          </span>
          <span className="inline-flex items-center px-3 py-1.5 bg-white/10 text-white/80 border border-white/20 rounded-sm text-xs font-medium">
            Vector Search
          </span>
        </div>
      </div>
    </footer>
  );
}
