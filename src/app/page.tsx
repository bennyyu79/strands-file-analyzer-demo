"use client";

import {
  useDefaultTool,
  useCoAgent,
  useCopilotReadable,
} from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { useCallback, useEffect, useRef, useState } from "react";

import { FileUpload } from "@/components/file-upload";
import {
  FindingsPanel,
  RedactedPanel,
  TweetsPanel,
  SummaryPanel,
} from "@/components/dashboard-panels";
import { DefaultToolCard } from "@/components/tool-cards";
import {
  FileInvestigatorState,
  INITIAL_STATE,
  UploadedFile,
} from "@/types/investigator";

// 🐛 DEBUG: 全局网络请求拦截器
if (typeof window !== 'undefined') {
  const originalFetch = window.fetch;
  window.fetch = async function(...args) {
    const [url, options] = args;

    // 拦截发送到 CopilotKit 的请求
    if (typeof url === 'string' && url.includes('/api/copilotkit')) {
      const parsedBody = options?.body ? JSON.parse(options.body as string) : null;
      console.log('🌐 [DEBUG] Fetch Request:', {
        url,
        method: options?.method,
        body: parsedBody,
        hasFiles: !!parsedBody?.state?.uploadedFiles?.length > 0,
        uploadedFilesCount: parsedBody?.state?.uploadedFiles?.length || 0,
        stateKeys: parsedBody?.state ? Object.keys(parsedBody.state) : [],
        uploadedFilesPreview: parsedBody?.state?.uploadedFiles?.map((f: any) => ({
          name: f.name,
          size: f.sizeBytes,
          base64Length: f.base64?.length || 0
        })) || []
      });

      // 🐛 DEBUG: 打印完整的请求体以供分析
      console.log('📄 [DEBUG] Full Request Body:', JSON.stringify(parsedBody, null, 2));
    }

    try {
      const response = await originalFetch(...args);

      // 拦截响应
      if (typeof url === 'string' && url.includes('/api/copilotkit')) {
        // 使用 async/await 而不是 .then()
        const clonedResponse = response.clone();
        try {
          const responseData = await clonedResponse.text();
          console.log('📥 [DEBUG] Fetch Response:', {
            url,
            status: response.status,
            statusText: response.statusText,
            dataLength: responseData.length,
            dataType: clonedResponse.headers.get('content-type'),
            preview: responseData.substring(0, 200)
          });
        } catch (e) {
          console.log('📥 [DEBUG] Fetch Response (parse error):', {
            url,
            status: response.status,
            error: e
          });
        }
      }

      return response;
    } catch (error) {
      // 捕获网络错误
      if (typeof url === 'string' && url.includes('/api/copilotkit')) {
        console.error('❌ [DEBUG] Fetch Error:', {
          url,
          errorString: String(error),
          errorKeys: Object.keys(error as object),
          errorMessage: error instanceof Error ? error.message : 'Not an Error',
          errorStack: error instanceof Error ? error.stack : 'No stack',
          errorName: error instanceof Error ? error.name : 'Unknown',
          fullError: JSON.stringify(error, Object.getOwnPropertyNames(error), 2)
        });
      }
      throw error;
    }
  };

  console.log('✅ [DEBUG] Network interceptor installed');
}

export default function FileInvestigatorPage() {
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Shared state with agent
  const { state, setState } = useCoAgent<FileInvestigatorState>({
    name: "file_investigator",
    initialState: INITIAL_STATE,
    // 禁用自动加载状态，避免初始化时的空请求导致 400 错误
    config: {
      autoLoad: false,
    },
  });

  // 🔥 FIX: 使用 useCopilotReadable 将状态暴露给 CopilotKit
  // 这样状态会被包含在发送到后端的 GraphQL 请求中
  useCopilotReadable({
    description: "Uploaded PDF files for analysis",
    value: state.uploadedFiles,
  });

  // 🐛 DEBUG: 监控 useCopilotReadable 的值变化
  useEffect(() => {
    console.log('📝 [DEBUG] useCopilotReadable value updated:', {
      count: state.uploadedFiles?.length || 0,
      files: state.uploadedFiles?.map(f => f.name) || [],
    });
  }, [state.uploadedFiles]);

  // Ref to track current state for use in tool handlers (avoids stale closure)
  const stateRef = useRef(state);
  useEffect(() => {
    stateRef.current = state;

    // 🐛 DEBUG: Log state changes
    console.log('🔄 [DEBUG] State changed:', {
      uploadedFiles: state.uploadedFiles?.length || 0,
      fileNames: state.uploadedFiles?.map(f => ({
        name: f.name,
        size: f.sizeBytes,
        base64Length: f.base64?.length || 0
      })) || [],
      analysisStatus: state.analysisStatus,
      findings: state.findings?.length || 0,
      redacted: state.redacted?.length || 0,
      tweets: state.tweets?.length || 0,
      hasSummary: !!state.summary
    });
  }, [state]);

  // Handle files change
  const handleFilesChange = useCallback(
    (files: UploadedFile[]) => {
      // 🐛 DEBUG: Log file upload
      console.log('📤 [DEBUG] Files uploaded:', {
        count: files.length,
        files: files.map(f => ({
          name: f.name,
          size: f.sizeBytes,
          base64Length: f.base64?.length || 0,
          mimeType: f.mimeType
        }))
      });

      const newState = {
        ...state,
        uploadedFiles: files,
        analysisStatus: "idle",
        // Reset results when files change
        findings: [],
        redacted: [],
        tweets: [],
        summary: null,
      };

      console.log('📤 [DEBUG] Calling setState with new state');
      setState(newState);
    },
    [state, setState]
  );

  // Handle tweet copy
  const handleCopyTweet = useCallback((content: string) => {
    navigator.clipboard.writeText(content);
    setToastMessage("Tweet copied! Handle with care...");
    setTimeout(() => setToastMessage(null), 2000);
  }, []);

  // Handle mock tweet post
  const handlePostTweet = useCallback(
    (id: string) => {
      setState({
        ...stateRef.current,
        tweets: stateRef.current.tweets.map((t) =>
          t.id === id ? { ...t, posted: true } : t
        ),
      });
      setToastMessage("Tweet posted! The truth is out there.");
      setTimeout(() => setToastMessage(null), 2000);
    },
    [setState]
  );

  // Handle tweet edit
  const handleEditTweet = useCallback(
    (id: string, newContent: string) => {
      setState({
        ...stateRef.current,
        tweets: stateRef.current.tweets.map((t) =>
          t.id === id ? { ...t, content: newContent } : t
        ),
      });
    },
    [setState]
  );

  // Tools update state directly, dashboard panels render from state

  // === Default Tool Renderer ===
  useDefaultTool({
    render: (props) => (
      <DefaultToolCard
        name={props.name}
        status={props.status}
        args={props.args}
        result={props.result}
      />
    ),
  });

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Toast */}
      {toastMessage && (
        <div className="fixed top-4 right-4 bg-slate-900 text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-fade-in">
          {toastMessage}
        </div>
      )}

      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">File Investigator</h1>
              <p className="text-sm text-slate-500">AI-powered document analysis</p>
            </div>
          </div>
          <div className="text-xs text-slate-400">
            Powered by things that didn&apos;t happen
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Upload + Panels */}
          <div className="lg:col-span-2 flex flex-col h-[calc(100vh-120px)]">
            {/* File Upload */}
            <div className="flex-shrink-0 mb-6">
              <FileUpload
                onFilesChange={handleFilesChange}
                currentFiles={state.uploadedFiles}
              />
            </div>

            {/* Results Grid - fills remaining space, 2 rows split evenly */}
            <div className="grid grid-cols-1 md:grid-cols-2 grid-rows-2 gap-6 flex-1 min-h-0">
              <FindingsPanel findings={state.findings} />
              <RedactedPanel redactedItems={state.redacted} />
              <TweetsPanel
                tweets={state.tweets}
                onCopy={handleCopyTweet}
                onPost={handlePostTweet}
                onEdit={handleEditTweet}
              />
              <SummaryPanel summary={state.summary} />
            </div>
          </div>

          {/* Right Column: Chat */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 h-[calc(100vh-180px)] overflow-hidden">
              <CopilotChat
                labels={{
                  title: "Investigation Assistant",
                  initial: "Upload a PDF and I'll help you investigate it. Some documents have more... interesting... contents than others.",
                  placeholder: "Ask me to analyze the document...",
                }}
                className="h-full"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
