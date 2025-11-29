<script setup lang="ts">
import { Textarea } from '~/components/ui/textarea';
import { Button } from '~/components/ui/button';
import { SidebarInset } from '~/components/ui/sidebar';
import MarkdownIt from 'markdown-it';

// Initialize MarkdownIt
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
});

// Types
interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface PrefetchContent {
  [key: string]: any;
}

interface ToolCall {
  id: string;
  name: string;
  arguments: string;
  response: string;
}

// State
const messages = ref<Message[]>([]);
const messageContent = ref('');
const isSending = ref(false);
const error = ref<string | null>(null);
const prefetchContent = ref<PrefetchContent | null>(null);
const toolCalls = ref<ToolCall[]>([]);

// Notebooks state
const availableNotebooks = ref<string[]>([]);
const selectedNotebooks = ref<string[]>([]);
const isLoadingNotebooks = ref(false);

// Sidebar state
const isSidebarOpen = ref(true);

// Load notebooks on mount
onMounted(async () => {
  isLoadingNotebooks.value = true;
  try {
    const notebooks = await $fetch<string[]>('http://localhost:8000/api/notebooks/');
    availableNotebooks.value = notebooks;
  } catch (err) {
    console.error('Failed to load notebooks:', err);
  } finally {
    isLoadingNotebooks.value = false;
  }
});

// Send message
const sendMessage = async () => {
  if (!messageContent.value.trim() || isSending.value) {
    return;
  }

  isSending.value = true;
  const content = messageContent.value.trim();
  messageContent.value = '';
  error.value = null;

  // Add user message to UI immediately
  messages.value.push({ role: 'user', content });

  try {
    // Prepare payload
    const payload = {
      messages: messages.value.map(m => ({ role: m.role, content: m.content })),
      notebooks: selectedNotebooks.value
    };

    // Call API
    const config = useRuntimeConfig();
    const response = await $fetch<{ response: string; prefetch_content: any; tool_calls: any[] }>('http://localhost:8000/api/chat/completion', {
      method: 'POST',
      body: payload,
    });

    // Add assistant message
    messages.value.push({ role: 'assistant', content: response.response });
    
    // Update prefetch content
    if (response.prefetch_content) {
      prefetchContent.value = response.prefetch_content;
    }
    
    // Update tool calls
    if (response.tool_calls) {
      toolCalls.value = response.tool_calls;
    } else {
      toolCalls.value = [];
    }
    
    // Scroll to bottom
    await nextTick();
    scrollToBottom();
  } catch (err: any) {
    error.value = err.message || 'Failed to send message';
    console.error('Error sending message:', err);
    // Optionally remove the user message or show error state
  } finally {
    isSending.value = false;
  }
};

// Scroll to bottom of messages
const scrollToBottom = () => {
  const messagesContainer = document.getElementById('messages-container');
  if (messagesContainer) {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
};

// Handle Enter key (Shift+Enter for new line, Enter to send)
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
};

// Render Markdown
const renderMarkdown = (content: string) => {
  return md.render(content);
};

// Toggle notebook selection
const toggleNotebook = (notebook: string) => {
  if (selectedNotebooks.value.includes(notebook)) {
    selectedNotebooks.value = selectedNotebooks.value.filter(n => n !== notebook);
  } else {
    selectedNotebooks.value.push(notebook);
  }
};

// Helper to parse JSON safely
const parseJson = (str: string) => {
  try {
    return JSON.parse(str);
  } catch (e) {
    return str;
  }
};
</script>

<template>
  <SidebarInset>
    <div class="w-full h-dvh flex flex-col">
      <!-- Header -->
      <div class="border-b p-4 flex items-center justify-between pl-14">
        <h2 class="text-xl font-bold">AI Chat (MVP)</h2>
        
        <div class="flex items-center gap-2">
          <!-- Notebook Selection Dropdown/List -->
          <div class="relative group">
            <Button variant="outline" size="sm" class="flex items-center gap-2">
              <Icon name="material-symbols:library-books-outline" />
              <span>Notebooks ({{ selectedNotebooks.length }})</span>
            </Button>
            
            <div class="absolute right-0 top-full mt-2 w-64 bg-white border rounded-lg shadow-lg p-2 z-50 hidden group-hover:block hover:block">
              <div v-if="isLoadingNotebooks" class="text-center p-2 text-sm text-gray-500">
                Loading notebooks...
              </div>
              <div v-else-if="availableNotebooks.length === 0" class="text-center p-2 text-sm text-gray-500">
                No notebooks available
              </div>
              <div v-else class="max-h-60 overflow-y-auto space-y-1">
                <div 
                  v-for="notebook in availableNotebooks" 
                  :key="notebook"
                  class="flex items-center gap-2 p-2 hover:bg-gray-100 rounded cursor-pointer"
                  @click="toggleNotebook(notebook)"
                >
                  <div class="w-4 h-4 border rounded flex items-center justify-center" :class="selectedNotebooks.includes(notebook) ? 'bg-blue-500 border-blue-500' : 'border-gray-300'">
                    <Icon v-if="selectedNotebooks.includes(notebook)" name="material-symbols:check" class="text-white text-xs" />
                  </div>
                  <span class="text-sm truncate">{{ notebook }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Toggle Sidebar Button -->
          <Button variant="ghost" size="sm" @click="isSidebarOpen = !isSidebarOpen">
            <Icon :name="isSidebarOpen ? 'material-symbols:right-panel-close' : 'material-symbols:right-panel-open'" size="20px" />
          </Button>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="p-4 bg-red-100 text-red-700 border-b">
        {{ error }}
      </div>

      <div class="flex-1 flex overflow-hidden">
        <!-- Messages Container -->
        <div
          id="messages-container"
          class="flex-1 overflow-y-auto p-4 space-y-4 transition-all duration-300"
        >
          <!-- Messages List -->
          <div v-if="messages.length > 0" class="space-y-4">
            <div
              v-for="(message, index) in messages"
              :key="index"
              class="flex"
              :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
            >
              <div
                class="max-w-[80%] rounded-lg p-3"
                :class="
                  message.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-900'
                "
              >
                <!-- Render Markdown for assistant, plain text for user (or markdown too if desired) -->
                <div 
                  v-if="message.role === 'assistant'" 
                  class="prose prose-sm dark:prose-invert max-w-none"
                  v-html="renderMarkdown(message.content)"
                ></div>
                <div v-else class="whitespace-pre-wrap">{{ message.content }}</div>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else class="flex justify-center items-center h-full">
            <div class="text-center">
              <p class="text-2xl font-bold mb-4">Welcome!</p>
              <p class="text-gray-500 mb-4">Start a conversation to see the magic happen.</p>
              <div v-if="availableNotebooks.length > 0" class="text-sm text-gray-400">
                Tip: Select notebooks from the top right menu to add context.
              </div>
            </div>
          </div>
        </div>

        <!-- Context & Tools Sidebar (Right) -->
        <div 
          class="border-l bg-gray-50 overflow-y-auto transition-all duration-300 flex flex-col"
          :class="isSidebarOpen ? 'w-96 p-4' : 'w-0 p-0 overflow-hidden border-none'"
        >
          <div class="space-y-6">
            
            <!-- Prefetch Section -->
            <div v-if="prefetchContent && Object.keys(prefetchContent).length > 0">
              <h3 class="font-bold mb-3 text-sm uppercase text-gray-500 flex items-center gap-2">
                <Icon name="material-symbols:lightbulb-outline" />
                Prefetch Context
              </h3>
              <div class="space-y-3">
                <div v-for="(content, key) in prefetchContent" :key="key" class="bg-white border rounded-lg shadow-sm overflow-hidden">
                  <div class="p-3 bg-gray-50 border-b font-semibold text-xs flex justify-between items-center">
                    <span>{{ key }}</span>
                  </div>
                  <div class="p-3">
                    <details class="text-xs">
                      <summary class="cursor-pointer text-blue-600 hover:text-blue-800 mb-2">View Content</summary>
                      <pre class="whitespace-pre-wrap overflow-x-auto bg-gray-50 p-2 rounded border">{{ JSON.stringify(content, null, 2) }}</pre>
                    </details>
                  </div>
                </div>
              </div>
            </div>

            <!-- Tool Calls Section -->
            <div v-if="toolCalls.length > 0">
              <h3 class="font-bold mb-3 text-sm uppercase text-gray-500 flex items-center gap-2">
                <Icon name="material-symbols:build-outline" />
                Tool Calls
              </h3>
              <div class="space-y-3">
                <div v-for="tool in toolCalls" :key="tool.id" class="bg-white border rounded-lg shadow-sm overflow-hidden">
                  <div class="p-3 bg-gray-50 border-b flex justify-between items-start">
                    <div>
                      <div class="font-semibold text-sm text-gray-800">{{ tool.name }}</div>
                      <div class="text-xs text-gray-500 mt-1 font-mono break-all">
                        {{ tool.arguments }}
                      </div>
                    </div>
                  </div>
                  <div class="p-3">
                    <details class="text-xs">
                      <summary class="cursor-pointer text-blue-600 hover:text-blue-800">View Result</summary>
                      <div class="mt-2 bg-gray-50 p-2 rounded border overflow-x-auto">
                        <pre class="whitespace-pre-wrap">{{ JSON.stringify(parseJson(tool.response), null, 2) }}</pre>
                      </div>
                    </details>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Empty State for Sidebar -->
            <div v-if="(!prefetchContent || Object.keys(prefetchContent).length === 0) && toolCalls.length === 0" class="text-center text-gray-400 text-sm py-10">
              No context or tool usage to display yet.
            </div>

          </div>
        </div>
      </div>

      <!-- Message Input -->
      <div class="border-t p-4">
        <div class="flex items-end gap-2 max-w-4xl mx-auto">
          <Textarea
            v-model="messageContent"
            @keydown="handleKeyDown"
            placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
            class="flex-1 resize-none min-h-[60px] max-h-[200px]"
            :disabled="isSending"
          />
          <Button
            @click="sendMessage"
            :disabled="!messageContent.trim() || isSending"
            class="h-[60px] px-6"
          >
            <span v-if="!isSending">Send</span>
            <span v-else>Sending...</span>
          </Button>
        </div>
      </div>
    </div>
  </SidebarInset>
</template>

<style>
/* Basic prose styling for markdown content if tailwind typography is not fully set up */
.prose p {
  margin-bottom: 0.5em;
}
.prose ul, .prose ol {
  margin-left: 1.5em;
  list-style-type: disc;
}
.prose pre {
  background-color: #f3f4f6;
  padding: 0.5em;
  border-radius: 0.25em;
  overflow-x: auto;
}
.prose code {
  background-color: #f3f4f6;
  padding: 0.1em 0.3em;
  border-radius: 0.25em;
  font-family: monospace;
}
</style>