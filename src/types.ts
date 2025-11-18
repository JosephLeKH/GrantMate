// Backend returns sources as array of strings like:
// ["Quantitative → PHC Headcount 2024", "Qualitative → PHC History Approach 2025"]
export interface AnswerData {
  question: string;
  answer: string;
  sources?: string[];
}
