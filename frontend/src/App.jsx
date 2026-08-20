import React, { useState, useEffect } from "react";
import { uploadMeetingAudio, getMeeting, listMeetings } from "./api";
import {
  Upload,
  FileAudio,
  CheckCircle2,
  Clock,
  AlertCircle,
  CheckSquare,
  MessageSquareQuote,
  ListChecks,
  FileText,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function App() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [currentMeetingId, setCurrentMeetingId] = useState(null);
  const [meetingData, setMeetingData] = useState(null);
  const [pastMeetings, setPastMeetings] = useState([]);
  const [selectedQuote, setSelectedQuote] = useState(null);

  // Load meeting history on mount
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const data = await listMeetings();
      setPastMeetings(data);
    } catch (err) {
      console.error("Failed to load past meetings:", err);
    }
  };

  // Polling loop when meeting is actively processing
  useEffect(() => {
    if (!currentMeetingId) return;
    if (
      meetingData &&
      (meetingData.status === "done" || meetingData.status === "failed")
    ) {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const data = await getMeeting(currentMeetingId);
        setMeetingData(data);
        if (data.status === "done" || data.status === "failed") {
          clearInterval(interval);
          fetchHistory();
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [currentMeetingId, meetingData?.status]);
  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    try {
      const res = await uploadMeetingAudio(file);
      setCurrentMeetingId(res.id);
      setMeetingData({ id: res.id, filename: res.filename, status: "pending" });
    } catch (err) {
      alert("Upload failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setUploading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "pending":
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full text-xs font-semibold">
            <Clock className="w-3.5 h-3.5 animate-spin" /> Queued
          </span>
        );
      case "transcribing":
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-full text-xs font-semibold">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Transcribing
            Audio
          </span>
        );
      case "summarizing":
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 bg-purple-500/10 text-purple-400 border border-purple-500/20 rounded-full text-xs font-semibold">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Extracting
            Insights
          </span>
        );
      case "done":
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full text-xs font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" /> Completed
          </span>
        );
      case "failed":
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 bg-red-500/10 text-red-400 border border-red-500/20 rounded-full text-xs font-semibold">
            <AlertCircle className="w-3.5 h-3.5" /> Failed
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur px-8 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-600 rounded-lg text-white font-bold">
            <FileAudio className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-100">
              AI Meeting Intelligence
            </h1>
            <p className="text-xs text-slate-400">
              Grounded Summaries & Verifiable Action Items
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            Pipeline Active
          </span>
        </div>
      </header>

      {/* Main Grid */}
      <div className="flex-1 grid grid-cols-12 gap-6 p-8 max-w-7xl mx-auto w-full">
        {/* Left Column: Upload & History */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          {/* Upload Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
              <Upload className="w-4 h-4 text-indigo-400" /> Upload Meeting
              Audio
            </h2>
            <form onSubmit={handleUpload} className="space-y-4">
              <label className="border-2 border-dashed border-slate-700 hover:border-indigo-500 bg-slate-950/50 hover:bg-slate-950 rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer transition">
                <FileAudio className="w-8 h-8 text-slate-400 mb-2" />
                <span className="text-sm font-medium text-slate-300">
                  {file ? file.name : "Select audio/video (MP3, WAV, MP4, M4A)"}
                </span>
                <span className="text-xs text-slate-500 mt-1">
                  Up to 25MB supported
                </span>
                <input
                  type="file"
                  accept="audio/*,video/mp4,.mp4,.m4a,.wav,.mp3,.ogg,.flac"
                  className="hidden"
                  onChange={(e) => setFile(e.target.files[0])}
                />
              </label>

              <button
                type="submit"
                disabled={!file || uploading}
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 font-medium rounded-lg transition text-sm flex items-center justify-center gap-2 shadow cursor-pointer disabled:cursor-not-allowed">
                {uploading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4" />
                )}
                {uploading ? "Uploading..." : "Process Recording"}
              </button>
            </form>
          </div>

          {/* Previous Meetings List */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-400" /> Recent Meetings
            </h2>
            <div className="space-y-2 max-h-[350px] overflow-y-auto pr-1">
              {pastMeetings.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-4">
                  No meetings processed yet.
                </p>
              ) : (
                pastMeetings.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => {
                      setCurrentMeetingId(m.id);
                      setMeetingData(m);
                    }}
                    className={`w-full text-left p-3 rounded-lg border transition text-xs flex flex-col gap-1 cursor-pointer ${
                      currentMeetingId === m.id
                        ? "bg-indigo-950/40 border-indigo-500/50"
                        : "bg-slate-950/40 border-slate-800 hover:border-slate-700"
                    }`}>
                    <div className="flex items-center justify-between w-full">
                      <span className="font-semibold text-slate-200 truncate">
                        {m.filename}
                      </span>
                      {getStatusBadge(m.status)}
                    </div>
                    <span className="text-[11px] text-slate-500">
                      {new Date(m.created_at).toLocaleString()}
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Dynamic Results View */}
        <div className="col-span-12 lg:col-span-8 space-y-6">
          {!meetingData ? (
            <div className="h-full min-h-[450px] border border-dashed border-slate-800 rounded-xl flex flex-col items-center justify-center p-8 text-center text-slate-500">
              <FileAudio className="w-12 h-12 stroke-1 text-slate-600 mb-3" />
              <h3 className="text-base font-semibold text-slate-400">
                No Meeting Selected
              </h3>
              <p className="text-xs max-w-sm mt-1">
                Upload a recording or choose one from the recent list to view
                transcript and executive intelligence.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Meeting Header Banner */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    {meetingData.filename}
                  </h2>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">
                    ID: {meetingData.id}
                  </p>
                </div>
                <div>{getStatusBadge(meetingData.status)}</div>
              </div>

              {/* In-Progress Notification */}
              {meetingData.status !== "done" &&
                meetingData.status !== "failed" && (
                  <div className="p-6 bg-slate-900 border border-slate-800 rounded-xl text-center">
                    <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto mb-3" />
                    <p className="text-sm font-semibold text-slate-200">
                      Processing Audio Pipeline
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      Whisper is transcribing and verifying grounding against
                      the transcript...
                    </p>
                  </div>
                )}

              {/* Error Banner */}
              {meetingData.status === "failed" && (
                <div className="p-6 bg-red-950/30 border border-red-500/30 rounded-xl">
                  <div className="flex items-center gap-2 text-red-400 font-bold mb-2">
                    <AlertCircle className="w-5 h-5" /> Processing Failed
                  </div>
                  <pre className="text-xs text-red-300 font-mono bg-slate-950 p-3 rounded overflow-x-auto max-h-48 whitespace-pre-wrap">
                    {meetingData.error_message ||
                      "An unknown error occurred during pipeline execution."}
                  </pre>
                </div>
              )}

              {/* Complete Insights View */}
              {meetingData.status === "done" && (
                <div className="space-y-6">
                  {/* Executive Summary */}
                  <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-indigo-400 mb-3 flex items-center gap-2">
                      <FileText className="w-4 h-4" /> Executive Summary
                    </h3>
                    <div className="text-sm text-slate-300 leading-relaxed prose prose-invert max-w-none">
                      <ReactMarkdown>{meetingData.summary}</ReactMarkdown>
                    </div>
                  </div>

                  {/* Decisions */}
                  {meetingData.decisions?.length > 0 && (
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
                      <h3 className="text-sm font-bold uppercase tracking-wider text-emerald-400 mb-3 flex items-center gap-2">
                        <CheckSquare className="w-4 h-4" /> Agreed Decisions
                      </h3>
                      <ul className="space-y-2">
                        {meetingData.decisions.map((dec, i) => (
                          <li
                            key={i}
                            className="flex items-start gap-2.5 text-sm text-slate-300 bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-2"></span>
                            <span>{dec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Grounded Action Items */}
                  {meetingData.action_items?.length > 0 && (
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2">
                          <ListChecks className="w-4 h-4" /> Grounded Action
                          Items
                        </h3>
                        <span className="text-[11px] text-slate-400 flex items-center gap-1">
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />{" "}
                          Fuzzy Grounding Verified
                        </span>
                      </div>
                      <div className="grid gap-3">
                        {meetingData.action_items.map((item, i) => (
                          <div
                            key={i}
                            className="bg-slate-950/60 border border-slate-800 p-4 rounded-lg space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                                {item.owner || "Unassigned"}
                              </span>
                              {item.due_date && (
                                <span className="text-xs text-amber-400 font-medium">
                                  Due: {item.due_date}
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-slate-200 font-medium">
                              {item.task}
                            </p>
                            {item.source_quote && (
                              <button
                                onClick={() =>
                                  setSelectedQuote(item.source_quote)
                                }
                                className="w-full text-left flex items-start gap-2 text-xs text-slate-400 bg-slate-900/90 p-2.5 rounded border border-slate-800/80 hover:border-indigo-500/40 transition cursor-pointer">
                                <MessageSquareQuote className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                                <span>
                                  <strong className="text-slate-300">
                                    Grounding Quote:
                                  </strong>{" "}
                                  "{item.source_quote}"
                                </span>
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Synchronized Diarized Transcript */}
                  <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
                      <FileAudio className="w-4 h-4 text-slate-400" />{" "}
                      Transcript & Diarization
                    </h3>
                    <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                      {meetingData.diarized_segments?.map((seg, i) => {
                        const isHighlighted =
                          selectedQuote &&
                          (seg.text
                            .toLowerCase()
                            .includes(selectedQuote.toLowerCase()) ||
                            selectedQuote
                              .toLowerCase()
                              .includes(seg.text.toLowerCase()));
                        return (
                          <div
                            key={i}
                            className={`p-3 rounded-lg border transition ${
                              isHighlighted
                                ? "bg-amber-500/10 border-amber-500/50"
                                : "bg-slate-950/40 border-slate-800"
                            }`}>
                            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                              <span className="font-semibold text-indigo-400">
                                {seg.speaker}
                              </span>
                              <span className="font-mono text-[11px]">
                                {seg.start}s - {seg.end}s
                              </span>
                            </div>
                            <p className="text-sm text-slate-300">{seg.text}</p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
