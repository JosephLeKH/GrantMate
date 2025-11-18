interface ToastProps {
  message: string;
  type: "success" | "error";
  show: boolean;
}

export function Toast({ message, type, show }: ToastProps) {
  return (
    <div
      className={`fixed bottom-8 right-8 bg-[#1F1912] text-[#F5F0E8] px-6 py-4 rounded-[3px] shadow-[0_20px_32px_-8px_rgba(31,25,18,0.25)] max-w-[400px] pointer-events-none flex items-center gap-2 transition-all duration-300 z-[1000] ${
        show ? 'opacity-100 translate-y-0 pointer-events-auto' : 'opacity-0 translate-y-4'
      } ${
        type === 'success' ? 'border-l-4 border-l-[#7CB342]' : 'border-l-4 border-l-[#C9826B]'
      }`}
    >
      <span className="text-xl flex-shrink-0">
        {type === "success" ? "✓" : "✕"}
      </span>
      <span className="text-[0.9375rem] font-medium">{message}</span>
    </div>
  );
}
