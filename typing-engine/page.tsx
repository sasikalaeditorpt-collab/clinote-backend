"use client";
import { useState } from "react";

export default function TypingEngineUI() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("http://localhost:8000/transcribe-docx", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      alert("Transcription failed");
      setLoading(false);
      return;
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "Clinote-Transcription.docx";
    a.click();

    setLoading(false);
  };

  return (
    <div style={{ padding: "20px" }}>
      <input
        type="file"
        accept=".wav,.mp3,.m4a"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />

      <button
        onClick={handleUpload}
        disabled={loading}
        style={{ marginLeft: "10px" }}
      >
        {loading ? "Processing..." : "Transcribe"}
      </button>
    </div>
  );
}