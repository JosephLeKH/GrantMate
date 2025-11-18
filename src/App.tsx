import { useState } from "react";
import { Header } from "./components/Header";
import { InputSection } from "./components/InputSection";
import { OutputSection } from "./components/OutputSection";
import { Footer } from "./components/Footer";
import { Toast } from "./components/Toast";
import { AnswerData } from "./types";

function App() {
  const [answers, setAnswers] = useState<AnswerData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [toastType, setToastType] = useState<"success" | "error">("success");
  const [showToast, setShowToast] = useState(false);

  const showToastMessage = (message: string, type: "success" | "error" = "success") => {
    setToastMessage(message);
    setToastType(type);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  const handleGenerate = async (questions: string, context: string) => {
    setIsLoading(true);
    setAnswers([]);

    try {
      // For public demo: Use environment variable or localhost
      // Set VITE_API_URL in your .env file for production
      const API_URL = import.meta.env.VITE_API_URL 
        || 'http://localhost:8000/api/generate';
      
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          grantQuestions: questions,  // ✅ Match backend API field name
          grantContext: context || "",  // ✅ Match backend API field name
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('API Error:', errorData);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // ✅ Backend returns "results" array, not "answers"
      if (data.results && Array.isArray(data.results)) {
        setAnswers(data.results);
        showToastMessage("✨ Answers generated successfully!", "success");
      } else {
        throw new Error("Invalid response format");
      }
    } catch (error) {
      console.error('Error generating answers:', error);
      showToastMessage("❌ Failed to generate answers. Please try again.", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setAnswers([]);
    showToastMessage("🗑️ Cleared all content", "success");
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-2">
        <InputSection 
          onGenerate={handleGenerate}
          onClear={handleClear}
          isLoading={isLoading}
        />
        <OutputSection 
          answers={answers}
          isLoading={isLoading}
          onCopy={showToastMessage}
        />
      </main>

      <Footer />
      <Toast 
        message={toastMessage}
        type={toastType}
        show={showToast}
      />
    </div>
  );
}

export default App;
