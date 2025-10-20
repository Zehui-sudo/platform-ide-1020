'use client';

import { useState, useRef, useEffect, useMemo } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Plus, History, Bot, PanelRightClose, ArrowDown } from 'lucide-react';
import { useLearningStore } from '@/store/learningStore';
import type { AIProviderType } from '@/types';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ContextReference } from './ContextReference';
import { ChatMessageRenderer } from './ChatMessageRenderer';
import { ChatHistoryView } from './ChatHistoryView';

type AIChatSidebarProps = {
  toggleSidebar: () => void;
};

export function AIChatSidebar({ toggleSidebar }: AIChatSidebarProps) {
  const {
    chatSessions,
    activeChatSessionId,
    createNewChat,
    switchChat,
    selectedContent,
    setSelectedContent,
    aiProvider,
    setAIProvider,
    sendChatMessage,
    sendingMessage,
  } = useLearningStore();
  
  const [view, setView] = useState<'chat' | 'history'>('chat');
  const activeSession = chatSessions.find(s => s.id === activeChatSessionId);
  const messages = useMemo(() => activeSession?.messages ?? [], [activeSession]);

  const [inputMessage, setInputMessage] = useState('');
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messageContainerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const ignoreScrollEventsRef = useRef(false);
  const autoScrollRef = useRef(true);
  const [scrollBtnFading, setScrollBtnFading] = useState(false);
  const [atBottom, setAtBottom] = useState(true);

  useEffect(() => {
    if (view !== 'chat') return;
    const scrollViewport = scrollAreaRef.current?.querySelector(
      '[data-radix-scroll-area-viewport], [data-slot="scroll-area-viewport"]'
    ) as HTMLDivElement | null;
    if (!messageContainerRef.current || !scrollViewport) return;

    const threshold = 8; // px; how close counts as bottom

    const isAtBottom = () =>
      scrollViewport.scrollHeight - (scrollViewport.scrollTop + scrollViewport.clientHeight) <=
      threshold;

    const scrollToBottom = () => {
      ignoreScrollEventsRef.current = true;
      scrollViewport.scrollTop = scrollViewport.scrollHeight;
      // release the guard on next frame to ignore this programmatic scroll
      requestAnimationFrame(() => {
        ignoreScrollEventsRef.current = false;
      });
    };

    // Initial: reset autoscroll and jump to bottom on session switch
    setAutoScroll(true);
    scrollToBottom();
    setAtBottom(true);

    // Track user scroll to toggle autoScroll
    const onScroll = () => {
      if (ignoreScrollEventsRef.current) return;
      const atBot = isAtBottom();
      setAtBottom(atBot);
      if (!atBot) {
        setAutoScroll(false);
        autoScrollRef.current = false;
      }
    };
    scrollViewport.addEventListener('scroll', onScroll, { passive: true });

    // Observe content changes; only autoscroll when enabled
    const observer = new MutationObserver(() => {
      if (autoScrollRef.current) {
        scrollToBottom();
        setAtBottom(true);
      } else {
        setAtBottom(isAtBottom());
      }
    });
    observer.observe(messageContainerRef.current, {
      childList: true,
      subtree: true,
      characterData: true,
    });

    return () => {
      scrollViewport.removeEventListener('scroll', onScroll as EventListener);
      observer.disconnect();
    };
  }, [activeChatSessionId, view]); // Re-setup when chat session or view changes

  // If messages array length changes (new message appended), autoscroll when enabled
  useEffect(() => {
    if (view !== 'chat') return;
    if (!autoScroll) return;
    const scrollViewport = scrollAreaRef.current?.querySelector(
      '[data-radix-scroll-area-viewport], [data-slot="scroll-area-viewport"]'
    ) as HTMLDivElement | null;
    if (!scrollViewport) return;
    ignoreScrollEventsRef.current = true;
    scrollViewport.scrollTop = scrollViewport.scrollHeight;
    requestAnimationFrame(() => {
      ignoreScrollEventsRef.current = false;
    });
    setAtBottom(true);
  }, [messages.length, view, autoScroll]);

  // keep ref in sync for observer callbacks
  useEffect(() => {
    autoScrollRef.current = autoScroll;
  }, [autoScroll]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !activeChatSessionId || sendingMessage) return;

    const message = inputMessage;
    const context = selectedContent;
    
    setInputMessage('');
    setSelectedContent(null);

    // Call the store's sendChatMessage which handles API call
    await sendChatMessage(message, context, useLearningStore.getState().currentPath?.subject);
  };


  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };


  return (
    <div className="h-full flex flex-col bg-background rounded-lg min-w-0">
      {/* Header */}
      <div className="p-3 border-b flex justify-between items-center min-w-0">
        {/* AI Provider Selector */}
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <Bot className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          <Select value={aiProvider} onValueChange={(value) => setAIProvider(value as AIProviderType)}>
            <SelectTrigger className="h-8 min-w-20 w-full max-w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="openai">OpenAI</SelectItem>
              <SelectItem value="anthropic">Claude</SelectItem>
              <SelectItem value="deepseek">DeepSeek</SelectItem>
              <SelectItem value="doubao">豆包</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <Button size="icon" variant="ghost" onClick={createNewChat} className="h-8 w-8">
            <Plus className="h-4 w-4" />
          </Button>
          <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => setView('history')}>
            <History className="h-4 w-4" />
          </Button>
          <Button size="icon" variant="ghost" className="h-8 w-8" onClick={toggleSidebar}>
            <PanelRightClose className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Messages */}
      {view === 'history' ? (
        <ChatHistoryView
          onBack={() => setView('chat')}
          onSelectChat={(sessionId) => {
            switchChat(sessionId);
            setView('chat');
          }}
        />
      ) : (
        <>
          <div className="flex-1 overflow-hidden relative">
            <ScrollArea className="h-full" ref={scrollAreaRef}>
              <div className="p-3 space-y-3" ref={messageContainerRef}>
                {messages.map((message) => (
                  <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className="w-full max-w-[95%] min-w-0 space-y-1 overflow-hidden">
                      {message.contextReference && message.sender === 'user' && (
                        <div className="mb-2">
                          <ContextReference
                            reference={message.contextReference}
                            onClear={() => {}}
                          />
                        </div>
                      )}
                      <div
                        className={`rounded-lg px-3 py-2 text-sm min-w-0 break-words overflow-hidden ${
                          message.sender === 'user'
                            ? 'bg-primary text-primary-foreground ml-auto'
                            : 'bg-muted'
                        }`}
                      >
                        <ChatMessageRenderer 
                          content={message.content}
                          linkedSections={message.linkedSections}
                        />
                      </div>
                      <div className={`text-xs text-muted-foreground px-1 ${
                        message.sender === 'user' ? 'text-right' : ''
                      }`}>
                        {new Date(message.timestamp).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
            {((!atBottom) || scrollBtnFading) && (
              <div className={`absolute bottom-3 left-1/2 -translate-x-1/2 z-10 transition-opacity transition-transform duration-200 ${scrollBtnFading ? 'opacity-0 translate-y-2' : 'opacity-100 translate-y-0'}`}>
                <Button
                  size="icon"
                  variant="secondary"
                  className="h-10 w-10 rounded-full shadow-lg flex items-center justify-center active:scale-95"
                  onClick={() => {
                    const scrollViewport = scrollAreaRef.current?.querySelector(
                      '[data-radix-scroll-area-viewport], [data-slot="scroll-area-viewport"]'
                    ) as HTMLDivElement | null;
                    if (!scrollViewport) return;
                    setScrollBtnFading(true);
                    autoScrollRef.current = true;
                    setAutoScroll(true);
                    ignoreScrollEventsRef.current = true;
                    scrollViewport.scrollTop = scrollViewport.scrollHeight;
                    requestAnimationFrame(() => {
                      ignoreScrollEventsRef.current = false;
                    });
                    // allow fade-out to complete before unmounting the button
                    setTimeout(() => setScrollBtnFading(false), 200);
                  }}
                  aria-label="回到最新消息"
                  title="回到最新"
                >
                  <ArrowDown className="h-5 w-5 text-primary" strokeWidth={2.75} />
                </Button>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-3 border-t space-y-2 flex-shrink-0">
            {selectedContent && (
              <ContextReference
                reference={selectedContent}
                onClear={() => setSelectedContent(null)}
              />
            )}
            <div className="flex gap-2 min-w-0">
              <Textarea
                data-chat-input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={activeChatSessionId ? "输入你的问题..." : "请先新建或选择一个对话"}
                className="min-h-[36px] max-h-[100px] resize-none text-sm flex-1 min-w-0"
                rows={1}
                disabled={!activeChatSessionId || sendingMessage}
              />
              <Button
                size="sm"
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || sendingMessage || !activeChatSessionId}
                className="self-end h-9 w-9 p-0 flex-shrink-0"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-xs text-muted-foreground hidden sm:block">
              按 Enter 发送，Shift+Enter 换行 | 勾画直接引用选中内容
            </p>
          </div>
        </>
      )}

    </div>
  );
}
