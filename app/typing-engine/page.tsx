"use client";

import { useState, useEffect } from "react";

type DoctorOption = {
  value: string;
  label: string;
};

export default function TypingEnginePage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [draft, setDraft] = useState("");

  const [doctorId, setDoctorId] = useState("");
  const [doctors, setDoctors] = useState<DoctorOption[]>([]);
  const [newDoctorId, setNewDoctorId] = useState("");
  const [creatingDoctor, setCreatingDoctor] = useState(false);

  const [sampleStatus, setSampleStatus] = useState("");
  const [sampleUploading, setSampleUploading] = useState(false);
  const [sampleCount, setSampleCount] = useState(0);

  useEffect(() => {
    fetchDoctors();
  }, []);

  useEffect(() => {
    if (doctorId) checkSampleCount(doctorId);
  }, [doctorId]);

  async function fetchDoctors() {
    try {
      const res = await fetch("http://localhost:8000/list-doctors");
      const json = await res.json();
      const opts = (json.doctors || []).map((d: string) => ({
        value: d,
        label: d,
      }));
      setDoctors(opts);
      if (opts.length > 0 && !doctorId) setDoctorId(opts[0].value);
    } catch {
      setDoctors([]);
    }
  }

  async function checkSampleCount(id: string) {
    try {
      const res = await fetch(
        `http://localhost:8000/style-sample-count?doctor_id=${id}`
      );
      const json = await res.json();
      setSampleCount(json.count);
    } catch {
      setSampleCount(0);
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;
    setFile(selected);
    setDraft("");
  };

  const generateDraft = async () => {
    if (!file) return;

    setLoading(true);
    setDraft("");
    setProgress(0);

    const interval = setInterval(() => {
      setProgress((prev) => (prev >= 90 ? prev : prev + 5));
    }, 500);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("doctor_id", doctorId);

    try {
      const res = await fetch("http://localhost:8000/transcribe-docx", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        clearInterval(interval);
        setProgress(0);
        setDraft("Transcription failed.");
        setLoading(false);
        return;
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "draft.docx";
      a.click();
      window.URL.revokeObjectURL(url);

      clearInterval(interval);
      setProgress(100);
      setDraft("Draft downloaded successfully.");
    } catch {
      clearInterval(interval);
      setProgress(0);
      setDraft("Error connecting to backend.");
    }

    setLoading(false);
    setTimeout(() => setProgress(0), 1000);
  };

  const uploadSamples = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setSampleUploading(true);
    setSampleStatus("Uploading…");

    for (const f of Array.from(files)) {
      const formData = new FormData();
      formData.append("doctor_id", doctorId);
      formData.append("file", f);

      const res = await fetch("http://localhost:8000/upload-style-sample", {
        method: "POST",
        body: formData,
      });

      const json = await res.json();
      if (json.error) {
        setSampleStatus(`Error: ${json.error}`);
        setSampleUploading(false);
        return;
      }
    }

    setSampleUploading(false);
    setSampleStatus("Samples uploaded successfully.");
    checkSampleCount(doctorId);
  };

  const createDoctorProfile = async () => {
    if (!newDoctorId.trim()) return;
    setCreatingDoctor(true);

    const formData = new FormData();
    formData.append("doctor_id", newDoctorId.trim());

    try {
      const res = await fetch("http://localhost:8000/create-doctor", {
        method: "POST",
        body: formData,
      });
      const json = await res.json();

      if (json.status === "created" || json.status === "exists") {
        setDoctorId(json.doctor_id);
        setNewDoctorId("");
        fetchDoctors();
        checkSampleCount(json.doctor_id);
      }
    } catch {}

    setCreatingDoctor(false);
  };

  return (
    <main className="max-w-3xl mx-auto px-6 py-20">
      <h1 className="text-4xl font-bold">TypingEngine</h1>
      <p className="mt-4 text-gray-600 text-lg">
        Upload a dictation file to generate an AI‑powered clinical draft.
      </p>

      {/* DOCTOR PROFILE */}
      <div className="mt-10 p-6 border rounded-xl bg-gray-50">
        <h2 className="text-2xl font-semibold mb-4">Doctor Profile</h2>

        <label className="block text-lg font-medium mb-2">
          Select Doctor (numeric code)
        </label>
        <select
          value={doctorId}
          onChange={(e) => setDoctorId(e.target.value)}
          className="border p-3 rounded-lg w-full bg-white"
        >
          {doctors.map((d) => (
            <option key={d.value} value={d.value}>
              {d.label}
            </option>
          ))}
        </select>

        <p className="mt-3 text-gray-700">
          Samples uploaded: {sampleCount}
          {sampleCount < 5 ? (
            <span className="text-red-600 ml-2">
              (Need at least 5 for style engine)
            </span>
          ) : (
            <span className="text-green-600 ml-2">(Style engine active)</span>
          )}
        </p>

        {/* Admin-only: create doctor code */}
        <div className="mt-6">
          <label className="block text-lg font-medium mb-2">
            Create New Doctor (numeric code)
          </label>
          <div className="flex gap-2">
            <input
              value={newDoctorId}
              onChange={(e) => setNewDoctorId(e.target.value)}
              placeholder="e.g., 2056"
              className="border p-3 rounded-lg flex-1 bg-white"
            />
            <button
              onClick={createDoctorProfile}
              disabled={creatingDoctor || !newDoctorId.trim()}
              className={`px-4 py-3 rounded-lg text-white font-medium ${
                creatingDoctor || !newDoctorId.trim()
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-green-600 hover:bg-green-700"
              }`}
            >
              {creatingDoctor ? "Creating…" : "Create"}
            </button>
          </div>
        </div>
      </div>

      {/* STYLE SAMPLE UPLOAD */}
      <div className="mt-10 p-6 border rounded-xl bg-gray-50">
        <h2 className="text-2xl font-semibold mb-4">Upload Style Samples</h2>

        <label className="block text-lg font-medium mb-2">
          Upload Corrected Reports (.txt or .docx)
        </label>

        <input
          type="file"
          multiple
          accept=".txt,.docx"
          onChange={uploadSamples}
          className="block w-full border p-3 rounded-lg bg-white"
        />

        <p className="mt-3 text-gray-700">
          {sampleUploading ? "Uploading…" : sampleStatus}
        </p>
      </div>

      {/* DICTATION UPLOAD */}
      <div className="mt-10 p-6 border rounded-xl bg-gray-50">
        <label className="block text-lg font-medium mb-3">
          Upload Dictation
        </label>

        <input
          type="file"
          accept="audio/*"
          onChange={handleFileChange}
          className="block w-full border p-3 rounded-lg bg-white"
        />

        {file && (
          <p className="mt-3 text-gray-700">
            Selected file: <span className="font-medium">{file.name}</span>
          </p>
        )}

        {loading && (
          <div className="mt-4 w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        <button
          disabled={!file || loading}
          onClick={generateDraft}
          className={`mt-6 px-6 py-3 rounded-lg text-white text-lg font-medium transition ${
            file && !loading
              ? "bg-blue-600 hover:bg-blue-700"
              : "bg-gray-400 cursor-not-allowed"
          }`}
        >
          {loading ? "Processing…" : "Generate Draft"}
        </button>
      </div>

      {/* OUTPUT */}
      <div className="mt-10 p-6 border rounded-xl bg-gray-50 whitespace-pre-line">
        <h2 className="text-2xl font-semibold">Draft Output</h2>

        {!draft && !loading && (
          <p className="mt-3 text-gray-500">
            The generated draft will appear here…
          </p>
        )}

        {loading && (
          <p className="mt-3 text-blue-600 font-medium">
            Processing dictation…
          </p>
        )}

        {draft && (
          <p className="mt-4 text-gray-800 leading-relaxed">{draft}</p>
        )}
      </div>
    </main>
  );
}